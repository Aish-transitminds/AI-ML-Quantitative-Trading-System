import { create } from 'zustand';
import { api } from '../api/client';

export interface AppState {
  // System State
  status: any;
  stocks: any[];
  qualifiedStocks: any[];
  totalStocks: number;
  wsConnected: boolean;

  // B2C State
  watchlist: string[];
  portfolio: any;
  searchResults: any[];
  
  // Market / AI Data
  trades: any[];
  tradeStats: any;
  modelResults: any;
  bestModel: string;
  datasetInfo: any;
  featureImportance: any[];
  thresholdAnalysis: any[];
  config: any;

  // Pro State
  isProMode: boolean;
  toggleProMode: () => void;

  // Actions
  fetchInitialData: () => Promise<void>;
  fetchStocks: () => Promise<void>;
  fetchModels: () => Promise<void>;
  fetchConfig: () => Promise<void>;
  fetchTrades: () => Promise<void>;
  
  // B2C Actions
  fetchWatchlist: () => Promise<void>;
  addToWatchlist: (symbol: string) => Promise<void>;
  removeFromWatchlist: (symbol: string) => Promise<void>;
  fetchPortfolio: () => Promise<void>;
  searchStocks: (query: string) => Promise<void>;

  // WebSocket
  handleWsMessage: (data: any) => void;
  setWsConnected: (connected: boolean) => void;
}

export const useStore = create<AppState>((set, get) => ({
  status: {},
  stocks: [],
  qualifiedStocks: [],
  totalStocks: 0,
  wsConnected: false,

  watchlist: [],
  portfolio: null,
  searchResults: [],

  isProMode: false,
  toggleProMode: () => set((state) => ({ isProMode: !state.isProMode })),

  trades: [],
  tradeStats: {},
  modelResults: {},
  bestModel: '',
  datasetInfo: {},
  featureImportance: [],
  thresholdAnalysis: [],
  config: {},

  fetchInitialData: async () => {
    try {
      const data = await api.getSnapshot();
      const stocksList = Object.values(data.stocks || {});
      set({
        status: data.status || {},
        stocks: stocksList,
        totalStocks: stocksList.length,
        qualifiedStocks: stocksList.filter((s: any) => s.passes_ltp_filter && s.passes_liquidity_filter),
        trades: data.trades || [],
        tradeStats: data.tradeStats || {},
        modelResults: data.model_results || {},
        featureImportance: data.feature_importance || [],
        thresholdAnalysis: data.threshold_analysis || [],
        datasetInfo: data.dataset_info || {},
        bestModel: data.best_model_name || '',
      });
      // Fetch B2C specific endpoints
      get().fetchWatchlist();
      get().fetchPortfolio();
    } catch (error) {
      console.error('Failed to fetch initial data:', error);
    }
  },

  fetchStocks: async () => {
    try {
      const data = await api.getStocks();
      set({
        stocks: data.stocks,
        totalStocks: data.total,
        qualifiedStocks: data.stocks.filter((s: any) => s.passes_ltp_filter && s.passes_liquidity_filter)
      });
    } catch (error) {
      console.error('Failed to fetch stocks:', error);
    }
  },

  fetchModels: async () => {
    try {
      const models = await api.getModels();
      set({
        modelResults: models.results,
        bestModel: models.best_model,
        datasetInfo: models.dataset_info
      });
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  },

  fetchConfig: async () => {
    try {
      const data = await api.getConfig();
      set({ config: data });
    } catch (error) {
      console.error('Failed to fetch config:', error);
    }
  },

  fetchTrades: async () => {
    try {
      const data = await api.getTrades();
      set({ trades: data.trades });
    } catch (error) {
      console.error('Failed to fetch trades:', error);
    }
  },

  fetchWatchlist: async () => {
    try {
      const data = await api.getWatchlist();
      set({ watchlist: data.watchlist || [] });
    } catch (error) {
      console.error('Failed to fetch watchlist:', error);
    }
  },

  addToWatchlist: async (symbol: string) => {
    try {
      await api.addToWatchlist(symbol);
      const { watchlist } = get();
      if (!watchlist.includes(symbol)) {
        set({ watchlist: [symbol, ...watchlist] });
      }
    } catch (error) {
      console.error('Failed to add to watchlist:', error);
    }
  },

  removeFromWatchlist: async (symbol: string) => {
    try {
      await api.removeFromWatchlist(symbol);
      set({ watchlist: get().watchlist.filter(s => s !== symbol) });
    } catch (error) {
      console.error('Failed to remove from watchlist:', error);
    }
  },

  fetchPortfolio: async () => {
    try {
      const data = await api.getPortfolio();
      set({ portfolio: data });
    } catch (error) {
      console.error('Failed to fetch portfolio:', error);
    }
  },

  searchStocks: async (query: string) => {
    if (!query.trim()) {
      set({ searchResults: [] });
      return;
    }
    try {
      const data = await api.searchStocks(query);
      set({ searchResults: data.results || [] });
    } catch (error) {
      console.error('Failed to search stocks:', error);
    }
  },

  handleWsMessage: (data: any) => {
    if (data.type === 'state_update') {
      set((state) => ({
        status: { ...state.status, ...data.status },
        stocks: data.stocks || state.stocks,
        tradeStats: data.trade_stats || state.tradeStats,
        bestModel: data.best_model || state.bestModel
      }));
    }
  },

  setWsConnected: (connected: boolean) => set({ wsConnected: connected }),
}));
