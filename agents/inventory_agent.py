from typing import Dict, Any, Optional, List
import random
from mongo_database import db

class InventoryAgent:
    async def check_inventory(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Check product availability across channels"""
        
        # Extract product reference from message
        product_id = self._extract_product_reference(user_message)
        
        if not product_id:
            return "I'd be happy to check inventory for you! Could you specify which product you're interested in?"
        
        product = db.get_product(product_id)
        if not product:
            return f"I couldn't find product #{product_id}. Could you check the product number?"

        response = f"**{product['product_name']}** - Inventory Status:\n\n"

        # Check online stock
        online_stock = product['stock']
        response += f"**Online Store:**\n"
        if online_stock > 10:
            response += f"✅ Plenty in stock ({online_stock} units)\n"
        elif online_stock > 0:
            response += f"⚠️ Low stock ({online_stock} units left)\n"
        else:
            response += f"❌ Out of stock\n"
        
        # Simulate store availability (in real app, this would query store APIs)
        store_availability = self._simulate_store_availability(product_id)
        response += f"\n**In-Store Availability:**\n"
        
        for store in store_availability:
            status = "✅ Available" if store['available'] else "❌ Not available"
            response += f"- {store['name']}: {status}"
            if store['available']:
                response += f" (Size: {store['size']})"
            response += "\n"
        
        response += "\n**Options:**\n"
        if online_stock > 0:
            response += "1. Order online for home delivery (2-3 business days)\n"
            response += "2. Order online for in-store pickup\n"
        
        if any(store['available'] for store in store_availability):
            response += "3. Reserve in-store for try-on\n"
            response += "4. Visit store for immediate purchase\n"
        
        if online_stock == 0 and not any(store['available'] for store in store_availability):
            response += "This item is currently out of stock everywhere.\n"
            response += "Would you like me to:\n"
            response += "1. Notify you when it's back in stock?\n"
            response += "2. Suggest similar available items?\n"
        
        return response
    
    def _extract_product_reference(self, message: str) -> Optional[int]:
        """Extract product ID from message"""
        # Simple extraction - in production use proper NLP
        words = message.split()
        for word in words:
            if word.isdigit() and len(word) < 4:  # Simple heuristic
                try:
                    return int(word)
                except:
                    pass
        return None
    
    def _simulate_store_availability(self, product_id: int) -> List[Dict]:
        """Simulate store availability check"""
        stores = [
            {"name": "NYC Flagship", "available": random.choice([True, False]), "size": random.choice(["S", "M", "L"])},
            {"name": "LA Boutique", "available": random.choice([True, False]), "size": random.choice(["S", "M", "L"])},
            {"name": "Chicago Store", "available": random.choice([True, False]), "size": random.choice(["S", "M", "L"])},
            {"name": "Miami Store", "available": random.choice([True, False]), "size": random.choice(["S", "M", "L"])},
        ]
        return stores