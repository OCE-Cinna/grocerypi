import axios from "axios";

// Kiosk API client: connects directly to local FastAPI backend
const api = axios.create({
  baseURL: "/",
  timeout: 10000,
});

export default api;
