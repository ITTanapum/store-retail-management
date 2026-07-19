from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Basket,
    BasketItem,
    Category,
    Customer,
    GoodsReceipt,
    Product,
    ProductPackage,
    Promotion,
    Sale,
    StockBalance,
    StockIssue,
    StockTransaction,
    Vendor,
    Warehouse,
)
from .permissions import (
    AdminOnlyPermission,
    InventoryPermission,
    MasterDataPermission,
    PosPermission,
    PromotionPermission,
)
from .serializers import (
    BasketSerializer,
    CategorySerializer,
    CustomerSerializer,
    GoodsReceiptSerializer,
    GroupSerializer,
    ProductPackageSerializer,
    ProductSerializer,
    PromotionSerializer,
    SaleSerializer,
    StockBalanceSerializer,
    StockIssueSerializer,
    StockTransactionSerializer,
    UserSerializer,
    VendorSerializer,
    WarehouseSerializer,
)
from .services import add_basket_item, checkout_basket, post_goods_receipt, post_stock_issue, recalculate_basket


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(
        {
            "id": request.user.id,
            "username": request.user.username,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
            "is_superuser": request.user.is_superuser,
            "roles": list(request.user.groups.values_list("name", flat=True)),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    today = timezone.localdate()
    product_count = Product.objects.filter(is_active=True).count()
    low_stock_qs = StockBalance.objects.select_related("product", "warehouse").filter(
        quantity_base__lte=F("product__safety_stock")
    )
    # Products without a balance are also low when safety stock is above zero.
    products_without_balance = Product.objects.filter(is_active=True, safety_stock__gt=0, stock_balances__isnull=True).count()
    sales_today = Sale.objects.filter(sold_at__date=today).aggregate(total=Coalesce(Sum("grand_total"), Value(Decimal("0"))))["total"]
    open_baskets = Basket.objects.filter(status=Basket.Status.OPEN).count()
    stock_quantity = StockBalance.objects.aggregate(total=Coalesce(Sum("quantity_base"), Value(Decimal("0"))))["total"]
    recent_transactions = StockTransaction.objects.select_related("product", "warehouse", "performed_by")[:10]

    return Response(
        {
            "product_count": product_count,
            "low_stock_count": low_stock_qs.count() + products_without_balance,
            "sales_today": sales_today,
            "open_baskets": open_baskets,
            "stock_quantity_base": stock_quantity,
            "low_stock_items": StockBalanceSerializer(low_stock_qs[:12], many=True).data,
            "recent_transactions": StockTransactionSerializer(recent_transactions, many=True).data,
        }
    )


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [MasterDataPermission]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [MasterDataPermission]
    search_fields = ["code", "name", "phone", "email", "tax_id"]
    ordering_fields = ["code", "name", "created_at"]


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [MasterDataPermission]
    search_fields = ["code", "name", "member_no", "phone", "email"]
    ordering_fields = ["code", "name", "created_at"]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [MasterDataPermission]
    search_fields = ["code", "name"]
    ordering_fields = ["code", "name"]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [MasterDataPermission]
    search_fields = ["sku", "barcode", "name", "description", "category__name"]
    ordering_fields = ["sku", "name", "safety_stock", "created_at"]

    def get_queryset(self):
        return Product.objects.select_related("category").prefetch_related("packages").annotate(
            current_stock_value=Coalesce(
                Sum("stock_balances__quantity_base"),
                Value(Decimal("0")),
                output_field=DecimalField(max_digits=18, decimal_places=3),
            )
        ).order_by("sku")


class ProductPackageViewSet(viewsets.ModelViewSet):
    queryset = ProductPackage.objects.select_related("product")
    serializer_class = ProductPackageSerializer
    permission_classes = [MasterDataPermission]
    search_fields = ["product__sku", "product__name", "barcode", "label", "package_type"]
    ordering_fields = ["product__sku", "units_per_package", "default_selling_price"]


class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.prefetch_related("products")
    serializer_class = PromotionSerializer
    permission_classes = [PromotionPermission]
    search_fields = ["code", "name", "promotion_type"]
    ordering_fields = ["start_at", "end_at", "name"]


class StockBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockBalance.objects.select_related("product", "warehouse")
    serializer_class = StockBalanceSerializer
    search_fields = ["product__sku", "product__name", "warehouse__code", "warehouse__name"]
    ordering_fields = ["quantity_base", "product__sku", "warehouse__code"]

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        queryset = self.filter_queryset(self.get_queryset().filter(quantity_base__lte=F("product__safety_stock")))
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(queryset, many=True).data)


class StockTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockTransaction.objects.select_related("product", "warehouse", "performed_by")
    serializer_class = StockTransactionSerializer
    search_fields = ["reference_no", "product__sku", "product__name", "warehouse__code", "transaction_type"]
    ordering_fields = ["occurred_at", "quantity_base", "reference_no"]


class GoodsReceiptViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceipt.objects.select_related("vendor", "warehouse", "created_by").prefetch_related("lines__product_package__product")
    serializer_class = GoodsReceiptSerializer
    permission_classes = [InventoryPermission]
    search_fields = ["receipt_no", "supplier_invoice_no", "vendor__name", "warehouse__name", "status"]
    ordering_fields = ["received_at", "receipt_no", "total_cost"]

    @action(detail=True, methods=["post"])
    def post_receipt(self, request, pk=None):
        receipt = post_goods_receipt(self.get_object(), request.user)
        return Response(self.get_serializer(receipt).data)


class StockIssueViewSet(viewsets.ModelViewSet):
    queryset = StockIssue.objects.select_related(
        "source_warehouse", "target_warehouse", "customer", "created_by"
    ).prefetch_related("lines__product_package__product")
    serializer_class = StockIssueSerializer
    permission_classes = [InventoryPermission]
    search_fields = ["issue_no", "issue_type", "status", "customer__name", "source_warehouse__name"]
    ordering_fields = ["issued_at", "issue_no", "total_amount"]

    @action(detail=True, methods=["post"])
    def post_issue(self, request, pk=None):
        issue = post_stock_issue(self.get_object(), request.user)
        return Response(self.get_serializer(issue).data)


class BasketViewSet(viewsets.ModelViewSet):
    queryset = Basket.objects.select_related("customer", "warehouse", "created_by").prefetch_related(
        "items__product_package__product", "items__promotion"
    )
    serializer_class = BasketSerializer
    permission_classes = [PosPermission]
    search_fields = ["basket_no", "customer__name", "warehouse__name", "status"]
    ordering_fields = ["created_at", "basket_no", "grand_total"]

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        basket = self.get_object()
        package_id = request.data.get("product_package_id")
        quantity = request.data.get("package_quantity")
        if not package_id or quantity in (None, ""):
            return Response({"detail": "product_package_id and package_quantity are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            package = ProductPackage.objects.get(pk=package_id, is_active=True)
        except ProductPackage.DoesNotExist:
            return Response({"detail": "Product package not found."}, status=status.HTTP_404_NOT_FOUND)
        add_basket_item(
            basket=basket,
            product_package=package,
            package_quantity=quantity,
            unit_price=request.data.get("unit_price"),
        )
        basket.refresh_from_db()
        return Response(self.get_serializer(basket).data)

    @action(detail=True, methods=["post"])
    def remove_item(self, request, pk=None):
        basket = self.get_object()
        item_id = request.data.get("item_id")
        try:
            item = BasketItem.objects.get(pk=item_id, basket=basket)
        except BasketItem.DoesNotExist:
            return Response({"detail": "Basket item not found."}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        recalculate_basket(basket)
        basket.refresh_from_db()
        return Response(self.get_serializer(basket).data)

    @action(detail=True, methods=["post"])
    def checkout(self, request, pk=None):
        sale = checkout_basket(self.get_object(), request.user)
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)


class SaleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sale.objects.select_related("basket", "customer", "warehouse", "cashier")
    serializer_class = SaleSerializer
    search_fields = ["sale_no", "basket__basket_no", "customer__name", "cashier__username"]
    ordering_fields = ["sold_at", "grand_total", "sale_no"]


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all().order_by("name")
    serializer_class = GroupSerializer
    permission_classes = [AdminOnlyPermission]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related("groups").all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [AdminOnlyPermission]
    search_fields = ["username", "first_name", "last_name", "email", "groups__name"]
    ordering_fields = ["username", "is_active", "date_joined"]
