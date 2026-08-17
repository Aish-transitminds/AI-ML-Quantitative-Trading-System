# Broker Setup (Angel One)

QuantumGrow interfaces primarily with Angel One via SmartAPI.

## Credentials Required

You need the following variables in your `.env` file:
```
BROKER=angel_one
API_KEY=<Your SmartAPI Key>
CLIENT_ID=<Your Angel One Client ID>
PASSWORD=<Your Angel One PIN>
TOTP_SECRET=<Your SmartAPI TOTP Token>
```

## Connection Lifecycle

1. **Authentication**: Handled via TOTP generation directly in the `AngelOneProvider` using `pyotp`.
2. **WebSocket Streaming**: Uses Mode 3 (Full) and Mode 1 (LTP) depending on the stock's qualification state.
3. **Resiliency**: The broker manager automatically monitors disconnect events. If a connection is dropped, a dedicated background thread handles the reconnection delay and seamlessly resubscribes the tracked tokens.

## Paisa Normalization
Angel One WebSocket payloads occasionally supply prices in "Paisa" instead of Rupees. The `AngelOneProvider` handles this normalization deterministically by unconditionally dividing Open, High, Low, Close, LTP, and Bid/Ask depth arrays by 100 before emitting `MarketTick` objects into the pipeline.
