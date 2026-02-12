import os
from typing import List, Dict, Any

import requests
from dotenv import load_dotenv

from database import db
from schemas import Channel

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class SalesAgent:
    def __init__(self):
        self.system_prompt = self._create_system_prompt()

    def _create_system_prompt(self) -> str:
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
                    "temperature": 0.35,
                    "max_tokens": 650,
                },
                timeout=45,
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
