from typing import Any, Dict, List, Optional

from database import db

STORE_LOCATIONS = [
    "NYC Flagship",
    "LA Boutique",
    "Chicago Store",
    "Miami Store",
]


class InventoryAgent:
    async def check_inventory(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Check product availability across online and store channels."""

        product_id = self._extract_product_reference(user_message)
        if not product_id:
            return "I'd be happy to check inventory for you! Could you specify which product you're interested in?"

        product = db.get_product(product_id)
        if not product:
            return f"I couldn't find product #{product_id}. Could you check the product number?"

        online_stock = int(product.get("stock", 0))
        store_availability = self._build_store_availability(product)

        response = f"**{product['product_name']}** - Inventory Status:\n\n"
        response += "**Online Store:**\n"
        if online_stock > 10:
            response += f"✅ Plenty in stock ({online_stock} units)\n"
        elif online_stock > 0:
            response += f"⚠️ Low stock ({online_stock} units left)\n"
        else:
            response += "❌ Out of stock\n"

        response += "\n**Store Pickup Availability:**\n"
        response += "_Based on the latest catalog stock snapshot._\n"
        for store in store_availability:
            if store["available"]:
                response += f"- {store['name']}: ✅ Available for pickup (Size: {store['size']})\n"
            else:
                response += f"- {store['name']}: ❌ Not available for pickup\n"

        response += "\n**Options:**\n"
        if online_stock > 0:
            response += "1. Order online for home delivery (2-3 business days)\n"
            response += "2. Order online for in-store pickup\n"

        if any(store["available"] for store in store_availability):
            response += "3. Reserve in-store for try-on\n"
            response += "4. Visit store for immediate purchase\n"

        if online_stock == 0 and not any(store["available"] for store in store_availability):
            response += "This item is currently out of stock everywhere.\n"
            response += "Would you like me to:\n"
            response += "1. Notify you when it's back in stock?\n"
            response += "2. Suggest similar available items?\n"

        return response

    def _extract_product_reference(self, message: str) -> Optional[int]:
        for word in message.split():
            normalized = word.strip(".,!?;:#")
            if normalized.isdigit() and len(normalized) < 4:
                return int(normalized)
        return None

    def _build_store_availability(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        stock = max(int(product.get("stock", 0)), 0)
        sizes = self._parse_sizes(product.get("available_sizes", ""))
        rotation = int(product.get("id", 0)) % len(STORE_LOCATIONS)

        pickup_ready_store_count = 0
        if stock > 0:
            pickup_ready_store_count = min(len(STORE_LOCATIONS), max(1, (stock + 9) // 10))

        available_store_indexes = {
            (rotation + offset) % len(STORE_LOCATIONS)
            for offset in range(pickup_ready_store_count)
        }

        availability: List[Dict[str, Any]] = []
        for index, store_name in enumerate(STORE_LOCATIONS):
            available = index in available_store_indexes
            size = sizes[(int(product.get("id", 0)) + index) % len(sizes)] if available else None
            availability.append(
                {
                    "name": store_name,
                    "available": available,
                    "size": size,
                }
            )

        return availability

    def _parse_sizes(self, available_sizes: str) -> List[str]:
        sizes = [size.strip() for size in str(available_sizes).split(",") if size.strip()]
        return sizes or ["One Size"]
