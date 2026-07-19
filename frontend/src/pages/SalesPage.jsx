import { useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";
import useApiList from "../useApiList";

const money = new Intl.NumberFormat("th-TH", { style: "currency", currency: "THB" });

export default function SalesPage() {
  const sales = useApiList("/sales/?page_size=500");
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => sales.rows.filter((row) => `${row.sale_no} ${row.basket_no} ${row.customer_name} ${row.cashier_name}`.toLowerCase().includes(query.toLowerCase())), [sales.rows, query]);
  const total = filtered.reduce((sum, row) => sum + Number(row.grand_total), 0);

  return (
    <section>
      <PageHeader title="Sales History" subtitle="Confirmed checkout records with customer, cashier, discounts, and final value." actions={<div className="header-total"><span>Visible sales</span><strong>{money.format(total)}</strong></div>} />
      <div className="toolbar"><input className="search-input" placeholder="Search sale, basket, customer or cashier..." value={query} onChange={(event) => setQuery(event.target.value)} /></div>
      <StatusMessage message={sales.error} type="error" />
      <article className="panel">
        <DataTable rows={filtered} empty={sales.loading ? "Loading sales..." : "No sales found."} columns={[
          { key: "sold_at", label: "Sold at", render: (row) => new Date(row.sold_at).toLocaleString("th-TH") },
          { key: "sale_no", label: "Sale No." },
          { key: "basket_no", label: "Basket" },
          { key: "customer_name", label: "Customer", render: (row) => row.customer_name || "Walk-in" },
          { key: "warehouse_name", label: "Warehouse" },
          { key: "subtotal", label: "Subtotal", render: (row) => money.format(row.subtotal) },
          { key: "discount_total", label: "Discount", render: (row) => money.format(row.discount_total) },
          { key: "grand_total", label: "Grand total", render: (row) => <strong>{money.format(row.grand_total)}</strong> },
          { key: "cashier_name", label: "Cashier" },
        ]} />
      </article>
    </section>
  );
}
