from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from .models import (
    Basket,
    Category,
    Customer,
    GoodsReceipt,
    GoodsReceiptLine,
    Product,
    ProductPackage,
    StockBalance,
    Vendor,
    Warehouse,
)
from .services import add_basket_item, checkout_basket, post_goods_receipt


class InventoryFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="StrongPassword123!")
        self.category = Category.objects.create(name="Test")
        self.vendor = Vendor.objects.create(code="V-TEST", name="Test Vendor")
        self.customer = Customer.objects.create(code="C-TEST", name="Test Customer")
        self.warehouse = Warehouse.objects.create(code="WH-TEST", name="Test Warehouse")
        self.product = Product.objects.create(
            sku="SKU-TEST",
            name="Test Product",
            category=self.category,
            safety_stock=Decimal("2"),
        )
        self.package = ProductPackage.objects.create(
            product=self.product,
            package_type=ProductPackage.PackageType.UNIT,
            units_per_package=Decimal("1"),
            default_purchase_price=Decimal("10"),
            default_selling_price=Decimal("15"),
        )

    def test_receipt_then_checkout_updates_balance(self):
        receipt = GoodsReceipt.objects.create(
            vendor=self.vendor,
            warehouse=self.warehouse,
            created_by=self.user,
        )
        GoodsReceiptLine.objects.create(
            receipt=receipt,
            product_package=self.package,
            package_quantity=Decimal("10"),
            unit_cost=Decimal("10"),
        )
        post_goods_receipt(receipt, self.user)
        self.assertEqual(
            StockBalance.objects.get(product=self.product, warehouse=self.warehouse).quantity_base,
            Decimal("10"),
        )

        basket = Basket.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            created_by=self.user,
        )
        add_basket_item(
            basket=basket,
            product_package=self.package,
            package_quantity=Decimal("3"),
            unit_price=Decimal("15"),
        )
        sale = checkout_basket(basket, self.user)
        self.assertEqual(sale.grand_total, Decimal("45.00"))
        self.assertEqual(
            StockBalance.objects.get(product=self.product, warehouse=self.warehouse).quantity_base,
            Decimal("7"),
        )
