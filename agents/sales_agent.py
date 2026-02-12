import os
<<<<<<< HEAD
import re
from typing import List, Dict, Any, Optional
=======
from typing import List, Dict, Any
>>>>>>> main

import requests
from dotenv import load_dotenv

from database import db
from schemas import Channel

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
<<<<<<< HEAD
MODEL = os.getenv("OPENROUTER_MODEL", "z-ai/glm-4.5-air:free")
=======
MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
>>>>>>> main
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class SalesAgent:
    def __init__(self):
        self.system_prompt = self._create_system_prompt()

    def _create_system_prompt(self) -> str:
<<<<<<< HEAD
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
        messages = [{"role": "system", "content": prompt}] + history[-12:] + [{"role": "user", "content": user_message}]

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
            for item in user_context["cross_channel_memory"][:8]:
                prompt += f"- {item}\n"

        prompt += "\nRAG Context:\n"
        prompt += f"- Parsed Intent: {rag_context.get('intent')}\n"
        prompt += f"- Parsed Preferences: {rag_context.get('preferences')}\n"
        prompt += "- Matched Products:\n"
        for product in rag_context.get("matched_products", [])[:5]:
            prompt += (
                f"  * {product['product_name']} | ${product['price']} | occasion={product['occasion']} "
                f"| category={product['dress_category']} | stock={product['stock']}\n"
            )

        if tool_outputs:
            prompt += "\nSpecialist agent outputs (may be verbose; summarize smartly):\n"
            for idx, output in enumerate(tool_outputs[:4], 1):
                prompt += f"{idx}. {output.get('source')}: {str(output.get('content'))[:1000]}\n"

        prompt += "\nHow to answer:\n"
        prompt += "1) Start with a strong direct answer and recommendations.\n"
        prompt += "2) Use specific products from matched products if available.\n"
        prompt += "3) If something critical is missing, ask at most 1-2 focused questions.\n"
        prompt += "4) End with a clear next step the user can take now.\n"
        return prompt

    def _call_openrouter(self, messages: List[Dict[str, str]]) -> str:
        if not OPENROUTER_API_KEY:
            return ""

=======
        return """You are Clara, a top-tier fashion retail sales associate.

Mission:
- Deliver best-in-class, personalized shopping support.
- Ask sharp follow-up questions when details are missing.
- Guide users from discovery to decision with confidence.

Operating style:
- Be concise but useful.
- Prefer concrete recommendations over generic advice.
- When product data is available, cite exact names, prices, occasions, and stock.
- Offer a clear next step at the end of each response.

Safety / quality:
- Never fabricate stock/order details if not in provided context.
- If information is missing, explicitly ask for it.
- Never mention being an AI model.
"""

    def process(
        self,
        user_message: str,
        history: List[Dict],
        user_context: Dict[str, Any],
        channel: Channel,
    ) -> str:
        """Primary sales response with lightweight tool-enriched context."""
        tool_context = self._build_tool_context(user_message, user_context)
        return self._generate_response(
            user_message=user_message,
            history=history,
            user_context=user_context,
            channel=channel,
            tool_outputs=[tool_context] if tool_context else [],
        )

    def compose_response(
        self,
        user_message: str,
        history: List[Dict],
        user_context: Dict[str, Any],
        channel: Channel,
        tool_outputs: List[Dict[str, Any]],
    ) -> str:
        """Synthesize multi-agent/tool outputs into one polished customer reply."""
        return self._generate_response(
            user_message=user_message,
            history=history,
            user_context=user_context,
            channel=channel,
            tool_outputs=tool_outputs,
        )

    def _generate_response(
        self,
        user_message: str,
        history: List[Dict],
        user_context: Dict[str, Any],
        channel: Channel,
        tool_outputs: List[Dict[str, Any]],
    ) -> str:
        enhanced_prompt = self._build_prompt(user_context, channel, tool_outputs)
        messages = [{"role": "system", "content": enhanced_prompt}]
        messages += history[-12:]
        messages.append({"role": "user", "content": user_message})

        llm_reply = self._call_openrouter(messages)
        if llm_reply:
            return llm_reply

        return self._fallback_response(user_message, user_context, tool_outputs)

    def _build_prompt(
        self,
        user_context: Dict[str, Any],
        channel: Channel,
        tool_outputs: List[Dict[str, Any]],
    ) -> str:
        prompt = self.system_prompt
        prompt += "\nCustomer Context:\n"
        if user_context.get("name"):
            prompt += f"- Name: {user_context['name']}\n"
        if "loyalty_score" in user_context:
            tier = self._get_loyalty_tier(int(user_context.get("loyalty_score", 0)))
            prompt += f"- Loyalty: {tier} ({user_context.get('loyalty_score', 0)} points)\n"
        if user_context.get("past_orders"):
            prompt += f"- Past Orders: {len(user_context['past_orders'])}\n"

        prompt += f"\nChannel: {channel.value}\n"
        if channel == Channel.MOBILE:
            prompt += "Keep formatting compact for mobile.\n"
        elif channel == Channel.WHATSAPP:
            prompt += "Use crisp bullets and natural conversational style.\n"
        elif channel == Channel.KIOSK:
            prompt += "Include in-store try-on / pickup suggestions when relevant.\n"

        if tool_outputs:
            prompt += "\nAgent/Tool Outputs (trusted context):\n"
            for idx, output in enumerate(tool_outputs, 1):
                prompt += f"{idx}. {output.get('source', 'unknown')}: {output.get('content', '')}\n"

        prompt += "\nResponse requirements:\n"
        prompt += "1) Start with direct answer to user intent.\n"
        prompt += "2) Provide specific recommendations or options.\n"
        prompt += "3) End with one clear next-step question.\n"
        return prompt

    def _call_openrouter(self, messages: List[Dict[str, str]]) -> str:
        if not OPENROUTER_API_KEY:
            return ""

