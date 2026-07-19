from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


def document_number(prefix: str) -> str:
    return f"{prefix}-{timezone.localdate():%Y%m%d}-{uuid4().hex[:6].upper()}"


def grn_number() -> str:
    return document_number("GRN")


def issue_number() -> str:
    return document_number("ISS")


def basket_number() -> str:
    return document_number("BSK")


def sale_number() -> str:
    return document_number("SAL")


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Vendor(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=180)
    tax_id = models.CharField(max_length=30, blank=True)
    contact_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    payment_terms_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Customer(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=180)
    member_no = models.CharField(max_length=40, blank=True, unique=True, null=True)
    tax_id = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    loyalty_points = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Warehouse(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Product(TimeStampedModel):
    sku = models.CharField(max_length=60, unique=True)
    barcode = models.CharField(max_length=80, blank=True, unique=True, null=True)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    base_unit_name = models.CharField(max_length=30, default="unit")
    safety_stock = models.DecimalField(
        max_digits=16,
        decimal_places=3,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Safety quantity stored in base units.",
    )
    track_expiry = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sku"]
        indexes = [models.Index(fields=["sku"]), models.Index(fields=["name"])]

    def __str__(self):
        return f"{self.sku} - {self.name}"


class ProductPackage(TimeStampedModel):
    class PackageType(models.TextChoices):
        UNIT = "UNIT", "Unit"
        PACK = "PACK", "Pack"
        PALLET = "PALLET", "Pallet"
        CONTAINER = "CONTAINER", "Container"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="packages")
    package_type = models.CharField(max_length=20, choices=PackageType.choices)
    label = models.CharField(max_length=60, blank=True)
    barcode = models.CharField(max_length=80, blank=True, unique=True, null=True)
    units_per_package = models.DecimalField(
        max_digits=16,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    default_purchase_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    default_selling_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["product__sku", "units_per_package"]
        constraints = [
            models.UniqueConstraint(fields=["product", "package_type"], name="uq_product_package_type")
        ]

    def __str__(self):
        return f"{self.product.sku} / {self.get_package_type_display()}"


class Promotion(TimeStampedModel):
    class PromotionType(models.TextChoices):
        PERCENT = "PERCENT", "Percentage discount"
        FIXED = "FIXED", "Fixed amount discount"
        BUY_X_GET_Y = "BUY_X_GET_Y", "Buy X get Y"

    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=160)
    promotion_type = models.CharField(max_length=20, choices=PromotionType.choices)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    minimum_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("1"))
    buy_quantity = models.PositiveIntegerField(default=0)
    get_quantity = models.PositiveIntegerField(default=0)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    products = models.ManyToManyField(Product, related_name="promotions", blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_at"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def is_current(self):
        now = timezone.now()
        return self.is_active and self.start_at <= now <= self.end_at


class StockBalance(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_balances")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stock_balances")
    quantity_base = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0"))

    class Meta:
        ordering = ["product__sku", "warehouse__code"]
        constraints = [
            models.UniqueConstraint(fields=["product", "warehouse"], name="uq_product_warehouse_balance")
        ]

    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.code}: {self.quantity_base}"


class StockTransaction(TimeStampedModel):
    class TransactionType(models.TextChoices):
        RECEIPT = "RECEIPT", "Stock receipt"
        SALE = "SALE", "Sale"
        SCRAP = "SCRAP", "Scrap"
        TRANSFER_OUT = "TRANSFER_OUT", "Transfer out"
        TRANSFER_IN = "TRANSFER_IN", "Transfer in"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"

    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    reference_no = models.CharField(max_length=60, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_transactions")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="stock_transactions")
    package_type = models.CharField(max_length=20, choices=ProductPackage.PackageType.choices)
    package_quantity = models.DecimalField(max_digits=16, decimal_places=3)
    quantity_base = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        help_text="Signed base-unit quantity. Receipts are positive; sales/scrap/out are negative.",
    )
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    occurred_at = models.DateTimeField(default=timezone.now)
    performed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="stock_transactions")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        indexes = [models.Index(fields=["reference_no"]), models.Index(fields=["occurred_at"])]


class GoodsReceipt(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        POSTED = "POSTED", "Posted"
        CANCELLED = "CANCELLED", "Cancelled"

    receipt_no = models.CharField(max_length=60, unique=True, default=grn_number)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="goods_receipts")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="goods_receipts")
    supplier_invoice_no = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    received_at = models.DateTimeField(default=timezone.now)
    total_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0"))
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="goods_receipts")

    class Meta:
        ordering = ["-received_at", "-id"]

    def __str__(self):
        return self.receipt_no


class GoodsReceiptLine(TimeStampedModel):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name="lines")
    product_package = models.ForeignKey(ProductPackage, on_delete=models.PROTECT)
    package_quantity = models.DecimalField(max_digits=16, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))])
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    base_quantity = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.base_quantity = self.package_quantity * self.product_package.units_per_package
        self.line_total = self.package_quantity * self.unit_cost
        super().save(*args, **kwargs)


class StockIssue(TimeStampedModel):
    class IssueType(models.TextChoices):
        SALE = "SALE", "Sale"
        SCRAP = "SCRAP", "Scrap"
        TRANSFER = "TRANSFER", "Transfer"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        POSTED = "POSTED", "Posted"
        CANCELLED = "CANCELLED", "Cancelled"

    issue_no = models.CharField(max_length=60, unique=True, default=issue_number)
    issue_type = models.CharField(max_length=20, choices=IssueType.choices)
    source_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="stock_issues_out")
    target_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stock_issues_in",
        blank=True,
        null=True,
    )
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="stock_issues", blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    issued_at = models.DateTimeField(default=timezone.now)
    reason = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0"))
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="stock_issues")

    class Meta:
        ordering = ["-issued_at", "-id"]

    def __str__(self):
        return self.issue_no


class StockIssueLine(TimeStampedModel):
    issue = models.ForeignKey(StockIssue, on_delete=models.CASCADE, related_name="lines")
    product_package = models.ForeignKey(ProductPackage, on_delete=models.PROTECT)
    package_quantity = models.DecimalField(max_digits=16, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))])
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    base_quantity = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0"))

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.base_quantity = self.package_quantity * self.product_package.units_per_package
        self.line_total = self.package_quantity * self.unit_price
        super().save(*args, **kwargs)


class Basket(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    basket_no = models.CharField(max_length=60, unique=True, default=basket_number)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="baskets", blank=True, null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="baskets")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0"))
    discount_total = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0"))
    grand_total = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0"))
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="baskets")

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.basket_no


class BasketItem(TimeStampedModel):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name="items")
    product_package = models.ForeignKey(ProductPackage, on_delete=models.PROTECT)
    package_quantity = models.DecimalField(max_digits=16, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))])
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0"))

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["basket", "product_package"], name="uq_basket_package")
        ]


class Sale(TimeStampedModel):
    sale_no = models.CharField(max_length=60, unique=True, default=sale_number)
    basket = models.OneToOneField(Basket, on_delete=models.PROTECT, related_name="sale")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="sales", blank=True, null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="sales")
    subtotal = models.DecimalField(max_digits=16, decimal_places=2)
    discount_total = models.DecimalField(max_digits=16, decimal_places=2)
    grand_total = models.DecimalField(max_digits=16, decimal_places=2)
    sold_at = models.DateTimeField(default=timezone.now)
    cashier = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sales")

    class Meta:
        ordering = ["-sold_at", "-id"]

    def __str__(self):
        return self.sale_no
