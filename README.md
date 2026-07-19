# FreshFlow Store Retail Management

A local-first Store Retail Management Web Application built with React, Django REST Framework, Python, and Microsoft SQL Server. DBeaver is used to create, inspect, and maintain the local database.

The UI uses a comfortable supermarket-inspired green, white, and red visual system with responsive layouts for TV, PC, notebook, tablet, and smartphone screens. It is inspired by the requested retail direction without copying Tops assets, logos, or proprietary page layouts.

## Included features

- Vendor and customer master data
- Product master with unique SKU
- Unit, pack, pallet, and container package conversion
- Purchase and selling price by package
- Goods receipt / stock import
- Sale, scrap, and warehouse transfer stock export
- Current stock by warehouse
- Safety-stock alerts
- Basket before checkout
- Confirmed sale history
- Percentage, fixed-value, and buy-X-get-Y promotions
- JWT login
- Admin, Manager, Inventory, Cashier, and Viewer roles
- Immutable stock transaction ledger
- Negative-stock protection
- Responsive dashboard and operational pages

## Technology versions

- Python 3.12 recommended
- Django 6.0.7
- Django REST Framework 3.16.1
- `mssql-django` 1.7.3
- Microsoft ODBC Driver 18
- Node.js 24 LTS recommended
- React 19
- Vite 8
- Microsoft SQL Server 2025 Express or Developer

## Quick start on Windows

Read the full guide first: [docs/INSTALL_WINDOWS.md](docs/INSTALL_WINDOWS.md)

After installing Python, Node.js, SQL Server, ODBC Driver 18, and DBeaver:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup-windows.ps1
```

Create the database by running [database/create_database.sql](database/create_database.sql) in DBeaver, edit `backend/.env`, then run:

```powershell
.\initialize-database.ps1
.\start-dev.ps1
```

Open `http://localhost:5173`.

## Demo accounts

| Role | Username | Password |
|---|---|---|
| Admin | admin | Admin@12345 |
| Manager | manager | Manager@12345 |
| Inventory | inventory | Inventory@12345 |
| Cashier | cashier | Cashier@12345 |
| Viewer | viewer | Viewer@12345 |

Change every demo password before entering real data.

## Project structure

```text
store-retail-management/
├─ backend/
│  ├─ config/                 Django settings and routes
│  ├─ core/                   Models, APIs, permissions, services, tests
│  ├─ manage.py
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ src/components/         Shared UI components
│  ├─ src/pages/              Operational screens
│  ├─ src/api.js              Axios + JWT refresh
│  ├─ src/styles.css          Responsive retail theme
│  ├─ package.json
│  └─ .env.example
├─ database/
│  └─ create_database.sql
├─ docs/
│  ├─ INSTALL_WINDOWS.md
│  ├─ ARCHITECTURE.md
│  └─ ADDED_REQUIREMENTS.md
├─ setup-windows.ps1
├─ initialize-database.ps1
├─ start-dev.ps1
└─ run-sqlite-demo.ps1
```

## Main workflow

### Receive stock

1. Create vendor, product, packages, and warehouse.
2. Create a goods receipt in draft state.
3. Add receipt lines using package quantities.
4. Post the receipt.
5. The system increases `StockBalance` and writes a `StockTransaction` ledger entry.

### Sell through basket

1. Create an open basket.
2. Add product packages.
3. The best active product promotion is recalculated automatically.
4. Checkout validates available stock.
5. The system creates the sale, reduces stock, writes the ledger, and confirms the basket.

### Scrap or transfer

1. Create a stock issue with type Scrap or Transfer.
2. Add issue lines.
3. For transfer, select different source and target warehouses.
4. Post the issue.
5. Transfer creates matching out and in ledger entries.

## Validation completed for this package

- Django system checks passed.
- Initial migrations were generated and applied in the included quick-test environment.
- Demo seed command completed.
- Automated inventory flow test covers receipt, basket, checkout, and final balance.
- API smoke test completed for receipt posting and checkout.
- React production build completed with Vite.

An actual connection to your own SQL Server instance cannot be tested from this package environment. The Microsoft SQL Server backend configuration follows the official `mssql-django` format; the final connection depends on your instance name, authentication mode, ODBC installation, password, TCP setting, and firewall.

## Documentation

- [Windows installation](docs/INSTALL_WINDOWS.md)
- [Architecture and ERD](docs/ARCHITECTURE.md)
- [Requirements added to complete the workflow](docs/ADDED_REQUIREMENTS.md)
