import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useStore } from '../../stores/useStore';
import { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { formatPrice } from '../../utils/formatters';

export default function Layout() {
  const { wsConnected, searchStocks, searchResults, isProMode, toggleProMode } = useStore();
  const [query, setQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const location = useLocation();

  // Close search when location changes
  useEffect(() => {
    setShowSearch(false);
    setQuery('');
  }, [location]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setQuery(v);
    if (v.length > 0) {
      searchStocks(v);
      setShowSearch(true);
    } else {
      setShowSearch(false);
    }
  };

  return (
    <div className="app-layout" style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-void)' }}>
      {/* Groww Style Top Navigation */}
      <nav style={{ 
        height: '64px', 
        background: 'var(--bg-base)', 
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        gap: '40px'
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: 32, height: 32, borderRadius: '8px', background: 'var(--primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>Q</div>
          <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>QuantumGrow</span>
        </div>

        {/* Global Search */}
        <div style={{ flex: 1, maxWidth: '400px', position: 'relative' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            background: 'var(--bg-surface)', 
            border: '1px solid var(--border-default)',
            borderRadius: '8px',
            padding: '0 16px',
            height: '42px',
            transition: 'all 0.2s',
          }} className="search-bar-container">
            <Search size={18} color="var(--text-muted)" style={{ marginRight: '12px' }} />
            <input 
              type="text" 
              placeholder="What are you looking for today?" 
              value={query}
              onChange={handleSearch}
              onFocus={() => query.length > 0 && setShowSearch(true)}
              style={{ 
                border: 'none', 
                background: 'transparent', 
                outline: 'none', 
                width: '100%',
                fontSize: '15px',
                color: 'var(--text-primary)'
              }}
            />
          </div>

          {/* Search Dropdown */}
          {showSearch && (
            <div style={{
              position: 'absolute',
              top: '50px',
              left: 0,
              right: 0,
              background: 'var(--bg-base)',
              border: '1px solid var(--border-default)',
              borderRadius: '8px',
              boxShadow: 'var(--shadow-lg)',
              maxHeight: '400px',
              overflowY: 'auto',
              zIndex: 1000
            }}>
              {searchResults.length === 0 ? (
                <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>No stocks found</div>
              ) : (
                searchResults.map(s => (
                  <NavLink key={s.symbol} to={`/stock/${s.symbol}`} style={{ textDecoration: 'none' }}>
                    <div style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer', transition: 'background 0.2s' }} className="search-item">
                      <div>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{s.symbol}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{s.name || s.exchange}</div>
                      </div>
                    </div>
                  </NavLink>
                ))
              )}
            </div>
          )}
        </div>

        {/* Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px', flex: 1, overflowX: 'auto', whiteSpace: 'nowrap' }}>
          <NavLink to="/" style={({ isActive }) => ({ 
            color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
            fontWeight: isActive ? 600 : 500,
            textDecoration: 'none',
            fontSize: '15px'
          })}>Explore</NavLink>
          
          <NavLink to="/investments" style={({ isActive }) => ({ 
            color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
            fontWeight: isActive ? 600 : 500,
            textDecoration: 'none',
            fontSize: '15px'
          })}>Investments</NavLink>

          <NavLink to="/watchlist" style={({ isActive }) => ({ 
            color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
            fontWeight: isActive ? 600 : 500,
            textDecoration: 'none',
            fontSize: '15px'
          })}>Watchlist</NavLink>

          {isProMode && (
            <>
              <div style={{ width: '1px', height: '24px', background: 'var(--border-default)' }}></div>
              <NavLink to="/pro/market" style={({ isActive }) => ({ 
                color: isActive ? '#0066FF' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                textDecoration: 'none',
                fontSize: '14px'
              })}>Market Data</NavLink>
              
              <NavLink to="/pro/logs" style={({ isActive }) => ({ 
                color: isActive ? '#0066FF' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                textDecoration: 'none',
                fontSize: '14px'
              })}>Trade Logs</NavLink>

              <NavLink to="/models" style={({ isActive }) => ({ 
                color: isActive ? '#0066FF' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                textDecoration: 'none',
                fontSize: '14px'
              })}>AI Lab</NavLink>

              <NavLink to="/settings" style={({ isActive }) => ({ 
                color: isActive ? '#0066FF' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                textDecoration: 'none',
                fontSize: '14px'
              })}>Settings</NavLink>
            </>
          )}
        </div>

        {/* Pro Mode Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: isProMode ? '#0066FF' : 'var(--text-muted)' }}>PRO</span>
          <button 
            onClick={toggleProMode}
            style={{
              width: '44px',
              height: '24px',
              borderRadius: '12px',
              background: isProMode ? '#0066FF' : 'var(--gray-300)',
              border: 'none',
              position: 'relative',
              cursor: 'pointer',
              transition: 'background 0.3s'
            }}
          >
            <div style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              background: 'white',
              position: 'absolute',
              top: '2px',
              left: isProMode ? '22px' : '2px',
              transition: 'left 0.3s',
              boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
            }} />
          </button>
        </div>

        {/* User Profile / Wallet */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', borderLeft: '1px solid var(--border-default)', paddingLeft: '24px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Available Balance</span>
            <span style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>{formatPrice(150000)}</span>
          </div>
          <div style={{ 
            width: 36, height: 36, borderRadius: '50%', background: 'var(--gray-100)', 
            border: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', 
            justifyContent: 'center', color: 'var(--primary)', fontWeight: 'bold' 
          }}>
            JD
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main style={{ flex: 1, overflowY: 'auto', padding: '32px 24px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
          <Outlet />
        </div>
      </main>

      {/* Connection Indicator (Fixed Bottom Right) */}
      {!wsConnected && (
        <div style={{ position: 'fixed', bottom: 20, right: 20, background: 'var(--loss)', color: 'white', padding: '8px 16px', borderRadius: '20px', fontSize: '12px', fontWeight: 600, boxShadow: '0 4px 12px rgba(235, 91, 60, 0.3)' }}>
          Reconnecting to market data...
        </div>
      )}
    </div>
  );
}
