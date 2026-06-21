import axios from "axios";


export const apiClient = axios.create({
  baseURL: "/api/backend",
  withCredentials: true,
});


export function unwrapList<T>(payload: T[] | { results?: T[] }) {
  return Array.isArray(payload) ? payload : payload.results ?? [];
}
