import os
import re
import time
from threading import Lock
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv

from database import db
from schemas import Channel

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
MODEL = os.getenv("OPENROUTER_MODEL", "z-ai/glm-4.5-air:free")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class SalesAgent:
    def __init__(self):
        self.system_prompt = self._create_system_prompt()
        self.http = requests.Session()
        self._response_cache: Dict[str, tuple[float, str]] = {}
        self._cache_lock = Lock()
        self._cache_ttl_seconds = 120

    def _create_system_prompt(self) -> str:
        return """You are Clara, an elite omnichannel fashion sales strategist.

You MUST:
- Give concrete, data-grounded recommendations from provided catalog context.
- Use memory context from previous conversations to personalize responses.
- Ask only the minimum follow-up questions needed.
- Always include a clear next action (choose product, add to cart, check stock, or checkout).

Response quality bar:
- Insightful and decisive.
- Specific product names, prices, occasions, and stock when available.
- Never generic filler.
- Never mention being an AI model.
"""

    def process(
        self,
        user_message: str,
        history: List[Dict],
        user_context: Dict[str, Any],
        channel: Channel,
    ) -> str:
        rag_context = self._build_rag_context(user_message, user_context)
        return self._generate_response(
            user_message=user_message,
            history=history,
            user_context=user_context,
            channel=channel,
            tool_outputs=[{"source": "rag_context", "content": rag_context}],
            rag_context=rag_context,
        )

    def compose_response(
        self,
        user_message: str,
        history: List[Dict],
        user_context: Dict[str, Any],
        channel: Channel,
        tool_outputs: List[Dict[str, Any]],
    ) -> str:
        rag_context = self._build_rag_context(user_message, user_context)
        merged_outputs = tool_outputs + [{"source": "rag_context", "content": rag_context}]
        return self._generate_response(
            user_message=user_message,
            history=history,
            user_context=user_context,
            channel=channel,
            tool_outputs=merged_outputs,
            rag_context=rag_context,
        )

    def _generate_response(
        self,
        user_message: str,
        history: List[Dict],
        user_context: Dict[str, Any],
        channel: Channel,
        tool_outputs: List[Dict[str, Any]],
        rag_context: Dict[str, Any],
    ) -> str:
        prompt = self._build_prompt(user_context, channel, tool_outputs, rag_context)
        messages = [{"role": "system", "content": prompt}] + history[-8:] + [{"role": "user", "content": user_message}]

        quick_response = self._fast_response_if_possible(user_message, rag_context, user_context)
        if quick_response:
            return quick_response

        llm_reply = self._call_openrouter(messages)
        if llm_reply:
            return llm_reply

        return self._rule_based_response(user_message, user_context, rag_context)

    def _build_prompt(
        self,
        user_context: Dict[str, Any],
        channel: Channel,
        tool_outputs: List[Dict[str, Any]],
        rag_context: Dict[str, Any],
    ) -> str:
        prompt = self.system_prompt
        prompt += "\nCustomer Profile:\n"
        prompt += f"- Name: {user_context.get('name', 'Customer')}\n"
        prompt += f"- Loyalty Score: {user_context.get('loyalty_score', 0)}\n"
        prompt += f"- Past Order Count: {len(user_context.get('past_orders', []))}\n"
        prompt += f"- Channel: {channel.value}\n"

        if user_context.get("cross_channel_memory"):
            prompt += "\nCross-channel memory snippets:\n"
            for item in user_context["cross_channel_memory"][:4]:
                prompt += f"- {item}\n"

        prompt += "\nRAG Context:\n"
        prompt += f"- Parsed Intent: {rag_context.get('intent')}\n"
        prompt += f"- Parsed Preferences: {rag_context.get('preferences')}\n"
        prompt += "- Matched Products:\n"
        for product in rag_context.get("matched_products", [])[:4]:
            prompt += (
                f"  * {product['product_name']} | ${product['price']} | occasion={product['occasion']} "
                f"| category={product['dress_category']} | stock={product['stock']}\n"
            )

        if tool_outputs:
            prompt += "\nSpecialist agent outputs (may be verbose; summarize smartly):\n"
            for idx, output in enumerate(tool_outputs[:3], 1):
                prompt += f"{idx}. {output.get('source')}: {str(output.get('content'))[:550]}\n"

        prompt += "\nHow to answer:\n"
        prompt += "1) Start with a strong direct answer and recommendations.\n"
        prompt += "2) Use specific products from matched products if available.\n"
        prompt += "3) If something critical is missing, ask at most 1-2 focused questions.\n"
        prompt += "4) End with a clear next step the user can take now.\n"
        return prompt

    def _call_openrouter(self, messages: List[Dict[str, str]]) -> str:
        if not OPENROUTER_API_KEY:
            return ""

        cache_key = self._messages_cache_key(messages)
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached

        try:
            response = self.http.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "Retail Sales Agent",
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.25,
                    "max_tokens": 420,
                },
                timeout=(2, 10),
            )
            if response.status_code != 200:
                return ""

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                return ""
            content = (choices[0].get("message", {}).get("content") or "").strip()
            if content:
                self._set_cached_response(cache_key, content)
            return content
        except Exception:
            return ""


    def _messages_cache_key(self, messages: List[Dict[str, str]]) -> str:
        flattened = "|".join(f"{msg.get('role','')}::{msg.get('content','')[:500]}" for msg in messages)
        return f"{MODEL}:{hash(flattened)}"

    def _get_cached_response(self, key: str) -> str:
        with self._cache_lock:
            cached = self._response_cache.get(key)
            if not cached:
                return ""
            created_at, value = cached
            if time.time() - created_at > self._cache_ttl_seconds:
                self._response_cache.pop(key, None)
                return ""
            return value

    def _set_cached_response(self, key: str, value: str) -> None:
        with self._cache_lock:
            self._response_cache[key] = (time.time(), value)

    def _fast_response_if_possible(
        self,
        user_message: str,
        rag_context: Dict[str, Any],
        user_context: Dict[str, Any],
    ) -> str:
        intent = rag_context.get("intent")
        if intent in {"inventory_check", "purchase", "fulfillment"}:
            return self._rule_based_response(user_message, user_context, rag_context)
        if len(user_message.strip()) <= 10:
            return self._rule_based_response(user_message, user_context, rag_context)
        return ""

    def _build_rag_context(self, user_message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        preferences = self._extract_preferences(user_message, user_context)
        matched_products = self._retrieve_products(preferences)
        intent = self._infer_intent(user_message)

        cart_summary = None
        if user_context.get("user_id"):
            cart = db.get_user_cart(user_context["user_id"])
            if cart:
                subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart)
                cart_summary = {
                    "items": len(cart),
                    "subtotal": round(subtotal, 2),
                }

        return {
            "intent": intent,
            "preferences": preferences,
            "matched_products": matched_products,
            "cart_summary": cart_summary,
            "memory": user_context.get("cross_channel_memory", []),
        }

    def _extract_preferences(self, message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        text = message.lower()
        preferences: Dict[str, Any] = {}

        occasion_map = {
            "wedding": "Formal",
            "gala": "Formal",
            "prom": "Formal",
            "formal": "Formal",
            "office": "Business",
            "business": "Business",
            "casual": "Casual",
            "party": "Party",
            "date": "Date",
        }
        for keyword, normalized in occasion_map.items():
            if keyword in text:
                preferences["occasion"] = normalized
                break

        budget_match = re.search(r"(?:under|below|less than|upto|up to)\s*\$?(\d+(?:\.\d+)?)", text)
        if budget_match:
            preferences["max_price"] = float(budget_match.group(1))

        price_range = re.search(r"\$?(\d+(?:\.\d+)?)\s*(?:to|\-|–)\s*\$?(\d+(?:\.\d+)?)", text)
        if price_range:
            low, high = float(price_range.group(1)), float(price_range.group(2))
            preferences["min_price"] = min(low, high)
            preferences["max_price"] = max(low, high)

        colors = ["black", "white", "blue", "navy", "red", "green", "pink", "beige", "burgundy"]
        found_colors = [color for color in colors if color in text]
        if found_colors:
            preferences["colors"] = found_colors

        if user_context.get("style_preferences") and "colors" not in preferences:
            preferences["colors"] = user_context["style_preferences"].get("colors", [])

        return preferences

    def _retrieve_products(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        products = db.products[:]

        occasion = preferences.get("occasion")
        min_price = preferences.get("min_price")
        max_price = preferences.get("max_price")
        colors = preferences.get("colors", [])

        scored: List[tuple[int, Dict[str, Any]]] = []
        for product in products:
            score = 0

            if occasion and product.get("occasion", "").lower() == occasion.lower():
                score += 4
            if min_price is not None and product.get("price", 0) >= min_price:
                score += 1
            if max_price is not None and product.get("price", 0) <= max_price:
                score += 2
            if colors:
                product_colors = product.get("colors", "").lower()
                if any(color in product_colors for color in colors):
                    score += 2

            score += 1 if product.get("stock", 0) > 0 else -2
            score += 1 if product.get("featured_dress") else 0

            if occasion or min_price is not None or max_price is not None or colors:
                if score > 0:
                    scored.append((score, product))
            else:
                scored.append((score, product))

        scored.sort(key=lambda row: (row[0], row[1].get("stock", 0)), reverse=True)
        return [row[1] for row in scored[:6]]

    def _infer_intent(self, message: str) -> str:
        lower = message.lower()
        if any(word in lower for word in ["recommend", "suggest", "find", "dress", "outfit"]):
            return "recommendation"
        if any(word in lower for word in ["stock", "available", "inventory"]):
            return "inventory_check"
        if any(word in lower for word in ["checkout", "pay", "buy", "purchase"]):
            return "purchase"
        if any(word in lower for word in ["delivery", "ship", "pickup"]):
            return "fulfillment"
        return "general_sales"

    def _rule_based_response(self, user_message: str, user_context: Dict[str, Any], rag_context: Dict[str, Any]) -> str:
        name = user_context.get("name", "there").split()[0]
        matched = rag_context.get("matched_products", [])
        preferences = rag_context.get("preferences", {})

        if len(user_message.strip()) <= 4:
            return (
                f"Hi {name}! I can help you choose the best dress quickly. "
                "Tell me your occasion, budget, and preferred color, and I'll shortlist top in-stock options instantly."
            )

        if matched:
            lines = []
            for product in matched[:3]:
                lines.append(
                    f"• {product['product_name']} — ${product['price']} ({product['occasion']}), stock: {product['stock']}"
                )

            preference_line = ""
            if preferences:
                preference_line = f"Based on your preferences {preferences}, here are my top picks:\n"

            return (
                f"Excellent choice, {name}. {preference_line}{chr(10).join(lines)}\n\n"
                "If you like one of these, tell me the product name and quantity and I'll help you add it to cart and move to checkout."
            )

        return (
            f"Got it, {name}. I can still help you find the right formal option. "
            "Share your budget range and preferred color, and I'll narrow down the best available dresses for you."
        )

    def _get_loyalty_tier(self, score: int) -> str:
        if score >= 500:
            return "Platinum"
        if score >= 200:
            return "Gold"
        if score >= 100:
            return "Silver"
        return "Bronze"
