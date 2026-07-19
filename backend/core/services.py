from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    Basket,
    BasketItem,
    GoodsReceipt,
    Promotion,
    Sale,
    StockBalance,
    StockIssue,
    StockTransaction,
)

MONEY = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def apply_best_promotion(product, package_quantity: Decimal, gross: Decimal):
    now = timezone.now()
    promotions = (
        Promotion.objects.filter(
            is_active=True,
            start_at__lte=now,
            end_at__gte=now,
            products=product,
            minimum_quantity__lte=package_quantity,
        )
        .order_by("id")
        .distinct()
    )
    best_promotion = None
    best_discount = Decimal("0")

    for promotion in promotions:
        discount = Decimal("0")
        if promotion.promotion_type == Promotion.PromotionType.PERCENT:
            discount = gross * promotion.value / Decimal("100")
        elif promotion.promotion_type == Promotion.PromotionType.FIXED:
            discount = promotion.value
        elif (
            promotion.promotion_type == Promotion.PromotionType.BUY_X_GET_Y
            and promotion.buy_quantity > 0
            and promotion.get_quantity > 0
        ):
            group_size = promotion.buy_quantity + promotion.get_quantity
            free_packages = int(package_quantity // group_size) * promotion.get_quantity
            per_package_price = gross / package_quantity if package_quantity else Decimal("0")
            discount = per_package_price * free_packages

        discount = min(money(discount), money(gross))
        if discount > best_discount:
            best_discount = discount
            best_promotion = promotion

    return best_promotion, best_discount


@transaction.atomic
def change_stock(*, product, warehouse, delta_base, transaction_type, reference_no, product_package,
                 package_quantity, user, unit_cost=Decimal("0"), unit_price=Decimal("0"), notes=""):
    delta_base = Decimal(delta_base)
    balance, _ = StockBalance.objects.select_for_update().get_or_create(
        product=product,
        warehouse=warehouse,
        defaults={"quantity_base": Decimal("0")},
    )
    new_quantity = balance.quantity_base + delta_base
    if new_quantity < 0:
        raise ValidationError(
            f"Insufficient stock for {product.sku} in {warehouse.code}. "
            f"Available {balance.quantity_base}, requested {abs(delta_base)} base units."
        )
    balance.quantity_base = new_quantity
    balance.save(update_fields=["quantity_base", "updated_at"])

    return StockTransaction.objects.create(
        transaction_type=transaction_type,
        reference_no=reference_no,
        product=product,
        warehouse=warehouse,
        package_type=product_package.package_type,
        package_quantity=package_quantity,
        quantity_base=delta_base,
        unit_cost=unit_cost,
        unit_price=unit_price,
        performed_by=user,
        notes=notes,
    )


@transaction.atomic
def post_goods_receipt(receipt: GoodsReceipt, user):
    receipt = GoodsReceipt.objects.select_for_update().prefetch_related("lines__product_package__product").get(pk=receipt.pk)
    if receipt.status != GoodsReceipt.Status.DRAFT:
        raise ValidationError("Only a draft goods receipt can be posted.")
    if not receipt.lines.exists():
        raise ValidationError("Add at least one receipt line before posting.")

    total = Decimal("0")
    for line in receipt.lines.all():
        package = line.product_package
        change_stock(
            product=package.product,
            warehouse=receipt.warehouse,
            delta_base=line.base_quantity,
            transaction_type=StockTransaction.TransactionType.RECEIPT,
            reference_no=receipt.receipt_no,
            product_package=package,
            package_quantity=line.package_quantity,
            user=user,
            unit_cost=line.unit_cost,
            notes=receipt.notes,
        )
        total += line.line_total

    receipt.total_cost = money(total)
    receipt.status = GoodsReceipt.Status.POSTED
    receipt.save(update_fields=["total_cost", "status", "updated_at"])
    return receipt


@transaction.atomic
def post_stock_issue(issue: StockIssue, user):
    issue = StockIssue.objects.select_for_update().prefetch_related("lines__product_package__product").get(pk=issue.pk)
    if issue.status != StockIssue.Status.DRAFT:
        raise ValidationError("Only a draft stock issue can be posted.")
    if not issue.lines.exists():
        raise ValidationError("Add at least one issue line before posting.")
    if issue.issue_type == StockIssue.IssueType.TRANSFER and not issue.target_warehouse:
        raise ValidationError("A transfer requires a target warehouse.")
    if issue.target_warehouse_id == issue.source_warehouse_id and issue.issue_type == StockIssue.IssueType.TRANSFER:
        raise ValidationError("Source and target warehouse must be different.")

    total = Decimal("0")
    for line in issue.lines.all():
        package = line.product_package
        outbound_type = {
            StockIssue.IssueType.SALE: StockTransaction.TransactionType.SALE,
            StockIssue.IssueType.SCRAP: StockTransaction.TransactionType.SCRAP,
            StockIssue.IssueType.TRANSFER: StockTransaction.TransactionType.TRANSFER_OUT,
        }[issue.issue_type]
        change_stock(
            product=package.product,
            warehouse=issue.source_warehouse,
            delta_base=-line.base_quantity,
            transaction_type=outbound_type,
            reference_no=issue.issue_no,
            product_package=package,
            package_quantity=line.package_quantity,
            user=user,
            unit_price=line.unit_price,
            notes=issue.reason,
        )
        if issue.issue_type == StockIssue.IssueType.TRANSFER:
            change_stock(
                product=package.product,
                warehouse=issue.target_warehouse,
                delta_base=line.base_quantity,
                transaction_type=StockTransaction.TransactionType.TRANSFER_IN,
                reference_no=issue.issue_no,
                product_package=package,
                package_quantity=line.package_quantity,
                user=user,
                unit_price=line.unit_price,
                notes=f"Transfer from {issue.source_warehouse.code}. {issue.reason}",
            )
        total += line.line_total

    issue.total_amount = money(total)
    issue.status = StockIssue.Status.POSTED
    issue.save(update_fields=["total_amount", "status", "updated_at"])
    return issue


def recalculate_basket(basket: Basket):
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    for item in basket.items.select_related("product_package__product"):
        gross = money(item.package_quantity * item.unit_price)
        promotion, discount = apply_best_promotion(
            item.product_package.product,
            item.package_quantity,
            gross,
        )
        item.promotion = promotion
        item.discount_amount = discount
        item.line_total = money(gross - discount)
        item.save(update_fields=["promotion", "discount_amount", "line_total", "updated_at"])
        subtotal += gross
        discount_total += discount

    basket.subtotal = money(subtotal)
    basket.discount_total = money(discount_total)
    basket.grand_total = money(subtotal - discount_total)
    basket.save(update_fields=["subtotal", "discount_total", "grand_total", "updated_at"])
    return basket


@transaction.atomic
def add_basket_item(*, basket: Basket, product_package, package_quantity, unit_price=None):
    basket = Basket.objects.select_for_update().get(pk=basket.pk)
    if basket.status != Basket.Status.OPEN:
        raise ValidationError("Only an open basket can be changed.")
    package_quantity = Decimal(str(package_quantity))
    if package_quantity <= 0:
        raise ValidationError("Quantity must be greater than zero.")
    unit_price = Decimal(str(unit_price if unit_price is not None else product_package.default_selling_price))

    item, created = BasketItem.objects.get_or_create(
        basket=basket,
        product_package=product_package,
        defaults={"package_quantity": package_quantity, "unit_price": unit_price},
    )
    if not created:
        item.package_quantity += package_quantity
        item.unit_price = unit_price
        item.save(update_fields=["package_quantity", "unit_price", "updated_at"])
    recalculate_basket(basket)
    return item


@transaction.atomic
def checkout_basket(basket: Basket, user):
    basket = (
        Basket.objects.select_for_update()
        .select_related("warehouse", "customer")
        .prefetch_related("items__product_package__product")
        .get(pk=basket.pk)
    )
    if basket.status != Basket.Status.OPEN:
        raise ValidationError("Only an open basket can be checked out.")
    if not basket.items.exists():
        raise ValidationError("The basket is empty.")

    recalculate_basket(basket)
    sale = Sale.objects.create(
        basket=basket,
        customer=basket.customer,
        warehouse=basket.warehouse,
        subtotal=basket.subtotal,
        discount_total=basket.discount_total,
        grand_total=basket.grand_total,
        cashier=user,
    )
    for item in basket.items.all():
        package = item.product_package
        base_quantity = item.package_quantity * package.units_per_package
        change_stock(
            product=package.product,
            warehouse=basket.warehouse,
            delta_base=-base_quantity,
            transaction_type=StockTransaction.TransactionType.SALE,
            reference_no=sale.sale_no,
            product_package=package,
            package_quantity=item.package_quantity,
            user=user,
            unit_price=item.unit_price,
            notes=f"Checkout from {basket.basket_no}",
        )

    basket.status = Basket.Status.CONFIRMED
    basket.save(update_fields=["status", "updated_at"])
    return sale


def total_stock_for_product(product):
    return product.stock_balances.aggregate(total=Sum("quantity_base"))["total"] or Decimal("0")
