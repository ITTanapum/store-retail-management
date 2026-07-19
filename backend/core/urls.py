from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BasketViewSet,
    CategoryViewSet,
    CustomerViewSet,
    GoodsReceiptViewSet,
    GroupViewSet,
    ProductPackageViewSet,
    ProductViewSet,
    PromotionViewSet,
    SaleViewSet,
    StockBalanceViewSet,
    StockIssueViewSet,
    StockTransactionViewSet,
    UserViewSet,
    VendorViewSet,
    WarehouseViewSet,
    dashboard_summary,
    me,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("vendors", VendorViewSet)
router.register("customers", CustomerViewSet)
router.register("warehouses", WarehouseViewSet)
router.register("products", ProductViewSet, basename="product")
router.register("product-packages", ProductPackageViewSet)
router.register("promotions", PromotionViewSet)
router.register("stock-balances", StockBalanceViewSet)
router.register("stock-transactions", StockTransactionViewSet)
router.register("goods-receipts", GoodsReceiptViewSet)
router.register("stock-issues", StockIssueViewSet)
router.register("baskets", BasketViewSet)
router.register("sales", SaleViewSet)
router.register("groups", GroupViewSet)
router.register("users", UserViewSet)

urlpatterns = [
    path("auth/me/", me, name="auth-me"),
    path("dashboard/summary/", dashboard_summary, name="dashboard-summary"),
    *router.urls,
]
