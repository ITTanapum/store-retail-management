import { useMemo, useState } from "react";
import api, { errorMessage } from "../api";
import DataTable from "../components/DataTable";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";
import useApiList from "../useApiList";

function localDateTime(daysFromNow = 0) {
  const date = new Date(Date.now() + daysFromNow * 86400000);
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}

const initial = {
  code: "",
  name: "",
  promotion_type: "PERCENT",
  value: "5",
  minimum_quantity: "1",
  buy_quantity: "0",
  get_quantity: "0",
  start_at: localDateTime(0),
  end_at: localDateTime(30),
  products: [],
};

export default function PromotionsPage() {
  const promotions = useApiList("/promotions/?page_size=500");
  const products = useApiList("/products/?page_size=500");
  const [form, setForm] = useState(initial);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const filtered = useMemo(() => promotions.rows.filter((row) => `${row.code} ${row.name} ${row.promotion_type}`.toLowerCase().includes(query.toLowerCase())), [promotions.rows, query]);
  const set = (name) => (event) => setForm((current) => ({ ...current, [name]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault(); setMessage(""); setError("");
    try {
      await api.post("/promotions/", {
        ...form,
        value: form.value,
        minimum_quantity: form.minimum_quantity,
        buy_quantity: Number(form.buy_quantity || 0),
        get_quantity: Number(form.get_quantity || 0),
        start_at: new Date(form.start_at).toISOString(),
        end_at: new Date(form.end_at).toISOString(),
        products: form.products.map(Number),
        is_active: true,
      });
      setForm({ ...initial, start_at: localDateTime(0), end_at: localDateTime(30), products: [] });
      setMessage("Promotion created and ready for its active period.");
      promotions.reload();
    } catch (err) { setError(errorMessage(err)); }
  };

  return (
    <section>
      <PageHeader title="Discount Promotions" subtitle="Promotions are automatically evaluated at basket time; the largest valid discount is applied." />
      <div className="split-layout">
        <form className="panel form-panel" onSubmit={submit}>
          <div className="panel-heading"><div><h2>Create promotion</h2><p>Percentage, fixed discount, or buy-X-get-Y.</p></div></div>
          <StatusMessage message={message} type="success" /><StatusMessage message={error} type="error" />
          <div className="form-grid">
            <label>Code<input value={form.code} onChange={set("code")} required /></label>
            <label>Name<input value={form.name} onChange={set("name")} required /></label>
            <label>Type<select value={form.promotion_type} onChange={set("promotion_type")}><option value="PERCENT">Percentage</option><option value="FIXED">Fixed amount</option><option value="BUY_X_GET_Y">Buy X get Y</option></select></label>
            <label>Value<input type="number" step="0.01" min="0" value={form.value} onChange={set("value")} required /></label>
            <label>Minimum package qty<input type="number" step="0.001" min="0" value={form.minimum_quantity} onChange={set("minimum_quantity")} /></label>
            <label>Buy quantity<input type="number" min="0" value={form.buy_quantity} onChange={set("buy_quantity")} /></label>
            <label>Get quantity<input type="number" min="0" value={form.get_quantity} onChange={set("get_quantity")} /></label>
            <label>Start<input type="datetime-local" value={form.start_at} onChange={set("start_at")} required /></label>
            <label>End<input type="datetime-local" value={form.end_at} onChange={set("end_at")} required /></label>
            <label className="span-2">Products<select multiple value={form.products.map(String)} onChange={(event) => setForm((current) => ({ ...current, products: [...event.target.selectedOptions].map((option) => option.value) }))} required>{products.rows.map((row) => <option key={row.id} value={row.id}>{row.sku} · {row.name}</option>)}</select><small>Hold Ctrl to select multiple products.</small></label>
          </div>
          <button className="primary-button">Create promotion</button>
        </form>
        <article className="panel wide-panel">
          <div className="panel-heading"><div><h2>Promotion calendar</h2><p>{promotions.rows.length} configured promotions</p></div></div>
          <input className="search-input" placeholder="Search promotion..." value={query} onChange={(event) => setQuery(event.target.value)} />
          <DataTable rows={filtered} empty={promotions.loading ? "Loading promotions..." : "No promotions found."} columns={[
            { key: "code", label: "Code" },
            { key: "name", label: "Promotion" },
            { key: "promotion_type", label: "Type" },
            { key: "value", label: "Value" },
            { key: "start_at", label: "Start", render: (row) => new Date(row.start_at).toLocaleDateString("th-TH") },
            { key: "end_at", label: "End", render: (row) => new Date(row.end_at).toLocaleDateString("th-TH") },
            { key: "is_active", label: "Status", render: (row) => <span className={`status-pill ${row.is_active ? "success" : "danger"}`}>{row.is_active ? "Enabled" : "Disabled"}</span> },
          ]} />
        </article>
      </div>
    </section>
  );
}
