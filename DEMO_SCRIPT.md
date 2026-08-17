# QuantumGrow AI - Video Demo Script

## Preparation Before Recording
1. Ensure the application is running (or open `https://quantumgrow-ai.onrender.com` in your browser).
2. For the best visual experience, make your browser full screen.
3. Have a screen recording tool ready (like OBS Studio, Loom, or built-in OS screen recorders). 

---

## 🎬 Script & Flow

### 1. Introduction (0:00 - 0:15)
* **Visual:** Start on the main **Dashboard** view of QuantumGrow AI.
* **Action:** Slowly move the mouse to highlight the active real-time ticker and the main UI components. 
* **Voiceover / Text (if adding captions):** "Welcome to QuantumGrow AI, a full-stack institutional-grade stock screener and machine learning prediction system. Today, I'll demonstrate how our system analyzes real-time market data to identify and evaluate SMMA crossovers."

### 2. Live Scanning & Quantitative Filters (0:15 - 0:30)
* **Visual:** Point to the live feed or the data tables showing incoming stock ticks. 
* **Action:** Highlight the metrics like Bid/Ask Qty and LTP (Last Traded Price).
* **Voiceover / Text:** "The system connects to live broker APIs via WebSockets. It filters NSE-listed stocks in real-time, focusing only on high-liquidity assets between ₹30 and ₹500, discarding noise and low-volume stocks."

### 3. Indicator Detection - SMMA (0:30 - 0:50)
* **Visual:** Switch to the charting section where the 1-minute bars and SMMA lines (20 and 120 periods) are displayed.
* **Action:** Hover over a recent crossover point on the chart.
* **Voiceover / Text:** "As market data streams in, our backend dynamically builds 1-minute bars and computes Smoothed Moving Averages (SMMA). The engine strictly looks for precise state transitions, like the SMMA 20 crossing above the SMMA 120."

### 4. Machine Learning & XAI Explainability (0:50 - 1:20)
* **Visual:** Scroll or click into the **Signals / Predictions** panel where ACCEPT/AVOID decisions are listed.
* **Action:** Expand or click on one of the recent signals to show the explanation (e.g., "LTQ 2-minute average is significantly above...").
* **Voiceover / Text:** "When a crossover is detected, a snapshot of over 25 quantitative features—including order book imbalance and Estimated Traded Quantity (ETQ)—is passed to our Machine Learning pipeline. The XGBoost model then classifies the signal as 'ACCEPT' or 'AVOID'. Furthermore, our Explainable AI provides transparent, rule-based reasoning for every decision."

### 5. Settings & Retraining (1:20 - 1:40)
* **Visual:** Navigate to the **Settings** or **Model Training** page.
* **Action:** Show the configuration toggles (like LIVE/OFFLINE mode, ML thresholds) and point out the 'Retrain Model' button. 
* **Voiceover / Text:** "The system is highly adaptable. Users can adjust liquidity thresholds, tweak indicator periods, or trigger a complete model retraining pipeline on historical data to adapt to new market regimes, all without touching the codebase."

### 6. Conclusion (1:40 - 1:50)
* **Visual:** Return to the main Dashboard, showing the real-time data flowing.
* **Action:** Leave the mouse still to let the user absorb the UI. 
* **Voiceover / Text:** "QuantumGrow AI bridges the gap between advanced quantitative engineering and modern, responsive web design. Thank you for watching."

---

## Tips for Recording
* **Smooth Movements:** Don't move your mouse too erratically. Point deliberately to the things you are talking about.
* **Pacing:** Give the viewer a few seconds to read the screen before moving to the next section.
* **Demo Data:** If the market is closed, ensure your app is running in `OFFLINE` mode (as configured in `.env` or settings) so the dashboard still displays simulated live ticks and crossover signals.
