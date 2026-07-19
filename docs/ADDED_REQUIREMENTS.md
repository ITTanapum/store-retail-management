# Requirements Added to Complete the System

The original requirements were preserved. The following supporting requirements were added because they are needed for a reliable retail inventory workflow.

## Included in this MVP

1. **Warehouse and stock location** — required for transfers and multi-location stock.
2. **Package conversion factor** — converts unit, pack, pallet, and container into one base quantity.
3. **Inventory transaction ledger** — preserves every receipt, sale, scrap, transfer, and adjustment history.
4. **Draft/post document status** — prevents stock from changing while a user is still editing.
5. **Negative-stock prevention** — blocks checkout or issue when stock is insufficient.
6. **Automatic document numbers** — GRN, issue, basket, and sale references.
7. **User/time audit fields** — identifies who created and posted transactions.
8. **Multiple warehouses** — source and target are mandatory for transfers.
9. **Promotion date range and product assignment** — controls where and when discounts apply.
10. **Best-promotion calculation** — checkout applies the largest currently valid product discount.
11. **Atomic database operations** — balance and ledger changes succeed or fail together.
12. **JWT login and five default roles** — Admin, Manager, Inventory, Cashier, Viewer.
13. **Bangkok timezone** — transaction dates follow the local operating timezone.
14. **SQLite quick-demo mode** — lets the UI be demonstrated before SQL Server setup; SQL Server remains the real configuration.
15. **Responsive navigation and tables** — optimized for TV, desktop, notebook, tablet, and phone widths.

## Recommended next phases

These are not claimed as complete in the MVP and should be planned after the base workflow is accepted:

- Purchase orders and receiving against purchase orders
- Customer returns, refunds, and vendor returns
- Stock counting and approval-based adjustments
- Batch/lot, expiry date, and FEFO control
- Barcode scanner and label-printing workflow
- VAT, receipt/invoice printing, and payment methods
- Promotion stacking rules, coupons, member tiers, and usage limits
- Branch-level reporting, gross margin, COGS, and inventory valuation
- Scheduled SQL Server backups and restore testing
- Approval workflow for high-value scrap or stock adjustment
