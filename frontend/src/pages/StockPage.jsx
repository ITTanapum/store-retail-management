import { useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";
import useApiList from "../useApiList";

export default function StockPage() {
  const { rows, loading, error, reload } = useApiList("/stock-balances/?page_size=500");
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => rows.filter((row) => `${row.sku} ${row.product_name} ${row.warehouse_code}`.toLowerCase().includes(query.toLowerCase())), [rows, query]);

  return (
    <section>
      <PageHeader title="Current Stock Status" subtitle="Quantities are shown in each product's base unit." actions={<button className="secondary-button" onClick={reload}>Refresh</button>} />
      <div className="toolbar"><input className="search-input" placeholder="Search SKU, product, warehouse..." value={query} onChange={(event) => setQuery(event.target.value)} /></div>
      <StatusMessage message={error} type="error" />
      <article className="panel">
        <DataTable
          rows={filtered}
          empty={loading ? "Loading stock..." : "No stock balances found. Post a goods receipt to add stock."}
          columns={[
            { key: "sku", label: "SKU" },
            { key: "product_name", label: "Product" },
            { key: "warehouse_code", label: "Warehouse" },
            { key: "quantity_base", label: "Current Qty" },
            { key: "safety_stock", label: "Safety Qty" },
            { key: "is_low_stock", label: "Status", render: (row) => <span className={`status-pill ${row.is_low_stock ? "danger" : "success"}`}>{row.is_low_stock ? "Low stock" : "Healthy"}</span> },
          ]}
        />
      </article>
    </section>
  );
}
