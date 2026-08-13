import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useStore } from './stores/useStore';
import { wsClient } from './api/websocket';
import { Toaster, toast } from 'sonner';
import { Tooltip } from 'react-tooltip';
import 'react-tooltip/dist/react-tooltip.css';
import Layout from './components/layout/Layout';
import Explore from './pages/Explore';
import StockDetail from './pages/StockDetail';
import Investments from './pages/Investments';
import Watchlist from './pages/Watchlist';
import ProMarketData from './pages/ProMarketData';
import ProTradeLogs from './pages/ProTradeLogs';
import ModelLab from './pages/ModelLab';
import Settings from './pages/Settings';

export default function App() {
  const { fetchInitialData, handleWsMessage, setWsConnected } = useStore();

  useEffect(() => {
    // Fetch initial data from REST API
    fetchInitialData();

    // Connect WebSocket for real-time updates
    wsClient.connect();
    
    let isInitialConnection = true;
    const unsub = wsClient.subscribe((data) => {
      handleWsMessage(data);
      if (isInitialConnection) {
        toast.success('Connected to Live Data feed', {
          style: { background: 'var(--bg-surface)', border: '1px solid var(--border-default)', color: 'var(--text-primary)' },
        });
        isInitialConnection = false;
      }
      setWsConnected(true);
    });

    // Check connection status periodically
    const statusInterval = setInterval(() => {
      setWsConnected(wsClient.connected);
    }, 3000);

    return () => {
      unsub();
      wsClient.disconnect();
      clearInterval(statusInterval);
    };
  }, []);

  return (
    <BrowserRouter>
      <Toaster position="bottom-right" theme="dark" closeButton />
      <Tooltip 
        id="app-tooltip" 
        style={{ 
          backgroundColor: 'var(--bg-elevated)', 
          color: 'var(--text-primary)', 
          borderRadius: '8px', 
          border: '1px solid var(--border-default)',
          fontSize: '12px',
          padding: '8px 12px',
          boxShadow: 'var(--shadow-md)',
          zIndex: 9999
        }} 
      />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Explore />} />
          <Route path="/stock/:symbol" element={<StockDetail />} />
          <Route path="/investments" element={<Investments />} />
          <Route path="/watchlist" element={<Watchlist />} />
          
          <Route path="/pro/market" element={<ProMarketData />} />
          <Route path="/pro/logs" element={<ProTradeLogs />} />
          <Route path="/models" element={<ModelLab />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
