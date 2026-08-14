"""FastAPI REST + WebSocket API server for the AI/ML Stock Predictor.

Wraps the existing Application class with proper HTTP/WS endpoints.
All core logic (SMMA, crossovers, ML, features) remains unchanged.

Endpoints:
    GET  /api/status            — system status
    GET  /api/stocks            — all screened stocks
    GET  /api/stocks/{symbol}   — individual stock detail
    GET  /api/trades            — all trades
    GET  /api/trades/stats      — trade statistics
    GET  /api/models            — ML model results
    GET  /api/models/importance — feature importance
    GET  /api/models/threshold  — threshold analysis
    GET  /api/config            — current settings
    POST /api/models/retrain    — trigger retraining
    WS   /ws                    — real-time state pushes
"""
from __future__ import annotations

import asyncio
import json
import os
import threading
import time
import urllib.request
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from main import get_application, Application
from config import settings


# ─── Application lifecycle ─────────────────────────────────────────────────

_app_instance: Optional[Application] = None


def _get_app() -> Application:
    """Get or create and start the Application singleton."""
    global _app_instance
    if _app_instance is None:
        _app_instance = get_application()
        try:
            _app_instance.start()
        except Exception as e:
            print(f"Application start failed: {e}")
            raise
    return _app_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start core engine on server startup."""
    _get_app()
    
    # Start the keep-awake background task to prevent Render from sleeping
    keep_awake = asyncio.create_task(keep_awake_task())
    
    yield
    
    keep_awake.cancel()
    if _app_instance:
        _app_instance.stop()


# ─── FastAPI app ────────────────────────────────────────────────────────────

api = FastAPI(
    title="AI/ML Quantitative Trading System",
    description="Institutional-grade stock screening and ML prediction API",
    version="2.0.0",
    lifespan=lifespan,
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Helper: serialize dataclass/objects ────────────────────────────────────

def _serialize_screen_result(result) -> Dict[str, Any]:
    """Convert a StockScreenResult to a JSON-safe dict."""
    return {
        "symbol": result.symbol,
        "exchange": result.exchange,
        "token": result.token,
        "ltp": result.ltp,
        "bid_price": result.bid_price,
        "bid_quantity": result.bid_quantity,
        "ask_price": result.ask_price,
        "ask_quantity": result.ask_quantity,
        "smma_fast": result.smma_fast,
        "smma_slow": result.smma_slow,
        "smma_difference": result.smma_difference,
        "etq_5m": result.etq_5m,
        "etq_20m": result.etq_20m,
        "etq_60m": result.etq_60m,
        "avg_ltp_20m": result.avg_ltp_20m,
        "avg_ltp_60m": result.avg_ltp_60m,
        "signal": result.signal,
        "ml_probability": result.ml_probability,
        "decision": result.decision,
        "passes_ltp_filter": result.passes_ltp_filter,
        "passes_liquidity_filter": result.passes_liquidity_filter,
        "last_update": result.last_update.isoformat() if result.last_update else None,
    }


# ─── REST endpoints ────────────────────────────────────────────────────────

@api.get("/api/ping")
async def ping():
    """Lightweight health-check endpoint to keep the server awake."""
    return {"status": "awake", "timestamp": datetime.now().isoformat()}


async def keep_awake_task():
    """Internal scheduler to ping our own URL every 10 minutes to prevent Render free-tier sleep."""
    # Render provides RENDER_EXTERNAL_URL automatically. Fallback to localhost if not found.
    base_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not base_url:
        base_url = f"http://127.0.0.1:{os.environ.get('PORT', 8000)}"
        
    ping_url = f"{base_url.rstrip('/')}/api/ping"
    
    while True:
        # Sleep for 10 minutes (Render sleeps after 15 mins of inactivity)
        await asyncio.sleep(10 * 60)
        try:
            def _do_ping():
                req = urllib.request.Request(ping_url, headers={'User-Agent': 'QuantumGrow-KeepAlive/1.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    return response.status
            
            status = await asyncio.to_thread(_do_ping)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Keep-awake ping sent to {ping_url} (Status: {status})")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Keep-awake ping failed: {e}")


@api.get("/api/status")
async def get_status():
    """System status: mode, broker, counts, connection state."""
    app = _get_app()
    state = app.state.get_snapshot()
    return state.get("status", {})


@api.get("/api/stocks")
async def get_stocks():
    """All screened stocks with current data and signals."""
    app = _get_app()
    state = app.state.get_snapshot()
    screen_results = state.get("screen_results", {})

    stocks = []
    for symbol, result in screen_results.items():
        stocks.append(_serialize_screen_result(result))

    # Sort: qualified first, then by symbol
    stocks.sort(key=lambda s: (
        not (s["passes_ltp_filter"] and s["passes_liquidity_filter"]),
        s["symbol"],
    ))
    return {
        "stocks": stocks,
        "total": len(stocks),
        "qualified": sum(
            1 for s in stocks
            if s["passes_ltp_filter"] and s["passes_liquidity_filter"]
        ),
    }


@api.get("/api/stocks/{symbol}")
async def get_stock_detail(symbol: str):
    """Detailed view of a single stock: market data, SMMA, signals, features."""
    app = _get_app()
    state = app.state.get_snapshot()
    screen_results = state.get("screen_results", {})

    result = screen_results.get(symbol)
    if not result:
        return {"error": f"Stock {symbol} not found", "available": list(screen_results.keys())}

    data = _serialize_screen_result(result)

    # Add signal explanation if available
    explanation = state.get("signal_explanations", {}).get(symbol, {})
    data["explanation"] = explanation

    # Add bars for charting
    bars = state.get("bars", {}).get(symbol, [])
    data["bars"] = bars

    # Add related trades
    trades = state.get("trades", [])
    data["related_trades"] = [t for t in trades if t.get("symbol") == symbol]

    return data


@api.get("/api/trades")
async def get_trades():
    """All trades (open + closed) with full details."""
    app = _get_app()
    state = app.state.get_snapshot()
    trades = state.get("trades", [])
    return {
        "trades": trades,
        "total": len(trades),
        "open": sum(1 for t in trades if t.get("status") == "OPEN"),
        "closed": sum(1 for t in trades if t.get("status") == "CLOSED"),
    }


@api.get("/api/trades/stats")
async def get_trade_stats():
    """Trading performance statistics: win rate, P&L, profit factor."""
    app = _get_app()
    state = app.state.get_snapshot()
    return state.get("trade_stats", {})


@api.get("/api/models")
async def get_models():
    """ML model comparison results (all models)."""
    app = _get_app()
    state = app.state.get_snapshot()
    return {
        "results": state.get("model_results", {}),
        "best_model": state.get("best_model_name"),
        "model_metrics": state.get("model_metrics", {}),
        "dataset_info": state.get("dataset_info", {}),
    }


@api.get("/api/models/importance")
async def get_feature_importance():
    """Feature importance from the best model."""
    app = _get_app()
    state = app.state.get_snapshot()
    importance = state.get("feature_importance", {})

    # Sort by importance descending
    sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    return {
        "features": [{"name": name, "importance": value} for name, value in sorted_features],
        "model": state.get("best_model_name"),
    }


@api.get("/api/models/threshold")
async def get_threshold_analysis():
    """Threshold analysis from validation set."""
    app = _get_app()
    state = app.state.get_snapshot()
    return {
        "analysis": state.get("threshold_analysis", []),
        "current_threshold": settings.ML_THRESHOLD,
    }


@api.get("/api/config")
async def get_config():
    """Current system configuration."""
    return {
        "mode": settings.MODE,
        "screening": {
            "ltp_min": settings.LTP_MIN,
            "ltp_max": settings.LTP_MAX,
            "min_bid_qty": settings.MIN_BID_QTY,
            "min_ask_qty": settings.MIN_ASK_QTY,
        },
        "smma": {
            "fast_period": settings.SMMA_FAST_PERIOD,
            "slow_period": settings.SMMA_SLOW_PERIOD,
            "timeframe": settings.SMMA_TIMEFRAME,
        },
        "ml": {
            "threshold": settings.ML_THRESHOLD,
            "min_trades_for_training": settings.MIN_TRADES_FOR_TRAINING,
            "train_ratio": settings.TRAIN_RATIO,
            "validation_ratio": settings.VALIDATION_RATIO,
            "test_ratio": settings.TEST_RATIO,
        },
        "data": {
            "tick_buffer_max_minutes": settings.TICK_BUFFER_MAX_MINUTES,
            "persist_interval_seconds": settings.TICK_PERSIST_INTERVAL_SECONDS,
            "historical_bars_fetch": settings.HISTORICAL_BARS_FETCH,
        },
    }


@api.post("/api/models/retrain")
async def retrain_models():
    """Trigger ML model retraining."""
    app = _get_app()
    try:
        app._train_model()
        state = app.state.get_snapshot()
        return {
            "success": True,
            "best_model": state.get("best_model_name"),
            "model_results": state.get("model_results", {}),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── B2C Consumer Endpoints ───────────────────────────────────────────────────

@api.get("/api/search")
async def search_stocks(q: str = ""):
    """Search for instruments by symbol or name."""
    app = _get_app()
    q = q.lower()
    instruments = app.db.get_instruments()
    results = []
    for inst in instruments:
        if q in inst["symbol"].lower() or (inst.get("name") and q in inst["name"].lower()):
            results.append(inst)
            if len(results) >= 20:  # Limit search results
                break
    return {"results": results}


@api.get("/api/watchlist")
async def get_watchlist():
    """Get user watchlist."""
    app = _get_app()
    return {"watchlist": app.db.get_watchlist()}


@api.post("/api/watchlist/{symbol}")
async def add_to_watchlist(symbol: str):
    """Add symbol to watchlist."""
    app = _get_app()
    app.db.add_to_watchlist(symbol)
    return {"success": True, "symbol": symbol}


@api.delete("/api/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    """Remove symbol from watchlist."""
    app = _get_app()
    app.db.remove_from_watchlist(symbol)
    return {"success": True, "symbol": symbol}


@api.get("/api/portfolio")
async def get_portfolio():
    """Simulate a user portfolio based on open/closed trades."""
    app = _get_app()
    state = app.state.get_snapshot()
    trades = state.get("trades", [])
    
    open_trades = [t.copy() for t in trades if t.get("status") == "OPEN"]
    
    total_invested = 0
    current_value = 0
    
    # Calculate current value based on latest LTP from screen_results
    screen_results = state.get("screen_results", {})
    
    for t in open_trades:
        sym = t.get("symbol")
        entry = t.get("entry_price", 0)
        signal = t.get("signal", "BUY")
        
        ltp = entry
        if sym in screen_results:
            ltp = screen_results[sym].ltp
            
        t["current_ltp"] = ltp
        
        if signal == "BUY":
            total_invested += entry
            val = ltp
            t["current_value"] = val
            t["return"] = val - entry
            current_value += val
        else:
            # Short Sell Logic
            total_invested += entry
            # If you short at 100, and it drops to 90, profit is +10. Value of position = 110.
            val = entry + (entry - ltp)
            t["current_value"] = val
            t["return"] = entry - ltp
            current_value += val
        
    total_return = current_value - total_invested
    total_return_pct = (total_return / total_invested * 100) if total_invested > 0 else 0
    
    return {
        "balance": 150000.00,  # Simulated available cash
        "total_invested": total_invested,
        "current_value": current_value,
        "total_return": total_return,
        "total_return_pct": total_return_pct,
        "holdings": open_trades
    }


@api.post("/api/execute")
async def execute_trade(payload: dict):
    """Execute a simulated manual trade."""
    app = _get_app()
    symbol = payload.get("symbol")
    signal_str = payload.get("signal", "BUY")
    
    # Get current price from screen_results
    state = app.state.get_snapshot()
    screen_results = state.get("screen_results", {})
    if symbol not in screen_results:
        return {"success": False, "error": f"Symbol {symbol} not found in market data."}
        
    current_ltp = screen_results[symbol].ltp
    
    from data.models import Trade, SignalType, TradeStatus
    
    trade = Trade(
        symbol=symbol,
        signal=SignalType(signal_str),
        entry_timestamp=datetime.now(),
        entry_price=current_ltp,
        status=TradeStatus.OPEN,
        ml_decision="MANUAL",
        ml_probability=1.0,
    )
    
    # Insert to DB
    app.db.insert_trade(trade)
    # Refresh app's internal trade list from DB so UI updates instantly
    app._update_trades_list()
    
    return {"success": True, "trade_id": trade.id, "price": current_ltp}

@api.post("/api/trades/{trade_id}/close")
async def close_trade(trade_id: int):
    """Close an open manual trade."""
    app = _get_app()
    open_trades = app.db.get_open_trades()
    trade_obj = next((t for t in open_trades if t.id == trade_id), None)
    
    if not trade_obj:
         return {"success": False, "error": "Trade not found or already closed."}
         
    state = app.state.get_snapshot()
    screen_results = state.get("screen_results", {})
    if trade_obj.symbol not in screen_results:
        return {"success": False, "error": f"Symbol {trade_obj.symbol} not found in market data."}
        
    current_ltp = screen_results[trade_obj.symbol].ltp
    
    trade_obj.close(exit_timestamp=datetime.now(), exit_price=current_ltp)
    app.db.update_trade(trade_obj)
    app._update_trades_list()
    
    return {"success": True, "trade_id": trade_id, "pnl": trade_obj.pnl}

@api.get("/api/snapshot")
async def get_full_snapshot():
    """Complete application state snapshot (used by WebSocket fallback)."""
    app = _get_app()
    state = app.state.get_snapshot()

    # Serialize screen results
    serialized_results = {}
    for sym, result in state.get("screen_results", {}).items():
        serialized_results[sym] = _serialize_screen_result(result)

    qualified = {}
    for sym, result in state.get("qualified_results", {}).items():
        qualified[sym] = _serialize_screen_result(result)

    return {
        "status": state.get("status", {}),
        "stocks": serialized_results,
        "qualified": qualified,
        "trades": state.get("trades", []),
        "trade_stats": state.get("trade_stats", {}),
        "model_results": state.get("model_results", {}),
        "feature_importance": state.get("feature_importance", {}),
        "threshold_analysis": state.get("threshold_analysis", []),
        "dataset_info": state.get("dataset_info", {}),
        "best_model_name": state.get("best_model_name"),
        "model_metrics": state.get("model_metrics", {}),
        "signal_explanations": state.get("signal_explanations", {}),
    }


# ─── WebSocket — real-time state pushes ─────────────────────────────────────

class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(data)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)


ws_manager = ConnectionManager()


@api.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time state updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Push snapshot every 2 seconds
            try:
                snapshot = await asyncio.to_thread(_build_ws_snapshot)
                await websocket.send_json(snapshot)
            except Exception:
                pass
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


def _build_ws_snapshot() -> dict:
    """Build a WebSocket-friendly snapshot."""
    app = _get_app()
    state = app.state.get_snapshot()

    stocks = []
    for sym, result in state.get("screen_results", {}).items():
        stocks.append(_serialize_screen_result(result))

    return {
        "type": "state_update",
        "timestamp": datetime.now().isoformat(),
        "status": state.get("status", {}),
        "stocks": stocks,
        "trade_stats": state.get("trade_stats", {}),
        "best_model": state.get("best_model_name"),
    }


# ─── Static file serving (production) ──────────────────────────────────────

import sys
def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

_web_dist = get_base_path() / "web" / "dist"
if _web_dist.exists():
    api.mount("/assets", StaticFiles(directory=str(_web_dist / "assets")), name="assets")

    @api.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for any non-API route."""
        file_path = _web_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_web_dist / "index.html"))
