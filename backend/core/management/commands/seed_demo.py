from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
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

MONEY = Decimal("0.01")
QTY = Decimal("0.001")


def money(value):
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


def qty(value):
    return Decimal(str(value)).quantize(QTY, rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = "Seed realistic demo data for every retail-management model."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing core retail data before creating the demo dataset.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self._reset_core_data()

        users = self._seed_roles_and_users()
        warehouses = self._seed_warehouses()
        vendors = self._seed_vendors()
        customers = self._seed_customers()
        products, packages = self._seed_products_and_packages()
        promotions = self._seed_promotions(products)

        balances = {(product.id, warehouse.id): Decimal("0") for product in products.values() for warehouse in warehouses.values()}

        self._seed_goods_receipts(users, warehouses, vendors, packages, balances)
        self._seed_stock_issues(users, warehouses, customers, packages, balances)
        self._seed_baskets_and_sales(users, warehouses, customers, packages, promotions, balances)
        self._seed_open_and_cancelled_baskets(users, warehouses, customers, packages, promotions)
        self._save_balances(products, warehouses, balances)

        self.stdout.write(self.style.SUCCESS("Retail demo data created successfully."))
        self.stdout.write("Run the server and sign in with one of these accounts:")
        for username, password, role, *_ in self.demo_users:
            self.stdout.write(f"  {role:9} {username:10} / {password}")
        self.stdout.write("Important: change all demo passwords before production use.")

    def _reset_core_data(self):
        # Delete dependent records first to respect PROTECT and OneToOne relations.
        StockTransaction.objects.all().delete()
        Sale.objects.all().delete()
        BasketItem.objects.all().delete()
        Basket.objects.all().delete()
        StockIssueLine.objects.all().delete()
        StockIssue.objects.all().delete()
        GoodsReceiptLine.objects.all().delete()
        GoodsReceipt.objects.all().delete()
        StockBalance.objects.all().delete()
        Promotion.objects.all().delete()
        ProductPackage.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Customer.objects.all().delete()
        Vendor.objects.all().delete()
        Warehouse.objects.all().delete()
        self.stdout.write(self.style.WARNING("Existing core retail data was deleted."))

    def _seed_roles_and_users(self):
        role_permissions = {
            "Admin": Permission.objects.all(),
            "Manager": Permission.objects.filter(content_type__app_label="core"),
            "Inventory": Permission.objects.filter(
                content_type__app_label="core",
                codename__in=[
                    "view_category", "view_vendor", "add_vendor", "change_vendor",
                    "view_customer", "add_customer", "change_customer",
                    "view_warehouse", "add_warehouse", "change_warehouse",
                    "view_product", "add_product", "change_product",
                    "view_productpackage", "add_productpackage", "change_productpackage",
                    "view_goodsreceipt", "add_goodsreceipt", "change_goodsreceipt",
                    "view_goodsreceiptline", "add_goodsreceiptline", "change_goodsreceiptline",
                    "view_stockissue", "add_stockissue", "change_stockissue",
                    "view_stockissueline", "add_stockissueline", "change_stockissueline",
                    "view_stockbalance", "view_stocktransaction",
                ],
            ),
            "Cashier": Permission.objects.filter(
                content_type__app_label="core",
                codename__in=[
                    "view_product", "view_productpackage", "view_customer",
                    "view_basket", "add_basket", "change_basket",
                    "view_basketitem", "add_basketitem", "change_basketitem", "delete_basketitem",
                    "view_sale", "add_sale", "view_stockbalance",
                ],
            ),
            "Viewer": Permission.objects.filter(
                content_type__app_label="core", codename__startswith="view_"
            ),
        }

        groups = {}
        for role, permissions in role_permissions.items():
            group, _ = Group.objects.get_or_create(name=role)
            group.permissions.set(permissions)
            groups[role] = group

        self.demo_users = [
            ("admin", "Admin@12345", "Admin", True, True),
            ("manager", "Manager@12345", "Manager", True, False),
            ("inventory", "Inventory@12345", "Inventory", True, False),
            ("cashier", "Cashier@12345", "Cashier", False, False),
            ("viewer", "Viewer@12345", "Viewer", False, False),
        ]
        result = {}
        for username, password, role, is_staff, is_superuser in self.demo_users:
            user, _ = User.objects.get_or_create(username=username)
            user.first_name = role
            user.last_name = "Demo"
            user.email = f"{username}@retail-demo.local"
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.is_active = True
            user.set_password(password)
            user.save()
            user.groups.set([groups[role]])
            result[username] = user
        return result

    def _seed_warehouses(self):
        rows = [
            ("MAIN", "Main Store", "88 Sukhumvit Road, Bangkok"),
            ("BACK", "Backroom Storage", "Rear building, Main Store"),
            ("DC01", "Bangkok Distribution Center", "Bang Na-Trat Road, Bangkok"),
        ]
        result = {}
        for code, name, address in rows:
            obj, _ = Warehouse.objects.update_or_create(
                code=code,
                defaults={"name": name, "address": address, "is_active": True},
            )
            result[code] = obj
        return result

    def _seed_vendors(self):
        rows = [
            ("V0001", "Siam Consumer Distribution Co., Ltd.", "0105559001001", "Nattapong S.", "02-100-1001", "sales@siamconsumer.example", "Bangkok", 30),
            ("V0002", "Thai Fresh Foods Supply Co., Ltd.", "0105559001002", "Pimchanok K.", "02-100-1002", "orders@thaifresh.example", "Pathum Thani", 15),
            ("V0003", "Metro Beverage Trading Co., Ltd.", "0105559001003", "Somsak P.", "02-100-1003", "contact@metrobeverage.example", "Nonthaburi", 30),
            ("V0004", "Clean Home Products Co., Ltd.", "0105559001004", "Araya T.", "02-100-1004", "sales@cleanhome.example", "Samut Prakan", 45),
        ]
        result = {}
        for code, name, tax_id, contact, phone, email, address, terms in rows:
            obj, _ = Vendor.objects.update_or_create(
                code=code,
                defaults={
                    "name": name, "tax_id": tax_id, "contact_name": contact,
                    "phone": phone, "email": email, "address": address,
                    "payment_terms_days": terms, "is_active": True,
                },
            )
            result[code] = obj
        return result

    def _seed_customers(self):
        rows = [
            ("WALKIN", "Walk-in Customer", None, "", "", "", "", 0),
            ("C0001", "Anan Chaiyasit", "MBR-0001", "", "081-111-1001", "anan@example.com", "Bangkok", 185),
            ("C0002", "Benjamas Rattanakul", "MBR-0002", "", "081-111-1002", "benjamas@example.com", "Nonthaburi", 420),
            ("C0003", "Chaiwat Mini Mart", "MBR-0003", "0105567003003", "02-222-3003", "purchase@chaiwatmart.example", "Bangkok", 950),
            ("C0004", "Darunee Srisuk", "MBR-0004", "", "081-111-1004", "darunee@example.com", "Samut Prakan", 75),
            ("C0005", "Ekkachai Office Co., Ltd.", "MBR-0005", "0105567003005", "02-222-3005", "admin@ekkachaioffice.example", "Pathum Thani", 1200),
        ]
        result = {}
        for code, name, member_no, tax_id, phone, email, address, points in rows:
            obj, _ = Customer.objects.update_or_create(
                code=code,
                defaults={
                    "name": name, "member_no": member_no, "tax_id": tax_id,
                    "phone": phone, "email": email, "address": address,
                    "loyalty_points": points, "is_active": True,
                },
            )
            result[code] = obj
        return result

    def _seed_products_and_packages(self):
        categories_data = [
            ("Grocery", "Rice, noodles, cooking ingredients and dry food"),
            ("Beverage", "Water, soft drinks, juice, coffee and tea"),
            ("Snack", "Biscuits, chips, chocolate and confectionery"),
            ("Personal Care", "Daily personal hygiene products"),
            ("Household", "Cleaning and household supplies"),
            ("Dairy & Chilled", "Milk and refrigerated products"),
        ]
        categories = {}
        for name, description in categories_data:
            obj, _ = Category.objects.update_or_create(
                name=name,
                defaults={"description": description, "is_active": True},
            )
            categories[name] = obj

        product_rows = [
            ("SKU-1001", "8850000001001", "Thai Jasmine Rice 5 kg", "Premium fragrant rice", "Grocery", "bag", 20, False, 165, 189, 6),
            ("SKU-1002", "8850000001002", "Drinking Water 600 ml", "Purified drinking water", "Beverage", "bottle", 96, False, 6, 8, 12),
            ("SKU-1003", "8850000001003", "Orange Juice 1 L", "100% orange juice", "Beverage", "carton", 24, True, 48, 59, 12),
            ("SKU-1004", "8850000001004", "Instant Noodles Tom Yum", "Spicy tom yum flavor", "Grocery", "pack", 60, False, 6, 8, 30),
            ("SKU-1005", "8850000001005", "Potato Chips Original 50 g", "Crispy salted potato chips", "Snack", "bag", 36, False, 17, 22, 12),
            ("SKU-1006", "8850000001006", "Chocolate Sandwich Biscuits", "Chocolate cream biscuits", "Snack", "pack", 30, False, 20, 27, 12),
            ("SKU-1007", "8850000001007", "UHT Milk 200 ml", "Plain UHT milk", "Dairy & Chilled", "box", 48, True, 10, 13, 36),
            ("SKU-1008", "8850000001008", "Shampoo Fresh Care 450 ml", "Daily care shampoo", "Personal Care", "bottle", 15, False, 89, 119, 6),
            ("SKU-1009", "8850000001009", "Liquid Hand Soap 250 ml", "Antibacterial hand soap", "Personal Care", "bottle", 18, False, 42, 55, 12),
            ("SKU-1010", "8850000001010", "Laundry Detergent 800 g", "Concentrated powder detergent", "Household", "bag", 20, False, 62, 79, 12),
            ("SKU-1011", "8850000001011", "Facial Tissue 3-Ply 180 Sheets", "Soft facial tissue", "Household", "box", 24, False, 28, 39, 5),
            ("SKU-1012", "8850000001012", "Cola Soft Drink 1.25 L", "Carbonated cola beverage", "Beverage", "bottle", 24, False, 24, 32, 12),
        ]

        products = {}
        packages = {}
        for sku, barcode, name, description, category, base_unit, safety, expiry, purchase, selling, pack_units in product_rows:
            product, _ = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "barcode": barcode, "name": name, "description": description,
                    "category": categories[category], "base_unit_name": base_unit,
                    "safety_stock": qty(safety), "track_expiry": expiry, "is_active": True,
                },
            )
            products[sku] = product

            package_specs = [
                (ProductPackage.PackageType.UNIT, "Unit", 1, purchase, selling),
                (ProductPackage.PackageType.PACK, f"Pack of {pack_units}", pack_units, money(purchase * pack_units * Decimal("0.94")), money(selling * pack_units * Decimal("0.95"))),
                (ProductPackage.PackageType.PALLET, "Pallet", pack_units * 40, money(purchase * pack_units * 40 * Decimal("0.88")), money(selling * pack_units * 40 * Decimal("0.90"))),
                (ProductPackage.PackageType.CONTAINER, "Container", pack_units * 400, money(purchase * pack_units * 400 * Decimal("0.82")), money(selling * pack_units * 400 * Decimal("0.85"))),
            ]
            for package_type, label, units, buy_price, sell_price in package_specs:
                package_barcode = f"{barcode}-{package_type[:2]}"
                package, _ = ProductPackage.objects.update_or_create(
                    product=product,
                    package_type=package_type,
                    defaults={
                        "label": label, "barcode": package_barcode,
                        "units_per_package": qty(units),
                        "default_purchase_price": money(buy_price),
                        "default_selling_price": money(sell_price),
                        "is_active": True,
                    },
                )
                packages[(sku, package_type)] = package
        return products, packages

    def _seed_promotions(self, products):
        now = timezone.now()
        rows = [
            ("WELCOME5", "Member Welcome 5%", Promotion.PromotionType.PERCENT, 5, 1, 0, 0, -30, 365, ["SKU-1001", "SKU-1003", "SKU-1008"]),
            ("SNACK10", "Snack Festival 10%", Promotion.PromotionType.PERCENT, 10, 2, 0, 0, -7, 30, ["SKU-1005", "SKU-1006"]),
            ("SAVE20", "Save 20 Baht", Promotion.PromotionType.FIXED, 20, 3, 0, 0, -15, 45, ["SKU-1010", "SKU-1011"]),
            ("BUY2GET1", "Buy 2 Get 1 Water", Promotion.PromotionType.BUY_X_GET_Y, 0, 2, 2, 1, -10, 60, ["SKU-1002"]),
        ]
        result = {}
        for code, name, promo_type, value, minimum, buy_qty, get_qty, start_days, end_days, product_skus in rows:
            promo, _ = Promotion.objects.update_or_create(
                code=code,
                defaults={
                    "name": name, "promotion_type": promo_type,
                    "value": money(value), "minimum_quantity": qty(minimum),
                    "buy_quantity": buy_qty, "get_quantity": get_qty,
                    "start_at": now + timedelta(days=start_days),
                    "end_at": now + timedelta(days=end_days), "is_active": True,
                },
            )
            promo.products.set([products[sku] for sku in product_skus])
            result[code] = promo
        return result

    def _add_balance(self, balances, product, warehouse, amount):
        key = (product.id, warehouse.id)
        balances[key] = qty(balances.get(key, Decimal("0")) + Decimal(amount))

    def _seed_goods_receipts(self, users, warehouses, vendors, packages, balances):
        now = timezone.now()
        receipts = [
            ("GRN-DEMO-0001", "V0001", "DC01", "INV-SCD-260701", GoodsReceipt.Status.POSTED, -18, [
                ("SKU-1001", "PACK", 20), ("SKU-1004", "PACK", 40), ("SKU-1006", "PACK", 24),
            ]),
            ("GRN-DEMO-0002", "V0003", "MAIN", "INV-MBT-260705", GoodsReceipt.Status.POSTED, -14, [
                ("SKU-1002", "PACK", 50), ("SKU-1003", "PACK", 15), ("SKU-1012", "PACK", 18),
            ]),
            ("GRN-DEMO-0003", "V0002", "BACK", "INV-TFF-260708", GoodsReceipt.Status.POSTED, -11, [
                ("SKU-1005", "PACK", 20), ("SKU-1007", "PACK", 12),
            ]),
            ("GRN-DEMO-0004", "V0004", "MAIN", "INV-CHP-260710", GoodsReceipt.Status.POSTED, -8, [
                ("SKU-1008", "PACK", 12), ("SKU-1009", "PACK", 15), ("SKU-1010", "PACK", 18), ("SKU-1011", "PACK", 20),
            ]),
            ("GRN-DEMO-0005", "V0001", "MAIN", "INV-SCD-DRAFT", GoodsReceipt.Status.DRAFT, -1, [
                ("SKU-1001", "PACK", 5), ("SKU-1004", "PACK", 10),
            ]),
            ("GRN-DEMO-0006", "V0003", "BACK", "INV-MBT-CANCEL", GoodsReceipt.Status.CANCELLED, -5, [
                ("SKU-1003", "PACK", 4),
            ]),
        ]

        for receipt_no, vendor_code, warehouse_code, invoice, status, days, lines in receipts:
            receipt, _ = GoodsReceipt.objects.update_or_create(
                receipt_no=receipt_no,
                defaults={
                    "vendor": vendors[vendor_code], "warehouse": warehouses[warehouse_code],
                    "supplier_invoice_no": invoice, "status": status,
                    "received_at": now + timedelta(days=days), "notes": "Generated realistic demo receipt",
                    "created_by": users["inventory"], "total_cost": Decimal("0"),
                },
            )
            receipt.lines.all().delete()
            total = Decimal("0")
            for sku, package_type, package_qty in lines:
                package = packages[(sku, package_type)]
                line = GoodsReceiptLine.objects.create(
                    receipt=receipt, product_package=package,
                    package_quantity=qty(package_qty), unit_cost=package.default_purchase_price,
                )
                total += line.line_total
                if status == GoodsReceipt.Status.POSTED:
                    self._add_balance(balances, package.product, warehouses[warehouse_code], line.base_quantity)
                    StockTransaction.objects.update_or_create(
                        reference_no=receipt_no,
                        product=package.product,
                        warehouse=warehouses[warehouse_code],
                        package_type=package_type,
                        defaults={
                            "transaction_type": StockTransaction.TransactionType.RECEIPT,
                            "package_quantity": line.package_quantity,
                            "quantity_base": line.base_quantity,
                            "unit_cost": line.unit_cost,
                            "unit_price": Decimal("0"),
                            "occurred_at": receipt.received_at,
                            "performed_by": users["inventory"],
                            "notes": f"Posted goods receipt {receipt_no}",
                        },
                    )
            receipt.total_cost = money(total)
            receipt.save(update_fields=["total_cost", "updated_at"])

    def _seed_stock_issues(self, users, warehouses, customers, packages, balances):
        now = timezone.now()
        issues = [
            ("ISS-DEMO-0001", StockIssue.IssueType.TRANSFER, "DC01", "MAIN", None, StockIssue.Status.POSTED, -12, "Replenish main store", [
                ("SKU-1001", "PACK", 8), ("SKU-1004", "PACK", 12), ("SKU-1006", "PACK", 5),
            ]),
            ("ISS-DEMO-0002", StockIssue.IssueType.TRANSFER, "BACK", "MAIN", None, StockIssue.Status.POSTED, -7, "Move fast-selling stock to shop floor", [
                ("SKU-1005", "PACK", 6), ("SKU-1007", "PACK", 4),
            ]),
            ("ISS-DEMO-0003", StockIssue.IssueType.SCRAP, "MAIN", None, None, StockIssue.Status.POSTED, -4, "Damaged during handling", [
                ("SKU-1003", "UNIT", 3), ("SKU-1012", "UNIT", 2),
            ]),
            ("ISS-DEMO-0004", StockIssue.IssueType.SALE, "MAIN", None, "C0003", StockIssue.Status.POSTED, -3, "Wholesale counter order", [
                ("SKU-1002", "PACK", 4), ("SKU-1004", "PACK", 3), ("SKU-1011", "PACK", 2),
            ]),
            ("ISS-DEMO-0005", StockIssue.IssueType.TRANSFER, "MAIN", "BACK", None, StockIssue.Status.DRAFT, 0, "Planned backroom transfer", [
                ("SKU-1008", "PACK", 2),
            ]),
        ]

        for issue_no, issue_type, source_code, target_code, customer_code, status, days, reason, lines in issues:
            issue, _ = StockIssue.objects.update_or_create(
                issue_no=issue_no,
                defaults={
                    "issue_type": issue_type,
                    "source_warehouse": warehouses[source_code],
                    "target_warehouse": warehouses[target_code] if target_code else None,
                    "customer": customers[customer_code] if customer_code else None,
                    "status": status, "issued_at": now + timedelta(days=days),
                    "reason": reason, "total_amount": Decimal("0"),
                    "created_by": users["inventory"],
                },
            )
            issue.lines.all().delete()
            total = Decimal("0")
            for sku, package_type, package_qty in lines:
                package = packages[(sku, package_type)]
                line = StockIssueLine.objects.create(
                    issue=issue, product_package=package,
                    package_quantity=qty(package_qty), unit_price=package.default_selling_price,
                )
                total += line.line_total
                if status != StockIssue.Status.POSTED:
                    continue

                self._add_balance(balances, package.product, warehouses[source_code], -line.base_quantity)
                out_type = {
                    StockIssue.IssueType.SALE: StockTransaction.TransactionType.SALE,
                    StockIssue.IssueType.SCRAP: StockTransaction.TransactionType.SCRAP,
                    StockIssue.IssueType.TRANSFER: StockTransaction.TransactionType.TRANSFER_OUT,
                }[issue_type]
                StockTransaction.objects.update_or_create(
                    reference_no=issue_no,
                    product=package.product,
                    warehouse=warehouses[source_code],
                    package_type=package_type,
                    defaults={
                        "transaction_type": out_type,
                        "package_quantity": line.package_quantity,
                        "quantity_base": -line.base_quantity,
                        "unit_cost": package.default_purchase_price,
                        "unit_price": line.unit_price,
                        "occurred_at": issue.issued_at,
                        "performed_by": users["inventory"],
                        "notes": reason,
                    },
                )

                if issue_type == StockIssue.IssueType.TRANSFER and target_code:
                    self._add_balance(balances, package.product, warehouses[target_code], line.base_quantity)
                    StockTransaction.objects.update_or_create(
                        reference_no=f"{issue_no}-IN",
                        product=package.product,
                        warehouse=warehouses[target_code],
                        package_type=package_type,
                        defaults={
                            "transaction_type": StockTransaction.TransactionType.TRANSFER_IN,
                            "package_quantity": line.package_quantity,
                            "quantity_base": line.base_quantity,
                            "unit_cost": package.default_purchase_price,
                            "unit_price": Decimal("0"),
                            "occurred_at": issue.issued_at,
                            "performed_by": users["inventory"],
                            "notes": f"Transfer received from {source_code}",
                        },
                    )
            issue.total_amount = money(total)
            issue.save(update_fields=["total_amount", "updated_at"])

    def _seed_baskets_and_sales(self, users, warehouses, customers, packages, promotions, balances):
        now = timezone.now()
        sale_rows = [
            ("BSK-DEMO-0001", "SAL-DEMO-0001", "C0001", -6, [("SKU-1001", "UNIT", 1, "WELCOME5"), ("SKU-1003", "UNIT", 2, "WELCOME5"), ("SKU-1005", "UNIT", 3, "SNACK10")]),
            ("BSK-DEMO-0002", "SAL-DEMO-0002", "WALKIN", -5, [("SKU-1002", "UNIT", 6, None), ("SKU-1004", "UNIT", 5, None), ("SKU-1009", "UNIT", 1, None)]),
            ("BSK-DEMO-0003", "SAL-DEMO-0003", "C0002", -2, [("SKU-1006", "UNIT", 2, "SNACK10"), ("SKU-1007", "UNIT", 12, None), ("SKU-1010", "UNIT", 3, "SAVE20")]),
            ("BSK-DEMO-0004", "SAL-DEMO-0004", "C0004", -1, [("SKU-1008", "UNIT", 1, "WELCOME5"), ("SKU-1011", "UNIT", 4, "SAVE20"), ("SKU-1012", "UNIT", 2, None)]),
        ]

        for basket_no, sale_no, customer_code, days, items in sale_rows:
            subtotal = Decimal("0")
            discount_total = Decimal("0")
            computed_items = []
            for sku, package_type, package_qty, promo_code in items:
                package = packages[(sku, package_type)]
                line_subtotal = money(package.default_selling_price * Decimal(package_qty))
                discount = Decimal("0")
                promo = promotions.get(promo_code) if promo_code else None
                if promo:
                    if promo.promotion_type == Promotion.PromotionType.PERCENT:
                        discount = money(line_subtotal * promo.value / Decimal("100"))
                    elif promo.promotion_type == Promotion.PromotionType.FIXED:
                        discount = min(money(promo.value), line_subtotal)
                line_total = money(line_subtotal - discount)
                subtotal += line_subtotal
                discount_total += discount
                computed_items.append((package, package_qty, promo, discount, line_total))

            grand_total = money(subtotal - discount_total)
            basket, _ = Basket.objects.update_or_create(
                basket_no=basket_no,
                defaults={
                    "customer": customers[customer_code], "warehouse": warehouses["MAIN"],
                    "status": Basket.Status.CONFIRMED, "subtotal": money(subtotal),
                    "discount_total": money(discount_total), "grand_total": grand_total,
                    "created_by": users["cashier"],
                },
            )
            basket.items.all().delete()
            for package, package_qty, promo, discount, line_total in computed_items:
                BasketItem.objects.create(
                    basket=basket, product_package=package,
                    package_quantity=qty(package_qty), unit_price=package.default_selling_price,
                    promotion=promo, discount_amount=money(discount), line_total=line_total,
                )
                base_qty = qty(Decimal(package_qty) * package.units_per_package)
                self._add_balance(balances, package.product, warehouses["MAIN"], -base_qty)
                StockTransaction.objects.update_or_create(
                    reference_no=sale_no,
                    product=package.product,
                    warehouse=warehouses["MAIN"],
                    package_type=package.package_type,
                    defaults={
                        "transaction_type": StockTransaction.TransactionType.SALE,
                        "package_quantity": qty(package_qty), "quantity_base": -base_qty,
                        "unit_cost": package.default_purchase_price,
                        "unit_price": package.default_selling_price,
                        "occurred_at": now + timedelta(days=days),
                        "performed_by": users["cashier"],
                        "notes": f"POS sale from basket {basket_no}",
                    },
                )

            Sale.objects.update_or_create(
                sale_no=sale_no,
                defaults={
                    "basket": basket, "customer": customers[customer_code],
                    "warehouse": warehouses["MAIN"], "subtotal": money(subtotal),
                    "discount_total": money(discount_total), "grand_total": grand_total,
                    "sold_at": now + timedelta(days=days), "cashier": users["cashier"],
                },
            )

    def _seed_open_and_cancelled_baskets(self, users, warehouses, customers, packages, promotions):
        rows = [
            ("BSK-DEMO-OPEN", Basket.Status.OPEN, "C0005", [("SKU-1002", "PACK", 2, None), ("SKU-1011", "UNIT", 3, "SAVE20")]),
            ("BSK-DEMO-CANCEL", Basket.Status.CANCELLED, "C0002", [("SKU-1005", "UNIT", 2, "SNACK10")]),
        ]
        for basket_no, status, customer_code, items in rows:
            basket, _ = Basket.objects.update_or_create(
                basket_no=basket_no,
                defaults={
                    "customer": customers[customer_code], "warehouse": warehouses["MAIN"],
                    "status": status, "created_by": users["cashier"],
                    "subtotal": Decimal("0"), "discount_total": Decimal("0"), "grand_total": Decimal("0"),
                },
            )
            basket.items.all().delete()
            subtotal = Decimal("0")
            discount_total = Decimal("0")
            for sku, package_type, package_qty, promo_code in items:
                package = packages[(sku, package_type)]
                line_subtotal = money(package.default_selling_price * Decimal(package_qty))
                promo = promotions.get(promo_code) if promo_code else None
                discount = Decimal("0")
                if promo and promo.promotion_type == Promotion.PromotionType.PERCENT:
                    discount = money(line_subtotal * promo.value / Decimal("100"))
                elif promo and promo.promotion_type == Promotion.PromotionType.FIXED:
                    discount = min(money(promo.value), line_subtotal)
                line_total = money(line_subtotal - discount)
                BasketItem.objects.create(
                    basket=basket, product_package=package, package_quantity=qty(package_qty),
                    unit_price=package.default_selling_price, promotion=promo,
                    discount_amount=money(discount), line_total=line_total,
                )
                subtotal += line_subtotal
                discount_total += discount
            basket.subtotal = money(subtotal)
            basket.discount_total = money(discount_total)
            basket.grand_total = money(subtotal - discount_total)
            basket.save(update_fields=["subtotal", "discount_total", "grand_total", "updated_at"])

    def _save_balances(self, products, warehouses, balances):
        for product in products.values():
            for warehouse in warehouses.values():
                StockBalance.objects.update_or_create(
                    product=product,
                    warehouse=warehouse,
                    defaults={"quantity_base": qty(balances[(product.id, warehouse.id)])},
                )