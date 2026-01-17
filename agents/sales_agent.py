import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from database import db
from schemas import Channel

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class SalesAgent:
    def __init__(self):
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        return """You are Clara, a top-tier sales associate for a premium fashion retail brand.

Your Goals:
1. Provide exceptional, personalized customer service
2. Understand customer needs through thoughtful questioning
3. Recommend products that match style, occasion, and budget
4. Guide customers smoothly through the buying journey
5. Handle objections gracefully and build trust
6. Maintain conversation continuity across channels

Core Principles:
- Be warm, professional, and fashion-savvy
- Use the customer's name when known
- Reference past purchases and preferences
- Suggest complementary items and bundles
- Clarify sizing and availability proactively
- Guide toward clear next steps (view, try, buy)

Available Actions:
- Browse products by category/occasion
- Check real-time inventory
- Add items to cart
- Process payments
- Schedule delivery/pickup
- Apply loyalty discounts
- Handle returns/exchanges

Never mention you're an AI. You're Clara, the personal shopping assistant."""
    
    def process(self, user_message: str, history: List[Dict], 
                user_context: Dict[str, Any], channel: Channel) -> str:
        """Process sales conversation"""
        
        # Enhance system prompt with user context
        enhanced_prompt = self.system_prompt
        
        if user_context:
            user_info = f"\nCustomer Context:\n"
            if user_context.get("name"):
                user_info += f"- Name: {user_context['name']}\n"
            if user_context.get("loyalty_score"):
                user_info += f"- Loyalty Tier: {self._get_loyalty_tier(user_context['loyalty_score'])}\n"
            if user_context.get("past_orders"):
                user_info += f"- Past Purchases: {len(user_context['past_orders'])} orders\n"
            
            enhanced_prompt += user_info
        
        # Add channel context
        channel_context = f"\nCurrent Channel: {channel.value.upper()}\n"
        if channel == Channel.KIOSK:
            channel_context += "Customer is in-store at a kiosk. Offer try-on availability and store assistance."
        elif channel == Channel.MOBILE:
            channel_context += "Customer is on mobile. Keep responses concise for small screens."
        elif channel == Channel.WHATSAPP:
            channel_context += "Customer is on WhatsApp. Use appropriate emojis and quick responses."
        
        enhanced_prompt += channel_context
        
        # Prepare messages
        messages = [{"role": "system", "content": enhanced_prompt}]
        messages += history
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "Retail Sales Agent"
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data:
                    return data["choices"][0]["message"]["content"]
            
            return "I apologize, but I'm having trouble processing your request. Could you please rephrase or try again?"
            
        except Exception as e:
            return "Our systems seem to be busy at the moment. Please try again in a moment or contact our store directly."
    
    def _get_loyalty_tier(self, score: int) -> str:
        if score >= 500:
            return "Platinum"
        elif score >= 200:
            return "Gold"
        elif score >= 100:
            return "Silver"
        else:
            return "Bronze"