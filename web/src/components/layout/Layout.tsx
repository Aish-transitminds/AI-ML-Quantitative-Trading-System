import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useStore } from '../../stores/useStore';
import { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { formatPrice } from '../../utils/formatters';

export default function Layout() {
  const { wsConnected, searchStocks, searchResults, isProMode, toggleProMode } = useStore();
  const [query, setQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  // Handle window resize
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Close menu and search when location changes
  useEffect(() => {
    setShowSearch(false);
    setQuery('');
    setMobileMenuOpen(false);
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
      {/* Mobile + Desktop Top Navigation */}
      <nav style={{ 
        height: 'var(--topbar-height)', 
        background: 'var(--bg-base)', 
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        alignItems: 'center',
        padding: isMobile ? '0 12px' : '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        gap: isMobile ? '12px' : '40px'
      }}>
        {/* Mobile Hamburger Menu */}
        {isMobile && (
          <button 
            className={`hamburger-menu ${mobileMenuOpen ? 'open' : ''}`}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '4px', padding: '8px' }}
          >
            <span style={{ width: 24, height: 2, background: 'var(--text-primary)', borderRadius: 1 }}></span>
            <span style={{ width: 24, height: 2, background: 'var(--text-primary)', borderRadius: 1 }}></span>
            <span style={{ width: 24, height: 2, background: 'var(--text-primary)', borderRadius: 1 }}></span>
          </button>
        )}

        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
          <div style={{ width: 28, height: 28, borderRadius: '6px', background: 'var(--primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', flexShrink: 0 }}>Q</div>
          {!isMobile && <span style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>QuantumGrow</span>}
          
          {/* Offline Mode Badge — Static */}
          <div 
            style={{ 
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginLeft: isMobile ? '4px' : '8px',
              padding: '4px 10px',
              borderRadius: '20px',
              background: 'rgba(255, 152, 0, 0.12)',
              border: '1px solid rgba(255, 152, 0, 0.3)',
            }}
            title="Application is running in OFFLINE DEMO mode with synthetic data."
          >
            <div style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#FF9800',
              flexShrink: 0,
            }} />
            <span style={{ 
              fontSize: '11px', 
              fontWeight: 700, 
              color: '#FF9800',
              letterSpacing: '0.5px',
            }}>
              OFFLINE DEMO
            </span>
          </div>
        </div>

        {/* Global Search - Hide on very small mobile */}
        {!isMobile && (
          <div style={{ flex: 1, maxWidth: '350px', position: 'relative' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              background: 'var(--bg-surface)', 
              border: '1px solid var(--border-default)',
              borderRadius: '8px',
              padding: '0 12px',
              height: '36px',
              transition: 'all 0.2s',
            }} className="search-bar-container">
              <Search size={16} color="var(--text-muted)" style={{ marginRight: '8px', flexShrink: 0 }} />
              <input 
                type="text" 
                placeholder="Find stocks..." 
                value={query}
                onChange={handleSearch}
                onFocus={() => query.length > 0 && setShowSearch(true)}
                style={{ 
                  border: 'none', 
                  background: 'transparent', 
                  outline: 'none', 
                  width: '100%',
                  fontSize: '13px',
                  color: 'var(--text-primary)'
                }}
              />
            </div>

            {/* Search Dropdown */}
            {showSearch && (
              <div style={{
                position: 'absolute',
                top: '40px',
                left: 0,
                right: 0,
                background: 'var(--bg-base)',
                border: '1px solid var(--border-default)',
                borderRadius: '8px',
                boxShadow: 'var(--shadow-lg)',
                maxHeight: '300px',
                overflowY: 'auto',
                zIndex: 1000
              }}>
                {searchResults.length === 0 ? (
                  <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>No stocks found</div>
                ) : (
                  searchResults.map(s => (
                    <NavLink key={s.symbol} to={`/stock/${s.symbol}`} style={{ textDecoration: 'none' }}>
                      <div style={{ padding: '10px 12px', display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer', transition: 'background 0.2s', fontSize: '13px' }} className="search-item">
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{s.symbol}</div>
                          <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{s.exchange}</div>
                        </div>
                      </div>
                    </NavLink>
                  ))
                )}
              </div>
            )}
          </div>
        )}

        {/* Desktop Navigation Links */}
        {!isMobile && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flex: 1, whiteSpace: 'nowrap', overflow: 'auto' }}>
            <NavLink to="/" style={({ isActive }) => ({ 
              color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
              fontWeight: isActive ? 600 : 500,
              textDecoration: 'none',
              fontSize: '13px'
            })}>Explore</NavLink>
            
            <NavLink to="/investments" style={({ isActive }) => ({ 
              color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
              fontWeight: isActive ? 600 : 500,
              textDecoration: 'none',
              fontSize: '13px'
            })}>Investments</NavLink>

            <NavLink to="/watchlist" style={({ isActive }) => ({ 
              color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
              fontWeight: isActive ? 600 : 500,
              textDecoration: 'none',
              fontSize: '13px'
            })}>Watchlist</NavLink>

            {isProMode && (
              <>
                <div style={{ width: '1px', height: '20px', background: 'var(--border-default)' }}></div>
                <NavLink to="/pro/market" style={({ isActive }) => ({ 
                  color: isActive ? '#0066FF' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 500,
                  textDecoration: 'none',
                  fontSize: '12px'
                })}>Market</NavLink>
                
                <NavLink to="/pro/logs" style={({ isActive }) => ({ 
                  color: isActive ? '#0066FF' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 500,
                  textDecoration: 'none',
                  fontSize: '12px'
                })}>Logs</NavLink>

                <NavLink to="/models" style={({ isActive }) => ({ 
                  color: isActive ? '#0066FF' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 500,
                  textDecoration: 'none',
                  fontSize: '12px'
                })}>Lab</NavLink>

                <NavLink to="/settings" style={({ isActive }) => ({ 
                  color: isActive ? '#0066FF' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 500,
                  textDecoration: 'none',
                  fontSize: '12px'
                })}>Settings</NavLink>
              </>
            )}
          </div>
        )}

        {/* Flex spacer on mobile */}
        {isMobile && <div style={{ flex: 1 }}></div>}

        {/* Desktop Right Section */}
        {!isMobile && (
          <>
            {/* Pro Mode Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '11px', fontWeight: 600, color: isProMode ? '#0066FF' : 'var(--text-muted)' }}>PRO</span>
              <button 
                onClick={toggleProMode}
                style={{
                  width: '40px',
                  height: '22px',
                  borderRadius: '11px',
                  background: isProMode ? '#0066FF' : 'var(--gray-300)',
                  border: 'none',
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'background 0.3s'
                }}
              >
                <div style={{
                  width: '18px',
                  height: '18px',
                  borderRadius: '50%',
                  background: 'white',
                  position: 'absolute',
                  top: '2px',
                  left: isProMode ? '20px' : '2px',
                  transition: 'left 0.3s',
                  boxShadow: '0 1px 2px rgba(0,0,0,0.2)'
                }} />
              </button>
            </div>

            {/* User Profile / Wallet */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', borderLeft: '1px solid var(--border-default)', paddingLeft: '16px', minWidth: 0 }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Balance</span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{formatPrice(150000)}</span>
              </div>
              <div style={{ 
                width: 32, height: 32, borderRadius: '50%', background: 'var(--gray-100)', 
                border: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', 
                justifyContent: 'center', color: 'var(--primary)', fontWeight: 'bold', fontSize: '12px', flexShrink: 0
              }}>
                JD
              </div>
            </div>
          </>
        )}

        {/* Mobile Menu Button */}
        {isMobile && (
          <button 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '6px', color: 'var(--text-primary)' }}
          >
            {mobileMenuOpen ? <X size={20} /> : null}
          </button>
        )}
      </nav>

      {/* Mobile Navigation Drawer */}
      {isMobile && mobileMenuOpen && (
        <>
          {/* Overlay */}
          <div 
            className="modal-overlay"
            onClick={() => setMobileMenuOpen(false)}
            style={{ position: 'fixed', top: 'var(--topbar-height)', left: 0, right: 0, bottom: 0, background: 'rgba(0, 0, 0, 0.3)', zIndex: 98 }}
          />
          
          {/* Mobile Menu */}
          <div style={{
            position: 'fixed',
            top: 'var(--topbar-height)',
            left: 0,
            width: '80vw',
            maxWidth: '320px',
            background: 'var(--bg-base)',
            borderRight: '1px solid var(--border-default)',
            boxShadow: 'var(--shadow-lg)',
            zIndex: 99,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <nav style={{ display: 'flex', flexDirection: 'column', padding: '12px 0' }}>
              <NavLink to="/" onClick={() => setMobileMenuOpen(false)} style={({ isActive }) => ({ 
                padding: '12px 16px',
                color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                textDecoration: 'none',
                fontSize: '14px',
                borderLeft: isActive ? '3px solid var(--primary)' : '3px solid transparent',
                background: isActive ? 'var(--bg-surface)' : 'transparent',
                display: 'block'
              })}>Explore</NavLink>
              
              <NavLink to="/investments" onClick={() => setMobileMenuOpen(false)} style={({ isActive }) => ({ 
                padding: '12px 16px',
                color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                textDecoration: 'none',
                fontSize: '14px',
                borderLeft: isActive ? '3px solid var(--primary)' : '3px solid transparent',
                background: isActive ? 'var(--bg-surface)' : 'transparent',
                display: 'block'
              })}>Investments</NavLink>

              <NavLink to="/watchlist" onClick={() => setMobileMenuOpen(false)} style={({ isActive }) => ({ 
                padding: '12px 16px',
                color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                textDecoration: 'none',
                fontSize: '14px',
                borderLeft: isActive ? '3px solid var(--primary)' : '3px solid transparent',
                background: isActive ? 'var(--bg-surface)' : 'transparent',
                display: 'block'
              })}>Watchlist</NavLink>

              {isProMode && (
                <>
                  <div style={{ height: '1px', background: 'var(--border-default)', margin: '8px 0' }}></div>
                  <NavLink to="/pro/market" onClick={() => setMobileMenuOpen(false)} style={({ isActive }) => ({ 
                    padding: '12px 16px',
                    color: isActive ? '#0066FF' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    textDecoration: 'none',
                    fontSize: '14px',
                    borderLeft: isActive ? '3px solid #0066FF' : '3px solid transparent',
                    background: isActive ? 'var(--bg-surface)' : 'transparent',
                    display: 'block'
                  })}>Market Data</NavLink>
                  
                  <NavLink to="/pro/logs" onClick={() => setMobileMenuOpen(false)} style={({ isActive }) => ({ 
                    padding: '12px 16px',
                    color: isActive ? '#0066FF' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    textDecoration: 'none',
                    fontSize: '14px',
                    borderLeft: isActive ? '3px solid #0066FF' : '3px solid transparent',
                    background: isActive ? 'var(--bg-surface)' : 'transparent',
                    display: 'block'
                  })}>Trade Logs</NavLink>

                  <NavLink to="/models" onClick={() => setMobileMenuOpen(false)} style={({ isActive }) => ({ 
                    padding: '12px 16px',
                    color: isActive ? '#0066FF' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    textDecoration: 'none',
                    fontSize: '14px',
                    borderLeft: isActive ? '3px solid #0066FF' : '3px solid transparent',
                    background: isActive ? 'var(--bg-surface)' : 'transparent',
                    display: 'block'
                  })}>AI Lab</NavLink>

                  <NavLink to="/settings" onClick={() => setMobileMenuOpen(false)} style={({ isActive }) => ({ 
                    padding: '12px 16px',
                    color: isActive ? '#0066FF' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    textDecoration: 'none',
                    fontSize: '14px',
                    borderLeft: isActive ? '3px solid #0066FF' : '3px solid transparent',
                    background: isActive ? 'var(--bg-surface)' : 'transparent',
                    display: 'block'
                  })}>Settings</NavLink>
                </>
              )}
            </nav>

            {/* Mobile Pro Toggle */}
            <div style={{ borderTop: '1px solid var(--border-default)', padding: '12px 16px', marginTop: 'auto' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', fontWeight: 600, color: isProMode ? '#0066FF' : 'var(--text-secondary)' }}>PRO Mode</span>
                <button 
                  onClick={toggleProMode}
                  style={{
                    width: '40px',
                    height: '22px',
                    borderRadius: '11px',
                    background: isProMode ? '#0066FF' : 'var(--gray-300)',
                    border: 'none',
                    position: 'relative',
                    cursor: 'pointer',
                    transition: 'background 0.3s'
                  }}
                >
                  <div style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    background: 'white',
                    position: 'absolute',
                    top: '2px',
                    left: isProMode ? '20px' : '2px',
                    transition: 'left 0.3s',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.2)'
                  }} />
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Main Content Area */}
      <main style={{ flex: 1, overflowY: 'auto', padding: isMobile ? '12px 12px' : '24px 32px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
          <Outlet />
        </div>
      </main>

      {/* Connection Indicator (Fixed Bottom Right) */}
      {!wsConnected && (
        <div style={{ position: 'fixed', bottom: 20, right: 20, background: 'var(--loss)', color: 'white', padding: '8px 12px', borderRadius: '20px', fontSize: '11px', fontWeight: 600, boxShadow: '0 4px 12px rgba(235, 91, 60, 0.3)', zIndex: 50 }}>
          Reconnecting...
        </div>
      )}
    </div>
  );
}
