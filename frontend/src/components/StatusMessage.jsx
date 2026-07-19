export default function StatusMessage({ message, type = "info" }) {
  if (!message) return null;
  return <div className={`status-message ${type}`}>{message}</div>;
}
