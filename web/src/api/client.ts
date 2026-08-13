/**
 * REST API client for the trading system backend.
 */
import { API_BASE } from '../utils/constants';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  getStatus:           ()              => request<any>('/api/status'),
  getStocks:           ()              => request<any>('/api/stocks'),
  getStockDetail:      (symbol: string) => request<any>(`/api/stocks/${encodeURIComponent(symbol)}`),
  getTrades:           ()              => request<any>('/api/trades'),
  getTradeStats:       ()              => request<any>('/api/trades/stats'),
  getModels:           ()              => request<any>('/api/models'),
  getFeatureImportance:()              => request<any>('/api/models/importance'),
  getThresholdAnalysis:()              => request<any>('/api/models/threshold'),
  getConfig:           ()              => request<any>('/api/config'),
  getSnapshot:         ()              => request<any>('/api/snapshot'),
  retrainModels:       ()              => request<any>('/api/models/retrain', { method: 'POST' }),

  // B2C Consumer Endpoints
  executeTrade:        (payload: any)  => request<any>('/api/execute', { method: 'POST', body: JSON.stringify(payload) }),
  closeTrade:          (tradeId: number) => request<any>(`/api/trades/${tradeId}/close`, { method: 'POST' }),
  searchStocks:        (query: string) => request<any>(`/api/search?q=${encodeURIComponent(query)}`),
  getPortfolio:        ()              => request<any>('/api/portfolio'),
  getWatchlist:        ()              => request<any>('/api/watchlist'),
  addToWatchlist:      (symbol: string) => request<any>(`/api/watchlist/${symbol}`, { method: 'POST' }),
  removeFromWatchlist: (symbol: string) => request<any>(`/api/watchlist/${symbol}`, { method: 'DELETE' }),
};
