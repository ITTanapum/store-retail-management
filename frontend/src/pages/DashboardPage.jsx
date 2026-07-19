import { useEffect, useState } from "react";
import { AlertTriangle, Boxes, CircleDollarSign, ShoppingBasket, Warehouse } from "lucide-react";
import api, { errorMessage } from "../api";
import DataTable from "../components/DataTable";
import MetricCard from "../components/MetricCard";
import PageHeader from "../components/PageHeader";
import StatusMessage from "../components/StatusMessage";

const money = new Intl.NumberFormat("th-TH", { style: "currency", currency: "THB" });

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/dashboard/summary/")
      .then((response) => setData(response.data))
      .catch((err) => setError(errorMessage(err)));
  }, []);

  return (
    <section>
      <PageHeader title="Retail Overview" subtitle="Live operational health across inventory, sales, and checkout." />
      <StatusMessage message={error} type="error" />
      <div className="metric-grid">
        <MetricCard icon={Boxes} label="Active Products" value={data?.product_count ?? "—"} hint="SKU catalogue" />
        <MetricCard icon={AlertTriangle} label="Low Stock Alerts" value={data?.low_stock_count ?? "—"} hint="At or below safety stock" tone="red" />
        <MetricCard icon={CircleDollarSign} label="Sales Today" value={data ? money.format(data.sales_today) : "—"} hint="Confirmed checkout" tone="gold" />
        <MetricCard icon={ShoppingBasket} label="Open Baskets" value={data?.open_baskets ?? "—"} hint="Waiting for checkout" tone="blue" />
        <MetricCard icon={Warehouse} label="Base Stock Units" value={data?.stock_quantity_base ?? "—"} hint="Across all warehouses" tone="purple" />
      </div>

      <div className="dashboard-grid">
        <article className="panel">
          <div className="panel-heading"><div><h2>Priority stock alerts</h2><p>Replenish these items first.</p></div><span className="alert-badge">Action required</span></div>
          <DataTable
            rows={data?.low_stock_items || []}
            columns={[
              { key: "sku", label: "SKU" },
              { key: "product_name", label: "Product" },
              { key: "warehouse_code", label: "Location" },
              { key: "quantity_base", label: "Current" },
              { key: "safety_stock", label: "Safety" },
            ]}
            empty="No low-stock items."
          />
        </article>
        <article className="panel">
          <div className="panel-heading"><div><h2>Recent stock activity</h2><p>Latest posted inventory movements.</p></div></div>
          <div className="activity-list">
            {(data?.recent_transactions || []).map((row) => (
              <div className="activity-item" key={row.id}>
                <div className={`activity-dot ${Number(row.quantity_base) >= 0 ? "in" : "out"}`} />
                <div><strong>{row.product_name}</strong><span>{row.transaction_type.replaceAll("_", " ")} · {row.reference_no}</span></div>
                <b>{Number(row.quantity_base) > 0 ? "+" : ""}{row.quantity_base}</b>
              </div>
            ))}
            {!data?.recent_transactions?.length && <p className="empty-note">No posted transactions yet.</p>}
          </div>
        </article>
      </div>
    </section>
  );
}
