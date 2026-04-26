import os
import re
import logging
from typing import List, Dict, Any, Optional
import numpy as np

import requests
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from database import db
from schemas import Channel

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/sfree")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
logger = logging.getLogger(__name__)

# Initialize embedding model globally (lazy load)
_embedding_model = None
def get_embedding_model():
    global _embedding_model
    if _embedding_model is None and EMBEDDINGS_AVAILABLE:
        try:
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence-Transformer model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")
    return _embedding_model


class SalesAgent:
    def __init__(self):
        self.system_prompt = self._create_system_prompt()

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
                f"| category={product['dress_category']} | stock={product['stock']} "
                f"| colors={product.get('colors', '')} | sizes={product.get('available_sizes', '')} "
                f"| material={product.get('material', '')} | description={product.get('description', '')[:120]}\n"
            )

        if tool_outputs:
            prompt += "\nSpecialist agent outputs (may be verbose; summarize smartly):\n"
            for idx, output in enumerate(tool_outputs[:4], 1):
                prompt += f"{idx}. {output.get('source')}: {str(output.get('content'))[:1000]}\n"

        prompt += "\nHow to answer:\n"
        prompt += "1) Start with a strong direct answer and recommendations.\n"
        prompt += "2) Use specific products from matched products if available.\n"
        prompt += "2a) If matched products exist, never say the catalog has no relevant items.\n"
        prompt += "2b) Respect gender/category intent strictly when products are matched, especially men/women/kids.\n"
        prompt += "3) If something critical is missing, ask at most 1-2 focused questions.\n"
        prompt += "4) End with a clear next step the user can take now.\n"
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
                    "temperature": 0.25,
                    "max_tokens": 800,
                },
                timeout=50,
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

    def _build_rag_context(self, user_message: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        preferences = self._extract_preferences(user_message, user_context)
        matched_products = self._retrieve_products(preferences)
        intent = self._infer_intent(user_message)

        logger.info(
            "SalesAgent RAG | message=%r | preferences=%s | matched=%s",
            user_message,
            preferences,
            [
                {
                    "id": product.get("id"),
                    "name": product.get("product_name"),
                    "category": product.get("dress_category"),
                    "occasion": product.get("occasion"),
                    "price": product.get("price"),
                }
                for product in matched_products[:5]
            ],
        )

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

        # PHASE 1: Enhanced occasion matching with fuzzy matching
        occasion_keywords = {
            "Formal": ["wedding", "gala", "prom", "formal", "black-tie", "elegant"],
            "Business": ["office", "business", "work", "professional", "meeting"],
            "Casual": ["casual", "everyday", "weekend", "relaxed", "chill"],
            "Party": ["party", "night-out", "club", "celebration", "birthday"],
            "Date": ["date", "date-night", "dinner", "romantic"],
            "Athletic": ["gym", "workout", "athletic", "sports", "training"],
        }
        
        for occasion, keywords in occasion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    preferences["occasion"] = occasion
                    break
            if "occasion" in preferences:
                break

        # PHASE 1: Enhanced price extraction
        budget_match = re.search(r"(?:under|below|less than|upto|up to)\s*\$?(\d+(?:\.\d+)?)", text)
        if budget_match:
            preferences["max_price"] = float(budget_match.group(1))

        price_range = re.search(r"\$?(\d+(?:\.\d+)?)\s*(?:to|\-|–)\s*\$?(\d+(?:\.\d+)?)", text)
        if price_range:
            low, high = float(price_range.group(1)), float(price_range.group(2))
            preferences["min_price"] = min(low, high)
            preferences["max_price"] = max(low, high)

        # PHASE 1: Enhanced fuzzy color matching
        color_palette = {
            "black": ["black", "jet", "ebony", "charcoal"],
            "white": ["white", "cream", "ivory", "pearl"],
            "blue": ["blue", "navy", "aqua", "cyan", "cobalt", "teal", "azure", "sapphire"],
            "red": ["red", "crimson", "scarlet", "maroon", "burgundy"],
            "green": ["green", "emerald", "forest", "mint", "lime", "sage"],
            "pink": ["pink", "rose", "magenta", "fuchsia", "coral", "blush"],
            "purple": ["purple", "violet", "lavender", "plum"],
            "beige": ["beige", "tan", "taupe", "khaki", "sand"],
            "gold": ["gold", "yellow", "golden", "amber"],
            "silver": ["silver", "gray", "grey", "metallic"],
            "brown": ["brown", "chocolate", "bronze", "tan"],
            "orange": ["orange", "peach", "apricot"],
        }
        
        found_colors = []
        for base_color, variations in color_palette.items():
            for variation in variations:
                if variation in text:
                    found_colors.append(base_color)
                    break
        
        if found_colors:
            preferences["colors"] = list(set(found_colors))

        # PHASE 1: Enhanced category matching with fuzzy matching
        category_keywords = {
            "men": ["men", "men's", "mens", "male", "gentlemen", "guy"],
            "women": ["women", "women's", "womens", "female", "ladies", "girl"],
            "kids": ["kids", "kid", "children", "boys", "girls", "baby", "toddler"],
        }
        for category_prefix, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                preferences["category_prefix"] = category_prefix
                break

        category_terms = {
            "suit": ["suit", "suits", "blazer", "blazers", "tuxedo"],
            "shirt": ["shirt", "shirts", "tee", "polo"],
            "dress": ["dress", "dresses", "gown", "gowns", "frock"],
            "top": ["top", "tops", "blouse", "blouses", "tank", "tunic"],
            "outerwear": ["jacket", "jackets", "coat", "coats", "outerwear", "hoodie", "sweater"],
            "pants": ["pants", "trousers", "jeans", "shorts", "leggings", "skirt"],
            "traditional": ["kurta", "saree", "lehenga", "ethnic", "traditional", "desi"],
        }
        matched_terms = [
            category_name
            for category_name, keywords in category_terms.items()
            if any(keyword in text for keyword in keywords)
        ]
        if matched_terms:
            preferences["category_terms"] = matched_terms

        # PHASE 1: Enhanced search terms extraction (exclude more stop words)
        tokens = re.findall(r"[a-zA-Z]+", text)
        stop_words = {
            "show", "me", "for", "with", "the", "and", "wear", "something", "need",
            "want", "looking", "look", "outfit", "formal", "casual", "party", "wedding",
            "mens", "men", "womens", "women", "kids", "kid", "dress", "shirt", "top",
            "a", "an", "or", "but", "is", "are", "in", "of", "to", "from", "by",
        }
        search_terms = [
            token for token in tokens
            if len(token) > 2 and token not in stop_words
        ]
        if search_terms:
            preferences["search_terms"] = search_terms[:8]  # Increased from 6

        # PHASE 1: Extract material preferences
        materials = ["cotton", "silk", "linen", "wool", "polyester", "denim", "leather", "velvet", "satin"]
        found_materials = [mat for mat in materials if mat in text]
        if found_materials:
            preferences["materials"] = found_materials

        # PHASE 1: Extract fit preferences
        fits = ["slim", "regular", "loose", "oversized", "tight", "fitted"]
        found_fits = [fit for fit in fits if fit in text]
        if found_fits:
            preferences["fits"] = found_fits

        # Use user context for additional preferences
        if user_context.get("style_preferences") and "colors" not in preferences:
            preferences["colors"] = user_context["style_preferences"].get("colors", [])

        return preferences

    def _retrieve_products(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        PHASE 1 + 2: Hybrid retrieval with fuzzy matching, popularity, and semantic search
        """
        products = db.get_all_products()

        occasion = preferences.get("occasion")
        min_price = preferences.get("min_price")
        max_price = preferences.get("max_price")
        colors = preferences.get("colors", [])
        category_prefix = preferences.get("category_prefix")
        category_terms = preferences.get("category_terms", [])
        search_terms = preferences.get("search_terms", [])
        materials = preferences.get("materials", [])
        fits = preferences.get("fits", [])

        # PHASE 2: Prepare for semantic search if embeddings available
        embedding_model = get_embedding_model()
        query_text = self._build_search_query_text(preferences)
        query_embedding = None
        
        if embedding_model and query_text:
            try:
                query_embedding = embedding_model.encode(query_text, convert_to_numpy=True)
            except Exception as e:
                logger.warning(f"Failed to encode query: {e}")

        scored: List[tuple[int, Dict[str, Any]]] = []
        
        for product in products:
            score = 0
            product_name = str(product.get("product_name", "")).lower()
            product_category = str(product.get("dress_category", "")).lower()
            product_description = str(product.get("description", "")).lower()
            product_colors_str = str(product.get("colors", "")).lower()
            product_material = str(product.get("material", "")).lower()
            product_sizes = str(product.get("available_sizes", "")).lower()
            
            # PHASE 1: Fuzzy category matching (70% threshold)
            if category_prefix:
                if product_category.startswith(f"{category_prefix}-"):
                    score += 8  # Increased from 6
                elif fuzz.partial_ratio(product_category, category_prefix) >= 70:
                    score += 5  # Partial match bonus

            # PHASE 1: Category term matching with fuzzy matching
            if category_terms:
                for term in category_terms:
                    if term in product_category or term in product_name:
                        score += 5
                    elif fuzz.token_set_ratio(term, product_name) >= 80:
                        score += 3  # Fuzzy match bonus

            # Occasion matching
            if occasion and str(product.get("occasion", "")).lower() == occasion.lower():
                score += 5

            # PHASE 1: Price matching (refined)
            if min_price is not None and product.get("price", 0) >= min_price:
                score += 1
            if max_price is not None and product.get("price", 0) <= max_price:
                score += 2

            # PHASE 1: Enhanced color matching with fuzzy matching
            if colors:
                for color in colors:
                    if color in product_colors_str:
                        score += 3
                    else:
                        # Fuzzy matching for color names
                        for prod_color in product_colors_str.split(','):
                            prod_color = prod_color.strip()
                            if fuzz.ratio(color, prod_color) >= 75:
                                score += 2
                                break

            # PHASE 1: Material matching
            if materials:
                for material in materials:
                    if material in product_material:
                        score += 2
                    elif fuzz.token_set_ratio(material, product_material) >= 75:
                        score += 1

            # PHASE 1: Fit preference matching
            if fits:
                for fit in fits:
                    if fit in product_description or fit in product_category:
                        score += 2

            # PHASE 1: Enhanced search term matching across multiple fields
            if search_terms:
                for term in search_terms:
                    # High priority: product name
                    if term in product_name:
                        score += 4
                    # Medium priority: category and description
                    elif term in product_category or term in product_description:
                        score += 2
                    # Low priority: sizes and material
                    elif term in product_sizes or term in product_material:
                        score += 1
                    # Fuzzy matching for slight misspellings
                    elif fuzz.ratio(term, product_name) >= 80:
                        score += 2

            # PHASE 1: Stock and popularity scoring
            stock = product.get("stock", 0)
            if stock > 0:
                score += 2
                # PHASE 1: Boost popular items
                view_count = product.get("view_count", 0)
                if view_count > 100:
                    score += 3
                elif view_count > 50:
                    score += 2
                elif view_count > 10:
                    score += 1
            else:
                score -= 2  # Penalize out of stock

            # Featured product bonus
            if product.get("featured_dress"):
                score += 2

            # PHASE 2: Semantic similarity scoring (if embeddings available)
            if embedding_model and query_embedding is not None:
                try:
                    product_desc_for_embed = f"{product_name} {product_category} {product_description}"
                    product_embedding = embedding_model.encode(product_desc_for_embed, convert_to_numpy=True)
                    similarity = cosine_similarity([query_embedding], [product_embedding])[0][0]
                    # Scale similarity to 0-5 range and add to score
                    semantic_score = int(similarity * 5)
                    score += semantic_score
                except Exception as e:
                    logger.debug(f"Semantic search failed for product {product.get('id')}: {e}")

            # Only include products with meaningful scores or basic filters met
            if (occasion or min_price is not None or max_price is not None or colors or 
                category_prefix or category_terms or search_terms or materials or fits):
                if score > 0:
                    scored.append((score, product))
            else:
                scored.append((score, product))

        # Sort by score (descending) and stock (descending)
        scored.sort(key=lambda row: (row[0], row[1].get("stock", 0)), reverse=True)
        
        matched_products = [row[1] for row in scored[:6]]
        
        # Track view count for popularity (PHASE 1)
        for product in matched_products:
            product_id = product.get("id")
            if product_id:
                db.increment_product_view_count(product_id)
        
        return matched_products

    def _build_search_query_text(self, preferences: Dict[str, Any]) -> str:
        """
        Build a combined text representation for semantic search
        """
        parts = []
        
        if preferences.get("occasion"):
            parts.append(f"occasion {preferences['occasion']}")
        
        if preferences.get("colors"):
            parts.append(f"color {' '.join(preferences['colors'])}")
        
        if preferences.get("category_terms"):
            parts.append(f"type {' '.join(preferences['category_terms'])}")
        
        if preferences.get("materials"):
            parts.append(f"material {' '.join(preferences['materials'])}")
        
        if preferences.get("fits"):
            parts.append(f"fit {' '.join(preferences['fits'])}")
        
        if preferences.get("search_terms"):
            parts.append(' '.join(preferences['search_terms']))
        
        return ' '.join(parts)

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

        if preferences.get("category_prefix") == "men" and preferences.get("occasion", "").lower() == "formal":
            return (
                f"I could not confidently rank the men's formal catalog for you just yet, {name}, "
                "but I should be looking at items like men's shirts and blazers. "
                "Tell me your budget or whether you want a shirt, blazer, or full outfit, and I'll narrow it down."
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
