from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from .models import (
    Basket,
    BasketItem,
    Category,
    Customer,
    GoodsReceipt,
    GoodsReceiptLine,
    Product,
    ProductPackage,
    Promotion,
    Sale,
    StockBalance,
    StockIssue,
    StockIssueLine,
    StockTransaction,
    Vendor,
    Warehouse,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"


class ProductPackageSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    package_type_display = serializers.CharField(source="get_package_type_display", read_only=True)

    class Meta:
        model = ProductPackage
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    packages = ProductPackageSerializer(many=True, read_only=True)
    current_stock = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_current_stock(self, obj):
        annotated = getattr(obj, "current_stock_value", None)
        if annotated is not None:
            return annotated
        return obj.stock_balances.aggregate(total=Sum("quantity_base"))["total"] or Decimal("0")

    def get_is_low_stock(self, obj):
        return Decimal(str(self.get_current_stock(obj))) <= obj.safety_stock


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = "__all__"

    def validate(self, attrs):
        start_at = attrs.get("start_at", getattr(self.instance, "start_at", None))
        end_at = attrs.get("end_at", getattr(self.instance, "end_at", None))
        if start_at and end_at and end_at <= start_at:
            raise serializers.ValidationError("Promotion end time must be after the start time.")
        return attrs


class StockBalanceSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)
    safety_stock = serializers.DecimalField(source="product.safety_stock", max_digits=16, decimal_places=3, read_only=True)
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = StockBalance
        fields = "__all__"

    def get_is_low_stock(self, obj):
        return obj.quantity_base <= obj.product.safety_stock


class StockTransactionSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)
    performed_by_name = serializers.CharField(source="performed_by.username", read_only=True)

    class Meta:
        model = StockTransaction
        fields = "__all__"


class GoodsReceiptLineSerializer(serializers.ModelSerializer):
    product_package_id = serializers.PrimaryKeyRelatedField(
        source="product_package", queryset=ProductPackage.objects.filter(is_active=True)
    )
    sku = serializers.CharField(source="product_package.product.sku", read_only=True)
    product_name = serializers.CharField(source="product_package.product.name", read_only=True)
    package_type = serializers.CharField(source="product_package.package_type", read_only=True)

    class Meta:
        model = GoodsReceiptLine
        fields = [
            "id",
            "product_package_id",
            "sku",
            "product_name",
            "package_type",
            "package_quantity",
            "unit_cost",
            "base_quantity",
            "line_total",
        ]
        read_only_fields = ["base_quantity", "line_total"]


class GoodsReceiptSerializer(serializers.ModelSerializer):
    lines = GoodsReceiptLineSerializer(many=True)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = GoodsReceipt
        fields = "__all__"
        read_only_fields = ["receipt_no", "status", "total_cost", "created_by"]

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop("lines", [])
        receipt = GoodsReceipt.objects.create(created_by=self.context["request"].user, **validated_data)
        for line in lines:
            GoodsReceiptLine.objects.create(receipt=receipt, **line)
        return receipt

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.status != GoodsReceipt.Status.DRAFT:
            raise serializers.ValidationError("Posted receipts cannot be edited.")
        lines = validated_data.pop("lines", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            for line in lines:
                GoodsReceiptLine.objects.create(receipt=instance, **line)
        return instance


class StockIssueLineSerializer(serializers.ModelSerializer):
    product_package_id = serializers.PrimaryKeyRelatedField(
        source="product_package", queryset=ProductPackage.objects.filter(is_active=True)
    )
    sku = serializers.CharField(source="product_package.product.sku", read_only=True)
    product_name = serializers.CharField(source="product_package.product.name", read_only=True)
    package_type = serializers.CharField(source="product_package.package_type", read_only=True)

    class Meta:
        model = StockIssueLine
        fields = [
            "id",
            "product_package_id",
            "sku",
            "product_name",
            "package_type",
            "package_quantity",
            "unit_price",
            "base_quantity",
            "line_total",
        ]
        read_only_fields = ["base_quantity", "line_total"]


class StockIssueSerializer(serializers.ModelSerializer):
    lines = StockIssueLineSerializer(many=True)
    source_warehouse_name = serializers.CharField(source="source_warehouse.name", read_only=True)
    target_warehouse_name = serializers.CharField(source="target_warehouse.name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = StockIssue
        fields = "__all__"
        read_only_fields = ["issue_no", "status", "total_amount", "created_by"]

    def validate(self, attrs):
        issue_type = attrs.get("issue_type", getattr(self.instance, "issue_type", None))
        target = attrs.get("target_warehouse", getattr(self.instance, "target_warehouse", None))
        source = attrs.get("source_warehouse", getattr(self.instance, "source_warehouse", None))
        if issue_type == StockIssue.IssueType.TRANSFER and not target:
            raise serializers.ValidationError("Target warehouse is required for transfer.")
        if issue_type == StockIssue.IssueType.TRANSFER and source and target and source.pk == target.pk:
            raise serializers.ValidationError("Source and target warehouse must differ.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop("lines", [])
        issue = StockIssue.objects.create(created_by=self.context["request"].user, **validated_data)
        for line in lines:
            StockIssueLine.objects.create(issue=issue, **line)
        return issue

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.status != StockIssue.Status.DRAFT:
            raise serializers.ValidationError("Posted issues cannot be edited.")
        lines = validated_data.pop("lines", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            for line in lines:
                StockIssueLine.objects.create(issue=instance, **line)
        return instance


class BasketItemSerializer(serializers.ModelSerializer):
    product_package_id = serializers.IntegerField(source="product_package.id", read_only=True)
    sku = serializers.CharField(source="product_package.product.sku", read_only=True)
    product_name = serializers.CharField(source="product_package.product.name", read_only=True)
    package_type = serializers.CharField(source="product_package.package_type", read_only=True)
    promotion_name = serializers.CharField(source="promotion.name", read_only=True)

    class Meta:
        model = BasketItem
        fields = "__all__"


class BasketSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Basket
        fields = "__all__"
        read_only_fields = ["basket_no", "status", "subtotal", "discount_total", "grand_total", "created_by"]

    def create(self, validated_data):
        return Basket.objects.create(created_by=self.context["request"].user, **validated_data)


class SaleSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    cashier_name = serializers.CharField(source="cashier.username", read_only=True)
    basket_no = serializers.CharField(source="basket.basket_no", read_only=True)

    class Meta:
        model = Sale
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]


class UserSerializer(serializers.ModelSerializer):
    group_ids = serializers.PrimaryKeyRelatedField(
        source="groups", queryset=Group.objects.all(), many=True, required=False
    )
    groups = serializers.StringRelatedField(many=True, read_only=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "groups",
            "group_ids",
            "password",
        ]

    def create(self, validated_data):
        groups = validated_data.pop("groups", [])
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        user.groups.set(groups)
        return user

    def update(self, instance, validated_data):
        groups = validated_data.pop("groups", None)
        password = validated_data.pop("password", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        if groups is not None:
            instance.groups.set(groups)
        return instance
