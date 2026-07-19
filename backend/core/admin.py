from django.contrib import admin

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


class ProductPackageInline(admin.TabularInline):
    model = ProductPackage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "safety_stock", "is_active")
    search_fields = ("sku", "barcode", "name")
    list_filter = ("category", "is_active", "track_expiry")
    inlines = [ProductPackageInline]


class GoodsReceiptLineInline(admin.TabularInline):
    model = GoodsReceiptLine
    extra = 0


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ("receipt_no", "vendor", "warehouse", "status", "received_at", "total_cost")
    list_filter = ("status", "warehouse")
    search_fields = ("receipt_no", "supplier_invoice_no", "vendor__name")
    inlines = [GoodsReceiptLineInline]


class StockIssueLineInline(admin.TabularInline):
    model = StockIssueLine
    extra = 0


@admin.register(StockIssue)
class StockIssueAdmin(admin.ModelAdmin):
    list_display = ("issue_no", "issue_type", "source_warehouse", "target_warehouse", "status", "issued_at")
    list_filter = ("issue_type", "status", "source_warehouse")
    search_fields = ("issue_no", "customer__name")
    inlines = [StockIssueLineInline]


class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 0


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ("basket_no", "customer", "warehouse", "status", "grand_total", "created_by")
    list_filter = ("status", "warehouse")
    search_fields = ("basket_no", "customer__name")
    inlines = [BasketItemInline]


admin.site.register(Category)
admin.site.register(Vendor)
admin.site.register(Customer)
admin.site.register(Warehouse)
admin.site.register(Promotion)
admin.site.register(StockBalance)
admin.site.register(StockTransaction)
admin.site.register(Sale)
