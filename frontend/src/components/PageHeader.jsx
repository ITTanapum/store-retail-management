export default function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="page-header">
      <div>
        <p className="eyebrow">Store operations</p>
        <h1>{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}
