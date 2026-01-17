from typing import Dict, Any
import random
from database import db

class PaymentAgent:
    async def process_payment(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Handle payment processing"""
        
        user_id = user_context.get("user_id")
        if not user_id:
            return "I need to know who you are to process payment. Please log in or provide your account details."
        
        # Get user's cart
        cart_items = db.get_user_cart(user_id)
        if not cart_items:
            return "Your cart is empty. Please add items before checkout."
        
        # Calculate total
        subtotal = sum(item['product']['price'] * item['quantity'] for item in cart_items)
        tax = subtotal * 0.08
        shipping = 0 if subtotal >= 100 else 9.99
        total = subtotal + tax + shipping
        
        # Apply loyalty discount if applicable
        user = db.get_user(user_id)
        loyalty_discount = min(user['loyalty_score'] * 0.01, 50)  # 1 point = $0.01, max $50
        final_total = max(0, total - loyalty_discount)
        
        response = f"**Order Summary:**\n\n"
        for item in cart_items:
            response += f"- {item['quantity']}x {item['product']['product_name']}: ${item['product']['price'] * item['quantity']:.2f}\n"
        
        response += f"\nSubtotal: ${subtotal:.2f}\n"
        response += f"Tax (8%): ${tax:.2f}\n"
        response += f"Shipping: ${shipping:.2f}\n"
        if loyalty_discount > 0:
            response += f"Loyalty Discount: -${loyalty_discount:.2f}\n"
        response += f"**Total: ${final_total:.2f}**\n\n"
        
        # Simulate payment methods
        payment_methods = ["Credit Card", "PayPal", "Apple Pay", "Google Pay", "Store Credit"]
        saved_methods = ["Visa ****1234", "PayPal (john@example.com)"]
        
        response += "**Available Payment Methods:**\n"
        for method in payment_methods:
            response += f"- {method}\n"
        
        response += "\n**Your Saved Methods:**\n"
        for method in saved_methods:
            response += f"- {method}\n"
        
        response += "\nHow would you like to pay? You can also say 'use loyalty points' or 'apply coupon'."
        
        return response
    
    async def execute_payment(self, user_id: int, payment_method: str, amount: float) -> Dict[str, Any]:
        """Execute payment (simulated)"""
        
        # Simulate payment processing
        success_rate = 0.95  # 95% success rate
        
        if random.random() < success_rate:
            transaction_id = f"txn_{random.randint(100000, 999999)}"
            
            # Update user loyalty points
            points_earned = int(amount * 10)  # 10 points per dollar
            db.update_user_loyalty(user_id, points_earned)
            
            return {
                "success": True,
                "transaction_id": transaction_id,
                "amount_charged": amount,
                "points_earned": points_earned,
                "message": "Payment successful!"
            }
        else:
            return {
                "success": False,
                "error_code": "DECLINED",
                "message": "Payment declined. Please try another payment method."
            }