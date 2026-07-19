import { useMemo, useState } from "react";
import api, { errorMessage } from "../api";
import DataTable from "../components/DataTable";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";
import useApiList from "../useApiList";

const blank = { code: "", name: "", phone: "", email: "", tax_id: "", address: "" };

export default function PartnersPage() {
  const [tab, setTab] = useState("customers");
  const customers = useApiList("/customers/?page_size=500");
  const vendors = useApiList("/vendors/?page_size=500");
  const [form, setForm] = useState(blank);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const source = tab === "customers" ? customers : vendors;
  const filtered = useMemo(() => source.rows.filter((row) => `${row.code} ${row.name} ${row.phone} ${row.email}`.toLowerCase().includes(query.toLowerCase())), [source.rows, query]);
  const set = (name) => (event) => setForm((current) => ({ ...current, [name]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault(); setMessage(""); setError("");
    try {
      await api.post(`/${tab}/`, { ...form, is_active: true, ...(tab === "customers" ? { member_no: null } : { contact_name: "", payment_terms_days: 0 }) });
      setForm(blank); setMessage(`${tab === "customers" ? "Customer" : "Vendor"} created.`); source.reload();
    } catch (err) { setError(errorMessage(err)); }
  };

  return (
    <section>
      <PageHeader title="Customers & Vendors" subtitle="Centralized partner information for purchasing, sales, tax, and contact history." />
      <div className="segmented-control"><button className={tab === "customers" ? "active" : ""} onClick={() => { setTab("customers"); setForm(blank); }}>Customers</button><button className={tab === "vendors" ? "active" : ""} onClick={() => { setTab("vendors"); setForm(blank); }}>Vendors</button></div>
      <div className="split-layout">
        <form className="panel form-panel" onSubmit={submit}>
          <div className="panel-heading"><div><h2>Add {tab === "customers" ? "customer" : "vendor"}</h2><p>Required master data for retail transactions.</p></div></div>
          <StatusMessage message={message} type="success" /><StatusMessage message={error} type="error" />
          <div className="form-grid">
            <label>Code<input value={form.code} onChange={set("code")} required /></label>
            <label>Name<input value={form.name} onChange={set("name")} required /></label>
            <label>Phone<input value={form.phone} onChange={set("phone")} /></label>
            <label>Email<input type="email" value={form.email} onChange={set("email")} /></label>
            <label className="span-2">Tax ID<input value={form.tax_id} onChange={set("tax_id")} /></label>
            <label className="span-2">Address<textarea rows="4" value={form.address} onChange={set("address")} /></label>
          </div>
          <button className="primary-button">Create {tab === "customers" ? "customer" : "vendor"}</button>
        </form>
        <article className="panel wide-panel">
          <div className="panel-heading"><div><h2>{tab === "customers" ? "Customer" : "Vendor"} directory</h2><p>{source.rows.length} records</p></div></div>
          <input className="search-input" placeholder="Search code, name, phone or email..." value={query} onChange={(event) => setQuery(event.target.value)} />
          <DataTable rows={filtered} empty={source.loading ? "Loading..." : "No records found."} columns={[
            { key: "code", label: "Code" },
            { key: "name", label: "Name" },
            { key: "phone", label: "Phone" },
            { key: "email", label: "Email" },
            { key: "tax_id", label: "Tax ID" },
            { key: "is_active", label: "Status", render: (row) => <span className={`status-pill ${row.is_active ? "success" : "danger"}`}>{row.is_active ? "Active" : "Inactive"}</span> },
          ]} />
        </article>
      </div>
    </section>
  );
}
