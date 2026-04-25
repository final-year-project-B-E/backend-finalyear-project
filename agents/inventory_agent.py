from typing import Any, Dict, List, Optional

from database import db


class InventoryAgent:
    async def check_inventory(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Check product availability using the fields stored in the catalog."""

        product_id = self._extract_product_reference(user_message)
        if not product_id:
            return "I'd be happy to check inventory for you! Could you specify which product you're interested in?"

        product = db.get_product(product_id)
        if not product:
            return f"I couldn't find product #{product_id}. Could you check the product number?"

        online_stock = int(product.get("stock", 0))
        size_options = self._parse_sizes(product.get("available_sizes", ""))
        store_availability = self._read_store_availability(product)

        response = f"**{product['product_name']}** - Inventory Status:\n\n"
        response += "**Online Store:**\n"
        if online_stock > 10:
            response += f"✅ Plenty in stock ({online_stock} units)\n"
        elif online_stock > 0:
            response += f"⚠️ Low stock ({online_stock} units left)\n"
        else:
            response += "❌ Out of stock\n"

        if size_options:
            response += f"Available Sizes: {', '.join(size_options)}\n"

        response += "\n**Store Pickup Availability:**\n"
        if store_availability:
            response += "_Based on store-level inventory stored in the product catalog._\n"
            for store in store_availability:
                if store["available"]:
                    response += f"- {store['name']}: ✅ Available"
                    if store.get("size"):
                        response += f" (Size: {store['size']})"
                    response += "\n"
                else:
                    response += f"- {store['name']}: ❌ Not available\n"
        else:
            response += (
                "Store-level availability is not stored in the current product catalog. "
                "I can confirm online stock, but not branch-by-branch pickup inventory.\n"
            )

        response += "\n**Options:**\n"
        if online_stock > 0:
            response += "1. Order online for home delivery (2-3 business days)\n"
            if store_availability:
                response += "2. Order online for in-store pickup\n"

        if any(store["available"] for store in store_availability):
            response += "3. Reserve in-store for try-on\n"
            response += "4. Visit store for immediate purchase\n"

        if online_stock == 0 and not any(store["available"] for store in store_availability):
            response += "This item is currently unavailable for online purchase.\n"
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

    def _parse_sizes(self, available_sizes: Any) -> List[str]:
        sizes = [size.strip() for size in str(available_sizes).split(",") if size.strip()]
        return sizes

    def _read_store_availability(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        store_fields = [
            product.get("stores"),
            product.get("locations"),
            product.get("stock_by_location"),
            product.get("availability"),
            product.get("inventory"),
        ]
        for field_value in store_fields:
            parsed = self._normalize_store_records(field_value)
            if parsed:
                return parsed
        return []

    def _normalize_store_records(self, raw_value: Any) -> List[Dict[str, Any]]:
        if isinstance(raw_value, list):
            normalized: List[Dict[str, Any]] = []
            for item in raw_value:
                if isinstance(item, dict):
                    normalized_item = self._normalize_store_dict(item)
                    if normalized_item:
                        normalized.append(normalized_item)
            return normalized

        if isinstance(raw_value, dict):
            normalized: List[Dict[str, Any]] = []
            for name, value in raw_value.items():
                if isinstance(value, dict):
                    record = self._normalize_store_dict({"name": name, **value})
                else:
                    record = self._normalize_store_dict({"name": name, "stock": value})
                if record:
                    normalized.append(record)
            return normalized

        return []

    def _normalize_store_dict(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        name = item.get("name") or item.get("store") or item.get("location") or item.get("city")
        if not name:
            return None

        stock_value = item.get("stock")
        if stock_value is None:
            stock_value = item.get("quantity")
        if stock_value is None and "available" in item:
            available = bool(item.get("available"))
        else:
            try:
                available = int(stock_value or 0) > 0
            except (TypeError, ValueError):
                available = bool(stock_value)

        size = item.get("size") or item.get("sizes")
        if isinstance(size, list):
            size = ", ".join(str(entry) for entry in size if entry)

        return {
            "name": str(name),
            "available": available,
            "size": size,
        }
