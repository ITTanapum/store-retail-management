import { useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";
import useApiList from "../useApiList";

export default function TransactionsPage() {
  const { rows, loading, error, reload } = useApiList("/stock-transactions/?page_size=500");
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => rows.filter((row) => `${row.reference_no} ${row.sku} ${row.product_name} ${row.transaction_type}`.toLowerCase().includes(query.toLowerCase())), [rows, query]);

  return (
    <section>
      <PageHeader title="Stock Ledger" subtitle="Immutable history of every posted stock movement." actions={<button className="secondary-button" onClick={reload}>Refresh</button>} />
      <div className="toolbar"><input className="search-input" placeholder="Search reference, SKU or transaction type..." value={query} onChange={(event) => setQuery(event.target.value)} /></div>
      <StatusMessage message={error} type="error" />
      <article className="panel">
        <DataTable
          rows={filtered}
          empty={loading ? "Loading transactions..." : "No stock transactions found."}
          columns={[
            { key: "occurred_at", label: "Date", render: (row) => new Date(row.occurred_at).toLocaleString("th-TH") },
            { key: "reference_no", label: "Reference" },
            { key: "transaction_type", label: "Type", render: (row) => row.transaction_type.replaceAll("_", " ") },
            { key: "sku", label: "SKU" },
            { key: "product_name", label: "Product" },
            { key: "warehouse_code", label: "Warehouse" },
            { key: "quantity_base", label: "Qty", render: (row) => <b className={Number(row.quantity_base) >= 0 ? "positive" : "negative"}>{Number(row.quantity_base) > 0 ? "+" : ""}{row.quantity_base}</b> },
            { key: "performed_by_name", label: "By" },
          ]}
        />
      </article>
    </section>
  );
}
