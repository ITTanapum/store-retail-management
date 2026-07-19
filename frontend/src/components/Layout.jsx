import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  BadgePercent,
  Boxes,
  ClipboardList,
  Gauge,
  LogOut,
  Menu,
  PackageOpen,
  ReceiptText,
  ShoppingBasket,
  Store,
  Truck,
  Users,
  Warehouse,
  X,
} from "lucide-react";
import { useAuth } from "../auth";

const links = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/products", label: "Products & SKU", icon: Boxes },
  { to: "/stock", label: "Current Stock", icon: Warehouse },
  { to: "/import-stock", label: "Import Stock", icon: PackageOpen },
  { to: "/export-stock", label: "Export Stock", icon: Truck },
  { to: "/basket", label: "Basket / POS", icon: ShoppingBasket },
  { to: "/partners", label: "Customers & Vendors", icon: Store },
  { to: "/promotions", label: "Promotions", icon: BadgePercent },
  { to: "/sales", label: "Sales History", icon: ReceiptText },
  { to: "/transactions", label: "Stock Ledger", icon: ClipboardList },
  { to: "/users", label: "Users & Permission", icon: Users, adminOnly: true },
];

export default function Layout() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.is_superuser || user?.roles?.includes("Admin");

  const signOut = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <button className="mobile-menu-button" onClick={() => setOpen(true)} aria-label="Open navigation">
        <Menu size={22} />
      </button>
      {open && <button className="nav-overlay" onClick={() => setOpen(false)} aria-label="Close navigation overlay" />}
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="brand-row">
          <div className="brand-mark"><Store size={26} /></div>
          <div>
            <strong>FreshFlow</strong>
            <span>Retail Management</span>
          </div>
          <button className="sidebar-close" onClick={() => setOpen(false)} aria-label="Close navigation"><X size={20} /></button>
        </div>

        <nav>
          {links.filter((link) => !link.adminOnly || isAdmin).map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}
            >
              <Icon size={19} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-user">
          <div className="avatar">{user?.username?.slice(0, 1).toUpperCase()}</div>
          <div>
            <strong>{user?.first_name || user?.username}</strong>
            <span>{user?.roles?.join(", ") || "User"}</span>
          </div>
          <button onClick={signOut} title="Sign out"><LogOut size={18} /></button>
        </div>
      </aside>
      <main className="main-content"><Outlet /></main>
    </div>
  );
}
