# Windows Local Installation Guide

This guide assumes Windows 10 or Windows 11 and a local SQL Server instance.

## 1. Install required programs

Install these applications in this order:

1. **Python 3.12 x64** — during installation enable **Add Python to PATH** and install the Python launcher.
2. **Node.js 24 LTS x64** — npm is included.
3. **Microsoft SQL Server 2025 Express** for a free small-server installation, or Developer edition for development/testing only.
4. **Microsoft ODBC Driver 18 for SQL Server x64**.
5. **DBeaver Community**.
6. **Visual Studio Code** and **Git** are optional but recommended.

Official download pages:

- Python: https://www.python.org/downloads/windows/
- Node.js: https://nodejs.org/en/download
- SQL Server: https://www.microsoft.com/sql-server/sql-server-downloads
- ODBC Driver 18: https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
- DBeaver Community: https://dbeaver.io/download/

## 2. Configure SQL Server

During SQL Server installation:

- Use instance name `SQLEXPRESS`, or note the instance name you choose.
- Enable SQL Server Authentication / mixed mode when available.
- Set and safely record the `sa` password.
- Install the Database Engine service.

For TCP connections, open **SQL Server Configuration Manager**, enable TCP/IP for the instance, then restart the SQL Server service. A named local instance can also be used as `localhost\SQLEXPRESS` without manually fixing a port.

## 3. Connect DBeaver

1. Open DBeaver.
2. Select **New Database Connection**.
3. Select **SQL Server**.
4. Use one of these server patterns:
   - Named instance: `localhost\SQLEXPRESS`
   - TCP: host `localhost`, port `1433`
5. Sign in with an administrator login such as `sa`.
6. Test the connection and allow DBeaver to download its JDBC driver when prompted.

## 4. Create the application database

1. In DBeaver, connect to the `master` database as an administrator.
2. Open `database/create_database.sql` from this project.
3. Change `ChangeThisStrongPassword!2026` to a strong local password.
4. Execute the entire script.
5. Confirm that `store_retail_db` and login `store_app` now exist.

The script grants `db_owner` for local development convenience. Use narrower database permissions before production use.

## 5. Prepare the project

Open PowerShell in the project root.

If scripts are blocked for the current PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Run:

```powershell
.\setup-windows.ps1
```

This creates `.venv`, installs Python packages, creates `.env` files, and runs `npm install`.

## 6. Configure the backend database connection

Open `backend/.env` and set values matching your SQL Server:

```env
DB_ENGINE=mssql
DB_NAME=store_retail_db
DB_USER=store_app
DB_PASSWORD=the-password-used-in-create_database.sql
DB_HOST=localhost\SQLEXPRESS
DB_PORT=
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_TRUST_CERTIFICATE=yes
DB_ENCRYPT=no
```

For a fixed TCP port, use:

```env
DB_HOST=localhost
DB_PORT=1433
```

## 7. Create Django tables and demo data

Run:

```powershell
.\initialize-database.ps1
```

The command performs Django checks, runs migrations, creates role groups, and inserts demo master data.

## 8. Start the web application

Run:

```powershell
.\start-dev.ps1
```

Open:

- Web application: `http://localhost:5173`
- Backend API: `http://127.0.0.1:8000/api/`
- Django Admin: `http://127.0.0.1:8000/admin/`

## 9. Demo accounts

Change these passwords before entering real business data.

| Role | Username | Password |
|---|---|---|
| Admin | admin | Admin@12345 |
| Manager | manager | Manager@12345 |
| Inventory | inventory | Inventory@12345 |
| Cashier | cashier | Cashier@12345 |
| Viewer | viewer | Viewer@12345 |

## 10. First operational test

1. Sign in as `admin`.
2. Open **Products & SKU** and confirm demo products are visible.
3. Open **Import Stock**, select the demo vendor, `MAIN` warehouse, a package, quantity, and cost, then post the receipt.
4. Open **Current Stock** and confirm the quantity increased.
5. Open **Basket / POS**, create a basket for `MAIN`, add the same product, and checkout.
6. Open **Stock Ledger** and confirm both receipt and sale transactions exist.
7. Open **Sales History** and confirm the sale record.

## 11. Use from another PC, phone, tablet, or TV on the same LAN

1. Find the server PC IPv4 address with `ipconfig`, for example `192.168.1.50`.
2. Add that IP to `DJANGO_ALLOWED_HOSTS` in `backend/.env`.
3. Add `http://192.168.1.50:5173` to `CORS_ALLOWED_ORIGINS`.
4. Change `frontend/.env`:

```env
VITE_API_BASE_URL=http://192.168.1.50:8000/api
```

5. Allow inbound Windows Firewall access for ports 5173 and 8000 on the private network.
6. Restart both servers and open `http://192.168.1.50:5173` from the device.

## Troubleshooting

### `Data source name not found` or ODBC error
Install Microsoft ODBC Driver 18 x64 and confirm the exact driver name in Windows ODBC Data Sources.

### Login timeout or server not found
Check the SQL Server service, instance name, TCP/IP setting, port, and Windows Firewall.

### Certificate error
For local development, keep `DB_TRUST_CERTIFICATE=yes`. Do not use this shortcut for an internet-facing production server.

### CORS error
Confirm the frontend origin exactly matches one entry in `CORS_ALLOWED_ORIGINS`, including protocol and port.

### PowerShell cannot find Python 3.12
Reinstall Python 3.12 with the launcher and PATH options, then verify:

```powershell
py -3.12 --version
```

### Quick demo without SQL Server
Run:

```powershell
.\run-sqlite-demo.ps1
```

This is for evaluation only. Real local operation should use SQL Server and a tested backup plan.
