import os
import json
from openai import OpenAI

api_key = os.getenv("NVIDIA_API_KEY")
base_url = "https://integrate.api.nvidia.com/v1"
model = "nvidia/nemotron-3-nano-30b-a3b"

client = OpenAI(api_key=api_key, base_url=base_url)

system_prompt = (
    "You are an expert quantitative market analyst. "
    "Your job is ONLY to explain the reasoning behind a pre-calculated Machine Learning trading signal. "
    "You MUST NOT calculate or suggest your own entry price, exit price, P&L, probability, or ACCEPT/AVOID decision. "
    "You MUST accept the ML decision and probability provided to you as absolute truth. "
    "Respond ONLY with a valid JSON object matching this schema exactly:\n"
    "{\n"
    '  "summary": "1-2 sentences summarizing the technical setup.",\n'
    '  "supporting_factors": ["string array of bullish/bearish points supporting the decision"],\n'
    '  "risk_factors": ["string array of risks or opposing indicators"],\n'
    '  "reasoning": "Detailed 2-3 paragraph explanation of the market context and why the ML model likely made this decision."\n'
    "}"
)

context = {
    "symbol": "DEMO_SBIN-EQ",
    "ltp": 100.99,
    "smma_fast": 100.92,
    "smma_slow": 100.75,
    "signal": "BUY",
    "ml_probability": 0.85,
    "decision": "ACCEPT",
    "liquidity": {
        "bid_qty": 2493000,
        "ask_qty": 910000
    }
}
user_prompt = f"Analyze this ML Signal for {context['symbol']}:\n{json.dumps(context, indent=2)}"

response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=1,
    top_p=1,
    max_tokens=4096,
    extra_body={"reasoning_budget": 2048},
    timeout=60.0
)

print(response.choices[0].message.content)
