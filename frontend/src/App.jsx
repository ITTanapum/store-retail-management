import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import Layout from "./components/Layout";
import BasketPage from "./pages/BasketPage";
import DashboardPage from "./pages/DashboardPage";
import ExportStockPage from "./pages/ExportStockPage";
import ImportStockPage from "./pages/ImportStockPage";
import LoginPage from "./pages/LoginPage";
import PartnersPage from "./pages/PartnersPage";
import ProductsPage from "./pages/ProductsPage";
import PromotionsPage from "./pages/PromotionsPage";
import SalesPage from "./pages/SalesPage";
import StockPage from "./pages/StockPage";
import TransactionsPage from "./pages/TransactionsPage";
import UsersPage from "./pages/UsersPage";

function ProtectedLayout() {
  const { user, loading } = useAuth();
  if (loading) return <div className="app-loader">Loading FreshFlow...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Layout />;
}

export default function App() {
  const { user, loading } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={loading ? <div className="app-loader">Loading...</div> : user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route element={<ProtectedLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="products" element={<ProductsPage />} />
        <Route path="stock" element={<StockPage />} />
        <Route path="import-stock" element={<ImportStockPage />} />
        <Route path="export-stock" element={<ExportStockPage />} />
        <Route path="basket" element={<BasketPage />} />
        <Route path="partners" element={<PartnersPage />} />
        <Route path="promotions" element={<PromotionsPage />} />
        <Route path="sales" element={<SalesPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="users" element={<UsersPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
