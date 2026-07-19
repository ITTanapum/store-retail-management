import { useState } from "react";
import { LockKeyhole, Store } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { errorMessage } from "../api";
import StatusMessage from "../components/StatusMessage";

export default function LoginPage() {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("Admin@12345");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await login(username, password);
      navigate("/");
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-visual">
        <div className="login-copy">
          <div className="login-logo"><Store size={30} /></div>
          <p className="eyebrow light">Retail operations, made clear</p>
          <h1>Track every item from receiving dock to checkout.</h1>
          <p>Responsive stock control, clear low-stock alerts, flexible package units, promotions, and permission-based workflows.</p>
          <div className="visual-pills">
            <span>Live stock ledger</span><span>Safety alerts</span><span>Fast POS</span>
          </div>
        </div>
      </div>
      <form className="login-card" onSubmit={submit}>
        <div className="login-card-icon"><LockKeyhole size={24} /></div>
        <h2>Welcome back</h2>
        <p>Sign in to your local retail management system.</p>
        <StatusMessage message={message} type="error" />
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
        </label>
        <button className="primary-button full" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
        <small>Demo default: admin / Admin@12345</small>
      </form>
    </div>
  );
}
