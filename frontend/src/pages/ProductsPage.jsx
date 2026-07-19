import { useMemo, useState } from "react";
import api, { errorMessage } from "../api";
import DataTable from "../components/DataTable";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";
import useApiList from "../useApiList";

const initialForm = {
  sku: "",
  barcode: "",
  name: "",
  category: "",
  base_unit_name: "unit",
  safety_stock: "0",
  package_type: "UNIT",
  units_per_package: "1",
  purchase_price: "0",
  selling_price: "0",
};

const initialPackageForm = {
  product: "",
  package_type: "PACK",
  label: "Pack",
  barcode: "",
  units_per_package: "12",
  purchase_price: "0",
  selling_price: "0",
};

export default function ProductsPage() {
  const productsApi = useApiList("/products/?page_size=500");
  const categoriesApi = useApiList("/categories/?page_size=500");
  const [form, setForm] = useState(initialForm);
  const [packageForm, setPackageForm] = useState(initialPackageForm);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [packageMessage, setPackageMessage] = useState("");
  const [packageError, setPackageError] = useState("");
  const [busy, setBusy] = useState(false);

  const filtered = useMemo(
    () => productsApi.rows.filter((row) => `${row.sku} ${row.name} ${row.category_name}`.toLowerCase().includes(query.toLowerCase())),
    [productsApi.rows, query],
  );
  const set = (name) => (event) => setForm((current) => ({ ...current, [name]: event.target.value }));
  const setPackage = (name) => (event) => setPackageForm((current) => ({ ...current, [name]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true); setMessage(""); setError("");
    try {
      const productResponse = await api.post("/products/", {
        sku: form.sku,
        barcode: form.barcode || null,
        name: form.name,
        description: "",
        category: Number(form.category),
        base_unit_name: form.base_unit_name,
        safety_stock: form.safety_stock,
        track_expiry: false,
        is_active: true,
      });
      await api.post("/product-packages/", {
        product: productResponse.data.id,
        package_type: form.package_type,
        label: form.package_type.charAt(0) + form.package_type.slice(1).toLowerCase(),
        barcode: null,
        units_per_package: form.units_per_package,
        default_purchase_price: form.purchase_price,
        default_selling_price: form.selling_price,
        is_active: true,
      });
      setForm(initialForm);
      setMessage("Product and initial package were created.");
      productsApi.reload();
    } catch (err) {
      setError(errorMessage(err));
    } finally { setBusy(false); }
  };

  const submitPackage = async (event) => {
    event.preventDefault();
    setBusy(true); setPackageMessage(""); setPackageError("");
    try {
      await api.post("/product-packages/", {
        product: Number(packageForm.product),
        package_type: packageForm.package_type,
        label: packageForm.label,
        barcode: packageForm.barcode || null,
        units_per_package: packageForm.units_per_package,
        default_purchase_price: packageForm.purchase_price,
        default_selling_price: packageForm.selling_price,
        is_active: true,
      });
      setPackageForm(initialPackageForm);
      setPackageMessage("Package conversion and prices were added.");
      productsApi.reload();
    } catch (err) {
      setPackageError(errorMessage(err));
    } finally { setBusy(false); }
  };

  return (
    <section>
      <PageHeader title="Products & SKU" subtitle="Define each item once, then configure unit, pack, pallet, and container conversions." />
      <div className="split-layout">
        <div className="stacked-column">
          <form className="panel form-panel" onSubmit={submit}>
            <div className="panel-heading"><div><h2>Add product</h2><p>Create an SKU with its first selling package.</p></div></div>
            <StatusMessage message={message} type="success" /><StatusMessage message={error} type="error" />
            <div className="form-grid">
              <label>SKU<input value={form.sku} onChange={set("sku")} required /></label>
              <label>Barcode<input value={form.barcode} onChange={set("barcode")} /></label>
              <label className="span-2">Product name<input value={form.name} onChange={set("name")} required /></label>
              <label>Category<select value={form.category} onChange={set("category")} required><option value="">Select category</option>{categoriesApi.rows.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
              <label>Base unit<input value={form.base_unit_name} onChange={set("base_unit_name")} required /></label>
              <label>Safety stock<input type="number" step="0.001" min="0" value={form.safety_stock} onChange={set("safety_stock")} required /></label>
              <label>Initial package<select value={form.package_type} onChange={set("package_type")}><option>UNIT</option><option>PACK</option><option>PALLET</option><option>CONTAINER</option></select></label>
              <label>Base units / package<input type="number" step="0.001" min="0.001" value={form.units_per_package} onChange={set("units_per_package")} required /></label>
              <label>Purchase price<input type="number" step="0.01" min="0" value={form.purchase_price} onChange={set("purchase_price")} required /></label>
              <label>Selling price<input type="number" step="0.01" min="0" value={form.selling_price} onChange={set("selling_price")} required /></label>
            </div>
            <button className="primary-button" disabled={busy}>{busy ? "Saving..." : "Create product"}</button>
          </form>

          <form className="panel form-panel" onSubmit={submitPackage}>
            <div className="panel-heading"><div><h2>Add package conversion</h2><p>Add the remaining pack, pallet, or container option to an existing SKU.</p></div></div>
            <StatusMessage message={packageMessage} type="success" /><StatusMessage message={packageError} type="error" />
            <div className="form-grid">
              <label className="span-2">Product<select value={packageForm.product} onChange={setPackage("product")} required><option value="">Select product</option>{productsApi.rows.map((row) => <option key={row.id} value={row.id}>{row.sku} · {row.name}</option>)}</select></label>
              <label>Package type<select value={packageForm.package_type} onChange={setPackage("package_type")}><option>UNIT</option><option>PACK</option><option>PALLET</option><option>CONTAINER</option></select></label>
              <label>Label<input value={packageForm.label} onChange={setPackage("label")} required /></label>
              <label>Package barcode<input value={packageForm.barcode} onChange={setPackage("barcode")} /></label>
              <label>Base units / package<input type="number" step="0.001" min="0.001" value={packageForm.units_per_package} onChange={setPackage("units_per_package")} required /></label>
              <label>Purchase price<input type="number" step="0.01" min="0" value={packageForm.purchase_price} onChange={setPackage("purchase_price")} required /></label>
              <label>Selling price<input type="number" step="0.01" min="0" value={packageForm.selling_price} onChange={setPackage("selling_price")} required /></label>
            </div>
            <button className="primary-button" disabled={busy}>{busy ? "Saving..." : "Add package"}</button>
          </form>
        </div>

        <article className="panel wide-panel">
          <div className="panel-heading"><div><h2>Product catalogue</h2><p>{productsApi.rows.length} active and inactive records</p></div></div>
          <input className="search-input" placeholder="Search SKU, name or category..." value={query} onChange={(event) => setQuery(event.target.value)} />
          <StatusMessage message={productsApi.error} type="error" />
          <DataTable
            rows={filtered}
            empty={productsApi.loading ? "Loading products..." : "No products found."}
            columns={[
              { key: "sku", label: "SKU" },
              { key: "name", label: "Product" },
              { key: "category_name", label: "Category" },
              { key: "current_stock", label: "Stock" },
              { key: "safety_stock", label: "Safety" },
              { key: "packages", label: "Packages", render: (row) => <div className="tag-list">{row.packages.map((pack) => <span key={pack.id}>{pack.package_type}: {pack.units_per_package}</span>)}</div> },
              { key: "is_low_stock", label: "Status", render: (row) => <span className={`status-pill ${row.is_low_stock ? "danger" : "success"}`}>{row.is_low_stock ? "Low" : "Healthy"}</span> },
            ]}
          />
        </article>
      </div>
    </section>
  );
}