>>>>>>> main
        try:
            response = requests.post(
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
<<<<<<< HEAD
                    "temperature": 0.25,
                    "max_tokens": 800,
                },
                timeout=50,
=======
                    "temperature": 0.35,
                    "max_tokens": 650,
                },
                timeout=45,
>>>>>>> main
            )
            if response.status_code != 200:
                return ""

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                return ""
            return (choices[0].get("message", {}).get("content") or "").strip()
        except Exception:
            return ""

<<<<<<< HEAD
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
                "Tell me your occasion, budget, and preferred color, and I’ll shortlist top in-stock options instantly."
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
                "If you like one of these, tell me the product name and quantity and I’ll help you add it to cart and move to checkout."
            )

        return (
            f"Got it, {name}. I can still help you find the right formal option. "
            "Share your budget range and preferred color, and I’ll narrow down the best available dresses for you."
        )
=======
    def _build_tool_context(self, user_message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        message_lower = user_message.lower()
        snippets = []

        # Product snapshot based on simple keyword matching
        products = db.products[:]
        keywords = [token.strip(".,!? ") for token in message_lower.split() if len(token) > 3]
        scored = []
        for product in products:
            haystack = f"{product.get('product_name','')} {product.get('dress_category','')} {product.get('occasion','')} {product.get('description','')}".lower()
            score = sum(1 for kw in keywords if kw in haystack)
            if score > 0:
                scored.append((score, product))
        scored.sort(key=lambda row: row[0], reverse=True)
        top_products = [row[1] for row in scored[:4]] if scored else products[:3]

        if top_products:
            product_lines = []
            for p in top_products:
                product_lines.append(
                    f"{p.get('product_name')} (${p.get('price')}, occasion: {p.get('occasion')}, stock: {p.get('stock')})"
                )
            snippets.append("Candidate products: " + "; ".join(product_lines))

        if user_context.get("user_id"):
            cart = db.get_user_cart(user_context["user_id"])
            if cart:
                cart_total = sum(item["product"]["price"] * item["quantity"] for item in cart)
                snippets.append(f"User cart has {len(cart)} items. Estimated subtotal: ${cart_total:.2f}.")

            orders = db.get_user_orders(user_context["user_id"])
            if orders:
                latest = orders[-1]
                snippets.append(
                    f"Latest order: {latest.get('order_number')} status={latest.get('order_status')} final=${latest.get('final_amount')}"
                )

        if not snippets:
            return {}

        return {
            "source": "database_context",
            "content": " | ".join(snippets),
        }

    def _fallback_response(self, user_message: str, user_context: Dict[str, Any], tool_outputs: List[Dict[str, Any]]) -> str:
        greeting = "Great question"
        if user_context.get("name"):
            greeting = f"Great question, {user_context['name'].split()[0]}"

        context_line = ""
        if tool_outputs:
            snippets = []
            for output in tool_outputs[:3]:
                source = output.get("source", "agent").replace("_", " ").title()
                content = (output.get("content", "") or "").strip()
                if content:
                    snippets.append(f"- {source}: {content}")
            if snippets:
                context_line = "\n\nHere’s what I can see right now:\n" + "\n".join(snippets)

        if any(word in user_message.lower() for word in ["recommend", "suggest", "find", "dress"]):
            return (
                f"{greeting}! I can help you pick the best option by style, occasion, and budget."
                f"{context_line}\n\n"
                "Tell me your occasion + budget + preferred colors, and I’ll shortlist the top choices with exact prices."
            )

        return (
            f"{greeting}! I can help with products, cart, checkout, delivery, loyalty, and support."
            f"{context_line}\n\nWhat would you like to do next?"
        )

    def _get_loyalty_tier(self, score: int) -> str:
        if score >= 500:
            return "Platinum"
        if score >= 200:
            return "Gold"
        if score >= 100:
            return "Silver"
        return "Bronze"
>>>>>>> main
