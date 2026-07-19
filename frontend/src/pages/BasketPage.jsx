import { useEffect, useMemo, useState } from "react";
import api, { errorMessage, listData } from "../api";
import DataTable from "../components/DataTable";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";
import useApiList from "../useApiList";

const money = new Intl.NumberFormat("th-TH", { style: "currency", currency: "THB" });

export default function BasketPage() {
  const warehouses = useApiList("/warehouses/?page_size=500");
  const customers = useApiList("/customers/?page_size=500");
  const packages = useApiList("/product-packages/?page_size=500");
  const [basket, setBasket] = useState(null);
  const [openBaskets, setOpenBaskets] = useState([]);
  const [warehouse, setWarehouse] = useState("");
  const [customer, setCustomer] = useState("");
  const [packageId, setPackageId] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [unitPrice, setUnitPrice] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const selectedPackage = useMemo(() => packages.rows.find((row) => row.id === Number(packageId)), [packages.rows, packageId]);

  const loadOpen = async () => {
    try {
      const response = await api.get("/baskets/?status=OPEN&page_size=100");
      setOpenBaskets(listData(response).filter((row) => row.status === "OPEN"));
    } catch (err) { setError(errorMessage(err)); }
  };

  useEffect(() => { loadOpen(); }, []);
  useEffect(() => {
    if (selectedPackage) setUnitPrice(selectedPackage.default_selling_price);
  }, [selectedPackage]);

  const createBasket = async () => {
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await api.post("/baskets/", {
        warehouse: Number(warehouse),
        customer: customer ? Number(customer) : null,
      });
      setBasket(response.data);
      setMessage(`Basket ${response.data.basket_no} created.`);
      loadOpen();
    } catch (err) { setError(errorMessage(err)); }
    finally { setBusy(false); }
  };

  const openBasket = async (id) => {
    try {
      const response = await api.get(`/baskets/${id}/`);
      setBasket(response.data);
      setWarehouse(String(response.data.warehouse));
      setCustomer(response.data.customer ? String(response.data.customer) : "");
      setMessage(""); setError("");
    } catch (err) { setError(errorMessage(err)); }
  };

  const addItem = async (event) => {
    event.preventDefault();
    if (!basket) return;
    setBusy(true); setMessage(""); setError("");
    try {
      const response = await api.post(`/baskets/${basket.id}/add_item/`, {
        product_package_id: Number(packageId),
        package_quantity: quantity,
        unit_price: unitPrice,
      });
      setBasket(response.data);
      setPackageId(""); setQuantity("1"); setUnitPrice("");
    } catch (err) { setError(errorMessage(err)); }
    finally { setBusy(false); }
  };

  const removeItem = async (itemId) => {
    try {
      const response = await api.post(`/baskets/${basket.id}/remove_item/`, { item_id: itemId });
      setBasket(response.data);
    } catch (err) { setError(errorMessage(err)); }
  };

  const checkout = async () => {
    setBusy(true); setMessage(""); setError("");
    try {
      const response = await api.post(`/baskets/${basket.id}/checkout/`);
      setMessage(`Sale ${response.data.sale_no} completed for ${money.format(response.data.grand_total)}.`);
      setBasket(null);
      loadOpen();
    } catch (err) { setError(errorMessage(err)); }
    finally { setBusy(false); }
  };

  return (
    <section>
      <PageHeader title="Basket / Point of Sale" subtitle="Create an open basket, add package quantities, apply the best valid promotion, and checkout." />
      <StatusMessage message={message} type="success" /><StatusMessage message={error} type="error" />
      <div className="basket-layout">
        <aside className="panel basket-sidebar">
          <div className="panel-heading"><div><h2>Open baskets</h2><p>Resume a saved cart.</p></div></div>
          <div className="open-basket-list">
            {openBaskets.map((row) => (
              <button key={row.id} className={basket?.id === row.id ? "selected" : ""} onClick={() => openBasket(row.id)}>
                <strong>{row.basket_no}</strong><span>{row.customer_name || "Walk-in"}</span><b>{money.format(row.grand_total)}</b>
              </button>
            ))}
            {!openBaskets.length && <p className="empty-note">No open baskets.</p>}
          </div>
        </aside>

        <div className="basket-main">
          {!basket ? (
            <article className="panel create-basket-card">
              <div className="panel-heading"><div><h2>Start a new basket</h2><p>Select the selling warehouse and optional customer.</p></div></div>
              <div className="form-grid">
                <label>Warehouse<select value={warehouse} onChange={(event) => setWarehouse(event.target.value)} required><option value="">Select warehouse</option>{warehouses.rows.map((row) => <option key={row.id} value={row.id}>{row.code} · {row.name}</option>)}</select></label>
                <label>Customer<select value={customer} onChange={(event) => setCustomer(event.target.value)}><option value="">Walk-in customer</option>{customers.rows.map((row) => <option key={row.id} value={row.id}>{row.code} · {row.name}</option>)}</select></label>
              </div>
              <button className="primary-button" onClick={createBasket} disabled={!warehouse || busy}>Create basket</button>
            </article>
          ) : (
            <article className="panel">
              <div className="panel-heading basket-heading"><div><h2>{basket.basket_no}</h2><p>{basket.customer_name || "Walk-in customer"} · {basket.warehouse_name}</p></div><span className="status-pill warning">OPEN</span></div>
              <form className="basket-add-form" onSubmit={addItem}>
                <label>Product package<select value={packageId} onChange={(event) => setPackageId(event.target.value)} required><option value="">Scan or select product</option>{packages.rows.map((row) => <option key={row.id} value={row.id}>{row.product_sku} · {row.product_name} · {row.package_type}</option>)}</select></label>
                <label>Quantity<input type="number" step="0.001" min="0.001" value={quantity} onChange={(event) => setQuantity(event.target.value)} required /></label>
                <label>Price<input type="number" step="0.01" min="0" value={unitPrice} onChange={(event) => setUnitPrice(event.target.value)} required /></label>
                <button className="primary-button" disabled={busy}>Add item</button>
              </form>
              <DataTable rows={basket.items || []} empty="Basket is empty." columns={[
                { key: "sku", label: "SKU" },
                { key: "product_name", label: "Product" },
                { key: "package_type", label: "Package" },
                { key: "package_quantity", label: "Qty" },
                { key: "unit_price", label: "Price" },
                { key: "promotion_name", label: "Promotion", render: (row) => row.promotion_name || "—" },
                { key: "discount_amount", label: "Discount" },
                { key: "line_total", label: "Total" },
                { key: "action", label: "", render: (row) => <button className="icon-text-button danger" onClick={() => removeItem(row.id)}>Remove</button> },
              ]} />
              <div className="checkout-summary">
                <div><span>Subtotal</span><strong>{money.format(basket.subtotal)}</strong></div>
                <div><span>Discount</span><strong>-{money.format(basket.discount_total)}</strong></div>
                <div className="grand"><span>Grand total</span><strong>{money.format(basket.grand_total)}</strong></div>
                <button className="primary-button checkout-button" onClick={checkout} disabled={!basket.items?.length || busy}>{busy ? "Processing..." : "Confirm sale & checkout"}</button>
              </div>
            </article>
          )}
        </div>
      </div>
    </section>
  );
}
