import { useMemo, useState } from "react";
import api, { errorMessage } from "../api";
import { useAuth } from "../auth";
import DataTable from "../components/DataTable";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";
import useApiList from "../useApiList";

const initial = { username: "", first_name: "", last_name: "", email: "", password: "", group: "", is_staff: false };

export default function UsersPage() {
  const { user } = useAuth();
  const users = useApiList("/users/?page_size=500");
  const groups = useApiList("/groups/?page_size=100");
  const [form, setForm] = useState(initial);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const isAdmin = user?.is_superuser || user?.roles?.includes("Admin");
  const filtered = useMemo(() => users.rows.filter((row) => `${row.username} ${row.first_name} ${row.last_name} ${row.email} ${row.groups}`.toLowerCase().includes(query.toLowerCase())), [users.rows, query]);
  const set = (name) => (event) => setForm((current) => ({ ...current, [name]: event.target.type === "checkbox" ? event.target.checked : event.target.value }));

  const submit = async (event) => {
    event.preventDefault(); setMessage(""); setError("");
    try {
      await api.post("/users/", {
        username: form.username,
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        password: form.password,
        group_ids: [Number(form.group)],
        is_active: true,
        is_staff: form.is_staff,
      });
      setForm(initial); setMessage("User account created."); users.reload();
    } catch (err) { setError(errorMessage(err)); }
  };

  if (!isAdmin) {
    return <section><PageHeader title="Users & Permission" subtitle="Only Admin users can manage accounts and role assignment." /><StatusMessage message="You do not have permission to access this page." type="error" /></section>;
  }

  return (
    <section>
      <PageHeader title="Users & Permission" subtitle="Role groups control access to master data, stock posting, checkout, and administration." />
      <div className="split-layout">
        <form className="panel form-panel" onSubmit={submit}>
          <div className="panel-heading"><div><h2>Create user</h2><p>Assign one primary operational role.</p></div></div>
          <StatusMessage message={message} type="success" /><StatusMessage message={error} type="error" />
          <div className="form-grid">
            <label>Username<input value={form.username} onChange={set("username")} required /></label>
            <label>Password<input type="password" minLength="8" value={form.password} onChange={set("password")} required /></label>
            <label>First name<input value={form.first_name} onChange={set("first_name")} /></label>
            <label>Last name<input value={form.last_name} onChange={set("last_name")} /></label>
            <label className="span-2">Email<input type="email" value={form.email} onChange={set("email")} /></label>
            <label>Role<select value={form.group} onChange={set("group")} required><option value="">Select role</option>{groups.rows.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
            <label className="checkbox-label"><input type="checkbox" checked={form.is_staff} onChange={set("is_staff")} />Allow Django Admin access</label>
          </div>
          <button className="primary-button">Create user</button>
        </form>
        <article className="panel wide-panel">
          <div className="panel-heading"><div><h2>User directory</h2><p>{users.rows.length} accounts</p></div></div>
          <input className="search-input" placeholder="Search user or role..." value={query} onChange={(event) => setQuery(event.target.value)} />
          <DataTable rows={filtered} empty={users.loading ? "Loading users..." : "No users found."} columns={[
            { key: "username", label: "Username" },
            { key: "first_name", label: "First name" },
            { key: "last_name", label: "Last name" },
            { key: "email", label: "Email" },
            { key: "groups", label: "Roles", render: (row) => <div className="tag-list">{row.groups.map((name) => <span key={name}>{name}</span>)}</div> },
            { key: "is_active", label: "Status", render: (row) => <span className={`status-pill ${row.is_active ? "success" : "danger"}`}>{row.is_active ? "Active" : "Inactive"}</span> },
          ]} />
        </article>
      </div>
    </section>
  );
}
