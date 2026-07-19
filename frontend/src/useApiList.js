import { useCallback, useEffect, useState } from "react";
import api, { errorMessage, listData } from "./api";

export default function useApiList(url, dependencies = []) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get(url);
      setRows(listData(response));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [url, ...dependencies]);

  useEffect(() => { load(); }, [load]);
  return { rows, setRows, loading, error, reload: load };
}
