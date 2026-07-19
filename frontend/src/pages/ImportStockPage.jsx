import { useMemo, useState } from "react";
import api, { errorMessage } from "../api";
import DataTable from "../components/DataTable";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";
import useApiList from "../useApiList";

const initial = { vendor: "", warehouse: "", supplier_invoice_no: "", product_package: "", package_quantity: "1", unit_cost: "0", notes: "" };

export default function ImportStockPage() {
  const vendors = useApiList("/vendors/?page_size=500");
  const warehouses = useApiList("/warehouses/?page_size=500");
  const packages = useApiList("/product-packages/?page_size=500");
  const receipts = useApiList("/goods-receipts/?page_size=100");
  const [form, setForm] = useState(initial);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const selectedPackage = useMemo(() => packages.rows.find((row) => row.id === Number(form.product_package)), [packages.rows, form.product_package]);
  const set = (name) => (event) => setForm((current) => ({ ...current, [name]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault(); setBusy(true); setMessage(""); setError("");
    try {
      const response = await api.post("/goods-receipts/", {
        vendor: Number(form.vendor),
        warehouse: Number(form.warehouse),
        supplier_invoice_no: form.supplier_invoice_no,
        notes: form.notes,
        lines: [{ product_package_id: Number(form.product_package), package_quantity: form.package_quantity, unit_cost: form.unit_cost }],
      });
      await api.post(`/goods-receipts/${response.data.id}/post_receipt/`);
      setMessage(`Receipt ${response.data.receipt_no} posted. Stock is now available.`);
      setForm(initial); receipts.reload();
    } catch (err) { setError(errorMessage(err)); }
    finally { setBusy(false); }
  };

  return (
    <section>
      <PageHeader title="Import Stock" subtitle="Receive goods from a vendor and immediately post them into the selected warehouse." />
      <div className="split-layout">
        <form className="panel form-panel" onSubmit={submit}>
          <div className="panel-heading"><div><h2>New goods receipt</h2><p>One-line quick receive for fast daily operation.</p></div></div>
          <StatusMessage message={message} type="success" /><StatusMessage message={error} type="error" />
          <div className="form-grid">
            <label>Vendor<select value={form.vendor} onChange={set("vendor")} required><option value="">Select vendor</option>{vendors.rows.map((row) => <option key={row.id} value={row.id}>{row.code} · {row.name}</option>)}</select></label>
            <label>Warehouse<select value={form.warehouse} onChange={set("warehouse")} required><option value="">Select warehouse</option>{warehouses.rows.map((row) => <option key={row.id} value={row.id}>{row.code} · {row.name}</option>)}</select></label>
            <label className="span-2">Supplier invoice<input value={form.supplier_invoice_no} onChange={set("supplier_invoice_no")} /></label>
            <label className="span-2">Product package<select value={form.product_package} onChange={set("product_package")} required><option value="">Select SKU and package</option>{packages.rows.map((row) => <option key={row.id} value={row.id}>{row.product_sku} · {row.product_name} · {row.package_type}</option>)}</select></label>
            <label>Package quantity<input type="number" step="0.001" min="0.001" value={form.package_quantity} onChange={set("package_quantity")} required /></label>
            <label>Cost / package<input type="number" step="0.01" min="0" value={form.unit_cost} onChange={set("unit_cost")} required /></label>
            <label className="span-2">Notes<textarea value={form.notes} onChange={set("notes")} rows="3" /></label>
          </div>
          {selectedPackage && <div className="calculation-strip"><span>Base quantity added</span><strong>{Number(form.package_quantity || 0) * Number(selectedPackage.units_per_package)} {selectedPackage.product_sku} base units</strong></div>}
          <button className="primary-button" disabled={busy}>{busy ? "Posting..." : "Receive and post stock"}</button>
        </form>
        <article className="panel wide-panel">
          <div className="panel-heading"><div><h2>Recent receipts</h2><p>Posted and draft vendor deliveries.</p></div></div>
          <DataTable rows={receipts.rows} empty={receipts.loading ? "Loading receipts..." : "No receipts yet."} columns={[
            { key: "receipt_no", label: "Receipt" },
            { key: "received_at", label: "Date", render: (row) => new Date(row.received_at).toLocaleString("th-TH") },
            { key: "vendor_name", label: "Vendor" },
            { key: "warehouse_name", label: "Warehouse" },
            { key: "total_cost", label: "Total" },
            { key: "status", label: "Status", render: (row) => <span className={`status-pill ${row.status === "POSTED" ? "success" : "warning"}`}>{row.status}</span> },
          ]} />
        </article>
      </div>
    </section>
  );
}
