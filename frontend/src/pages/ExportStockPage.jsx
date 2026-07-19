import { useState } from "react";
import api, { errorMessage } from "../api";
import DataTable from "../components/DataTable";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";
import useApiList from "../useApiList";

const initial = { issue_type: "SALE", source_warehouse: "", target_warehouse: "", customer: "", product_package: "", package_quantity: "1", unit_price: "0", reason: "" };

export default function ExportStockPage() {
  const warehouses = useApiList("/warehouses/?page_size=500");
  const customers = useApiList("/customers/?page_size=500");
  const packages = useApiList("/product-packages/?page_size=500");
  const issues = useApiList("/stock-issues/?page_size=100");
  const [form, setForm] = useState(initial);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (name) => (event) => setForm((current) => ({ ...current, [name]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setMessage(""); setError("");
    try {
      const payload = {
        issue_type: form.issue_type,
        source_warehouse: Number(form.source_warehouse),
        target_warehouse: form.issue_type === "TRANSFER" ? Number(form.target_warehouse) : null,
        customer: form.issue_type === "SALE" && form.customer ? Number(form.customer) : null,
        reason: form.reason,
        lines: [{ product_package_id: Number(form.product_package), package_quantity: form.package_quantity, unit_price: form.unit_price }],
      };
      const response = await api.post("/stock-issues/", payload);
      await api.post(`/stock-issues/${response.data.id}/post_issue/`);
      setMessage(`${form.issue_type} ${response.data.issue_no} posted successfully.`);
      setForm(initial); issues.reload();
    } catch (err) { setError(errorMessage(err)); }
    finally { setBusy(false); }
  };

  return (
    <section>
      <PageHeader title="Export Stock" subtitle="Post sales, scrap, or warehouse transfers with negative-stock protection." />
      <div className="split-layout">
        <form className="panel form-panel" onSubmit={submit}>
          <div className="panel-heading"><div><h2>New stock issue</h2><p>Choose the reason and destination for the outgoing stock.</p></div></div>
          <StatusMessage message={message} type="success" /><StatusMessage message={error} type="error" />
          <div className="form-grid">
            <label>Issue type<select value={form.issue_type} onChange={set("issue_type")}><option value="SALE">Sale</option><option value="SCRAP">Scrap</option><option value="TRANSFER">Transfer</option></select></label>
            <label>Source warehouse<select value={form.source_warehouse} onChange={set("source_warehouse")} required><option value="">Select warehouse</option>{warehouses.rows.map((row) => <option key={row.id} value={row.id}>{row.code} · {row.name}</option>)}</select></label>
            {form.issue_type === "TRANSFER" && <label className="span-2">Target warehouse<select value={form.target_warehouse} onChange={set("target_warehouse")} required><option value="">Select target</option>{warehouses.rows.map((row) => <option key={row.id} value={row.id}>{row.code} · {row.name}</option>)}</select></label>}
            {form.issue_type === "SALE" && <label className="span-2">Customer<select value={form.customer} onChange={set("customer")}><option value="">Walk-in / no customer</option>{customers.rows.map((row) => <option key={row.id} value={row.id}>{row.code} · {row.name}</option>)}</select></label>}
            <label className="span-2">Product package<select value={form.product_package} onChange={set("product_package")} required><option value="">Select SKU and package</option>{packages.rows.map((row) => <option key={row.id} value={row.id}>{row.product_sku} · {row.product_name} · {row.package_type}</option>)}</select></label>
            <label>Package quantity<input type="number" step="0.001" min="0.001" value={form.package_quantity} onChange={set("package_quantity")} required /></label>
            <label>Price / package<input type="number" step="0.01" min="0" value={form.unit_price} onChange={set("unit_price")} required /></label>
            <label className="span-2">Reason / notes<textarea value={form.reason} onChange={set("reason")} rows="3" /></label>
          </div>
          <button className="primary-button danger-action" disabled={busy}>{busy ? "Posting..." : "Post stock issue"}</button>
        </form>
        <article className="panel wide-panel">
          <div className="panel-heading"><div><h2>Recent stock issues</h2><p>Sale, scrap, and transfer documents.</p></div></div>
          <DataTable rows={issues.rows} empty={issues.loading ? "Loading issues..." : "No stock issues yet."} columns={[
            { key: "issue_no", label: "Issue" },
            { key: "issued_at", label: "Date", render: (row) => new Date(row.issued_at).toLocaleString("th-TH") },
            { key: "issue_type", label: "Type" },
            { key: "source_warehouse_name", label: "From" },
            { key: "target_warehouse_name", label: "To" },
            { key: "total_amount", label: "Amount" },
            { key: "status", label: "Status", render: (row) => <span className={`status-pill ${row.status === "POSTED" ? "success" : "warning"}`}>{row.status}</span> },
          ]} />
        </article>
      </div>
    </section>
  );
}
