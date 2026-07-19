export default function MetricCard({ icon: Icon, label, value, hint, tone = "green" }) {
  return (
    <article className={`metric-card ${tone}`}>
      <div className="metric-icon"><Icon size={22} /></div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        {hint && <span>{hint}</span>}
      </div>
    </article>
  );
}
