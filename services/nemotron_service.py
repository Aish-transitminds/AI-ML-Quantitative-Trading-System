import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NemotronService:
    """Service to interact with NVIDIA Nemotron-3-Nano-30B-A3B for ML signal explanations."""

    def __init__(self):
        raw_key = os.getenv("NVIDIA_API_KEY")
        self.api_key = raw_key.strip() if raw_key else None
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "nvidia/nemotron-3-nano-30b-a3b"
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                logger.warning("openai package not installed. Nemotron AI disabled.")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client for Nemotron: {e}")
        else:
            logger.warning("NVIDIA_API_KEY not set. Nemotron AI analyst disabled.")

    def analyze_signal(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an ML signal using Nemotron and return structured reasoning.
        
        Args:
            symbol: The stock symbol
            context: Dictionary containing authoritative ML backend state 
                     (e.g., ltp, smma, ml_probability, decision, features)
        
        Returns:
            Dict containing summary, supporting_factors, risk_factors, and reasoning.
        """
        fallback_response = {
            "summary": "AI Analyst temporarily unavailable.",
            "supporting_factors": [],
            "risk_factors": [],
            "reasoning": "Unable to connect to Nemotron AI. Please verify NVIDIA_API_KEY and network connection."
        }

        if not self.client:
            return fallback_response

        # Strictly enforce constraint: Nemotron MUST NOT calculate probabilities or decisions.
        # It MUST use the provided context to EXPLAIN the decision.
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

        user_prompt = f"Analyze this ML Signal for {symbol}:\n{json.dumps(context, indent=2)}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1,
                top_p=1,
                max_tokens=16384,
                extra_body={"reasoning_budget": 16384},
                timeout=60.0
            )
            
            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("Empty response from Nemotron")
            
            # Remove any <think>...</think> tags which might contain curly braces
            import re
            text_without_think = re.sub(r'<think>.*?</think>', '', result_text, flags=re.DOTALL)
            
            # Extract JSON from potential reasoning output
            json_match = re.search(r'\{.*\}', text_without_think, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                # Ensure it has the expected lowercase keys for the frontend
                return {
                    "summary": parsed.get("summary") or parsed.get("Summary") or "Summary not provided.",
                    "supporting_factors": parsed.get("supporting_factors") or parsed.get("Supporting_Factors") or parsed.get("Supporting Factors") or [],
                    "risk_factors": parsed.get("risk_factors") or parsed.get("Risk_Factors") or parsed.get("Risk Factors") or [],
                    "reasoning": parsed.get("reasoning") or parsed.get("Reasoning") or "Reasoning not provided."
                }
            else:
                raise ValueError("No JSON block found in response")

        except json.JSONDecodeError as e:
            logger.error(f"Nemotron returned invalid JSON: {e}\nResponse: {result_text}")
            fallback_response["reasoning"] = "Received invalid response format from AI Analyst."
            return fallback_response
        except Exception as e:
            logger.error(f"Nemotron AI analysis failed: {e}")
            fallback_response["reasoning"] = f"Nemotron AI analysis failed: {str(e)}"
            return fallback_response
