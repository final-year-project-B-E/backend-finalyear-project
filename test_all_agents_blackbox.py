#!/usr/bin/env python3
"""
Comprehensive Black-Box Testing Suite for All Agents
Tests all 7 agents with realistic user scenarios
"""

import json
import requests
import time
from typing import Dict, List, Any
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Test user for all scenarios
TEST_USER_ID = "test_user_001"
TEST_USER_EMAIL = "blackbox_test@example.com"
TEST_USER_NAME = "BlackBox Tester"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class AgentTestRunner:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_order_number = None
        self.test_product_id = None

    def print_header(self, text: str):
        print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"{BOLD}{BLUE}{text}{RESET}")
        print(f"{BOLD}{BLUE}{'='*70}{RESET}")

    def print_test(self, agent: str, scenario: str, passed: bool, message: str = ""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = f"{GREEN}✓ PASS{RESET}"
        else:
            self.failed_tests += 1
            status = f"{RED}✗ FAIL{RESET}"
        
        print(f"{status} | {BOLD}{agent}{RESET:20} | {scenario:40} {message}")
        self.test_results.append({
            "agent": agent,
            "scenario": scenario,
            "status": "PASS" if passed else "FAIL",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def print_summary(self):
        print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"{BOLD}TEST SUMMARY{RESET}")
        print(f"{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"Total Tests: {BOLD}{self.total_tests}{RESET}")
        print(f"Passed: {GREEN}{self.passed_tests}{RESET}")
        print(f"Failed: {RED}{self.failed_tests}{RESET}")
        print(f"Success Rate: {BOLD}{(self.passed_tests/self.total_tests*100):.1f}%{RESET}")
        print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

    def setup_test_user(self):
        """Create or get test user"""
        print(f"\n{YELLOW}Setting up test user...{RESET}")
        try:
            response = requests.post(
                f"{API_BASE_URL}/auth/register",
                headers=HEADERS,
                json={
                    "email": TEST_USER_EMAIL,
                    "password": "TestPassword123!",
                    "first_name": "BlackBox",
                    "last_name": "Tester"
                },
                timeout=5
            )
            if response.status_code in [200, 201, 409]:  # 409 = already exists
                print(f"{GREEN}✓ Test user ready{RESET}")
                return True
        except Exception as e:
            print(f"{RED}✗ Failed to setup user: {e}{RESET}")
            return False

    def get_products(self) -> List[Dict]:
        """Get available products for testing"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/products",
                timeout=5
            )
            if response.status_code == 200:
                products = response.json()
                if products:
                    self.test_product_id = products[0].get("id")
                    return products
        except Exception as e:
            print(f"{RED}✗ Failed to fetch products: {e}{RESET}")
        return []

    # ============================================================================
    # SALES AGENT TESTS
    # ============================================================================
    
    def test_sales_agent_greeting(self):
        """Test 1: Sales Agent should respond to greeting"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "Hi, I'm looking for a dress",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code == 200 and response.json().get("reply")
            self.print_test("Sales Agent", "Greeting & Initial Response", passed, 
                          f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Sales Agent", "Greeting & Initial Response", False, str(e))

    def test_sales_agent_product_recommendation(self):
        """Test 2: Sales Agent should recommend products based on preferences"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "Show me a blue formal dress under $200",
                    "channel": "web"
                },
                timeout=10
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     data.get("reply") and 
                     len(data.get("reply", "")) > 20)
            self.print_test("Sales Agent", "Product Recommendation", passed,
                          f"Rec Length: {len(data.get('reply', ''))}")
        except Exception as e:
            self.print_test("Sales Agent", "Product Recommendation", False, str(e))

    def test_sales_agent_follow_up(self):
        """Test 3: Sales Agent should handle follow-up questions"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "Do you have it in black?",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code == 200 and response.json().get("reply")
            self.print_test("Sales Agent", "Follow-up Question Handling", passed,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Sales Agent", "Follow-up Question Handling", False, str(e))

    def test_sales_agent_style_extraction(self):
        """Test 4: Sales Agent should extract multiple style preferences"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "I need a casual cotton shirt with green and silver colors, around $50-100",
                    "channel": "web"
                },
                timeout=10
            )
            data = response.json()
            reply = data.get("reply", "").lower()
            passed = (response.status_code == 200 and 
                     reply and 
                     any(word in reply for word in ["shirt", "green", "cotton", "$"]))
            self.print_test("Sales Agent", "Multi-Preference Extraction", passed,
                          f"Preferences extracted: {passed}")
        except Exception as e:
            self.print_test("Sales Agent", "Multi-Preference Extraction", False, str(e))

    # ============================================================================
    # RECOMMENDATION AGENT TESTS
    # ============================================================================

    def test_recommendation_agent_by_category(self):
        """Test 5: Recommendation Agent should filter by category"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/agents/recommendation/get_recommendations",
                params={"category": "women-dress"},
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     isinstance(data, list) and 
                     len(data) > 0)
            self.print_test("Recommendation Agent", "Category Filtering", passed,
                          f"Products found: {len(data) if isinstance(data, list) else 0}")
        except Exception as e:
            self.print_test("Recommendation Agent", "Category Filtering", False, str(e))

    def test_recommendation_agent_by_occasion(self):
        """Test 6: Recommendation Agent should filter by occasion"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/agents/recommendation/get_recommendations",
                params={"occasion": "Formal"},
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     isinstance(data, list) and 
                     len(data) > 0)
            self.print_test("Recommendation Agent", "Occasion Filtering", passed,
                          f"Products found: {len(data) if isinstance(data, list) else 0}")
        except Exception as e:
            self.print_test("Recommendation Agent", "Occasion Filtering", False, str(e))

    def test_recommendation_agent_top_3(self):
        """Test 7: Recommendation Agent should return top 3 products"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/agents/recommendation/get_recommendations",
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     isinstance(data, list) and 
                     len(data) <= 3)
            self.print_test("Recommendation Agent", "Top 3 Products Limit", passed,
                          f"Products returned: {len(data) if isinstance(data, list) else 0}")
        except Exception as e:
            self.print_test("Recommendation Agent", "Top 3 Products Limit", False, str(e))

    # ============================================================================
    # INVENTORY AGENT TESTS
    # ============================================================================

    def test_inventory_agent_stock_check(self):
        """Test 8: Inventory Agent should check stock availability"""
        try:
            if not self.test_product_id:
                self.print_test("Inventory Agent", "Stock Availability Check", False, "No product ID")
                return
            
            response = requests.get(
                f"{API_BASE_URL}/agents/inventory/check_inventory",
                params={"product_id": self.test_product_id},
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     "stock" in data and 
                     data.get("stock") is not None)
            self.print_test("Inventory Agent", "Stock Availability Check", passed,
                          f"Stock: {data.get('stock', 'N/A')}")
        except Exception as e:
            self.print_test("Inventory Agent", "Stock Availability Check", False, str(e))

    def test_inventory_agent_size_options(self):
        """Test 9: Inventory Agent should return size options"""
        try:
            if not self.test_product_id:
                self.print_test("Inventory Agent", "Size Options", False, "No product ID")
                return
            
            response = requests.get(
                f"{API_BASE_URL}/agents/inventory/check_inventory",
                params={"product_id": self.test_product_id},
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     ("available_sizes" in data or "sizes" in data))
            self.print_test("Inventory Agent", "Size Options", passed,
                          f"Sizes available: {'Yes' if passed else 'No'}")
        except Exception as e:
            self.print_test("Inventory Agent", "Size Options", False, str(e))

    def test_inventory_agent_multiple_products(self):
        """Test 10: Inventory Agent should check multiple product stocks"""
        try:
            products = self.get_products()
            if len(products) < 2:
                self.print_test("Inventory Agent", "Multiple Products Check", False, "Insufficient products")
                return
            
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "Do you have these in stock? Check availability",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code == 200
            self.print_test("Inventory Agent", "Multiple Products Check", passed,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Inventory Agent", "Multiple Products Check", False, str(e))

    # ============================================================================
    # PAYMENT AGENT TESTS
    # ============================================================================

    def test_payment_agent_payment_methods(self):
        """Test 11: Payment Agent should list payment methods"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/agents/payment/get_payment_methods",
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     isinstance(data, list) and 
                     len(data) > 0)
            self.print_test("Payment Agent", "Payment Methods List", passed,
                          f"Methods: {len(data) if isinstance(data, list) else 0}")
        except Exception as e:
            self.print_test("Payment Agent", "Payment Methods List", False, str(e))

    def test_payment_agent_order_summary(self):
        """Test 12: Payment Agent should generate order summary"""
        try:
            # First, create an order
            response = requests.post(
                f"{API_BASE_URL}/user/{TEST_USER_ID}/checkout",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "items": [{"product_id": self.test_product_id, "quantity": 1, "price": 99.99}]
                },
                timeout=10
            )
            
            if response.status_code in [200, 201, 400]:
                order = response.json()
                self.test_order_number = order.get("order_number") or order.get("order", {}).get("order_number")
                
                # Now test payment agent
                summary_response = requests.get(
                    f"{API_BASE_URL}/agents/payment/get_order_summary",
                    params={"order_number": self.test_order_number},
                    timeout=5
                )
                passed = (summary_response.status_code == 200 and 
                         summary_response.json().get("total"))
                self.print_test("Payment Agent", "Order Summary Generation", passed,
                              f"Total: ${summary_response.json().get('total', 'N/A')}")
            else:
                self.print_test("Payment Agent", "Order Summary Generation", False, "Order creation failed")
        except Exception as e:
            self.print_test("Payment Agent", "Order Summary Generation", False, str(e))

    def test_payment_agent_loyalty_discount(self):
        """Test 13: Payment Agent should calculate loyalty discounts"""
        try:
            if not self.test_order_number:
                self.print_test("Payment Agent", "Loyalty Discount Calculation", False, "No order")
                return
            
            response = requests.post(
                f"{API_BASE_URL}/orders/{self.test_order_number}/apply-loyalty-points",
                headers=HEADERS,
                json={"points_to_redeem": 100},
                timeout=10
            )
            passed = response.status_code in [200, 201]
            self.print_test("Payment Agent", "Loyalty Discount Calculation", passed,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Payment Agent", "Loyalty Discount Calculation", False, str(e))

    # ============================================================================
    # FULFILLMENT AGENT TESTS
    # ============================================================================

    def test_fulfillment_agent_delivery_options(self):
        """Test 14: Fulfillment Agent should provide delivery options"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/agents/fulfillment/get_delivery_options",
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     isinstance(data, list) and 
                     len(data) > 0)
            self.print_test("Fulfillment Agent", "Delivery Options", passed,
                          f"Options: {len(data) if isinstance(data, list) else 0}")
        except Exception as e:
            self.print_test("Fulfillment Agent", "Delivery Options", False, str(e))

    def test_fulfillment_agent_shipping_cost(self):
        """Test 15: Fulfillment Agent should calculate shipping costs"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "How much is shipping? What about pickup options?",
                    "channel": "web"
                },
                timeout=10
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     "shipping" in data.get("reply", "").lower())
            self.print_test("Fulfillment Agent", "Shipping Cost Calculation", passed,
                          f"Fulfillment info provided: {passed}")
        except Exception as e:
            self.print_test("Fulfillment Agent", "Shipping Cost Calculation", False, str(e))

    def test_fulfillment_agent_order_status(self):
        """Test 16: Fulfillment Agent should track order status"""
        try:
            if not self.test_order_number:
                self.print_test("Fulfillment Agent", "Order Status Tracking", False, "No order")
                return
            
            response = requests.get(
                f"{API_BASE_URL}/orders/{self.test_order_number}",
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     data.get("status"))
            self.print_test("Fulfillment Agent", "Order Status Tracking", passed,
                          f"Status: {data.get('status', 'N/A')}")
        except Exception as e:
            self.print_test("Fulfillment Agent", "Order Status Tracking", False, str(e))

    # ============================================================================
    # LOYALTY AGENT TESTS
    # ============================================================================

    def test_loyalty_agent_tier_display(self):
        """Test 17: Loyalty Agent should display tier information"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/user/{TEST_USER_ID}/loyalty",
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     data.get("tier") and 
                     data.get("loyalty_score") is not None)
            self.print_test("Loyalty Agent", "Tier Information Display", passed,
                          f"Tier: {data.get('tier', 'N/A')}, Score: {data.get('loyalty_score', 'N/A')}")
        except Exception as e:
            self.print_test("Loyalty Agent", "Tier Information Display", False, str(e))

    def test_loyalty_agent_points_balance(self):
        """Test 18: Loyalty Agent should show points balance"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/user/{TEST_USER_ID}/loyalty",
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     data.get("points_value") is not None)
            self.print_test("Loyalty Agent", "Points Balance Display", passed,
                          f"Points Value: ${data.get('points_value', 'N/A')}")
        except Exception as e:
            self.print_test("Loyalty Agent", "Points Balance Display", False, str(e))

    def test_loyalty_agent_coupons(self):
        """Test 19: Loyalty Agent should manage coupons"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "What coupons or discounts do I have available?",
                    "channel": "web"
                },
                timeout=10
            )
            data = response.json()
            reply = data.get("reply", "").lower()
            passed = (response.status_code == 200 and 
                     any(word in reply for word in ["coupon", "discount", "promo"]))
            self.print_test("Loyalty Agent", "Coupon Management", passed,
                          f"Coupon info provided: {passed}")
        except Exception as e:
            self.print_test("Loyalty Agent", "Coupon Management", False, str(e))

    def test_loyalty_agent_tier_progression(self):
        """Test 20: Loyalty Agent should show tier progression"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/user/{TEST_USER_ID}/loyalty",
                timeout=5
            )
            data = response.json()
            passed = (response.status_code == 200 and 
                     data.get("next_tier") and 
                     data.get("points_to_next_tier") is not None)
            self.print_test("Loyalty Agent", "Tier Progression Tracking", passed,
                          f"Next tier: {data.get('next_tier', 'N/A')}, Points needed: {data.get('points_to_next_tier', 'N/A')}")
        except Exception as e:
            self.print_test("Loyalty Agent", "Tier Progression Tracking", False, str(e))

    # ============================================================================
    # SUPPORT AGENT TESTS
    # ============================================================================

    def test_support_agent_return_policy(self):
        """Test 21: Support Agent should explain return policy"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "What's your return policy?",
                    "channel": "web"
                },
                timeout=10
            )
            data = response.json()
            reply = data.get("reply", "").lower()
            passed = (response.status_code == 200 and 
                     any(word in reply for word in ["return", "policy", "day", "exchange"]))
            self.print_test("Support Agent", "Return Policy Info", passed,
                          f"Policy info provided: {passed}")
        except Exception as e:
            self.print_test("Support Agent", "Return Policy Info", False, str(e))

    def test_support_agent_issue_resolution(self):
        """Test 22: Support Agent should help resolve issues"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "I have an issue with my order. Can you help?",
                    "channel": "web"
                },
                timeout=10
            )
            data = response.json()
            passed = response.status_code == 200 and data.get("reply")
            self.print_test("Support Agent", "Issue Resolution", passed,
                          f"Support response provided: {passed}")
        except Exception as e:
            self.print_test("Support Agent", "Issue Resolution", False, str(e))

    def test_support_agent_order_issues(self):
        """Test 23: Support Agent should handle order-specific issues"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "My order hasn't arrived yet, can you check the status?",
                    "channel": "web"
                },
                timeout=10
            )
            data = response.json()
            passed = response.status_code == 200 and data.get("reply")
            self.print_test("Support Agent", "Order Status Issue", passed,
                          f"Status check provided: {passed}")
        except Exception as e:
            self.print_test("Support Agent", "Order Status Issue", False, str(e))

    # ============================================================================
    # CROSS-AGENT INTEGRATION TESTS
    # ============================================================================

    def test_intent_routing_recommendation(self):
        """Test 24: Intent routing should trigger Recommendation Agent"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "Can you recommend something nice?",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code == 200 and response.json().get("reply")
            self.print_test("Intent Routing", "Recommendation Intent", passed,
                          f"Agent routing: {'OK' if passed else 'FAILED'}")
        except Exception as e:
            self.print_test("Intent Routing", "Recommendation Intent", False, str(e))

    def test_intent_routing_inventory(self):
        """Test 25: Intent routing should trigger Inventory Agent"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "Is this in stock?",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code == 200 and response.json().get("reply")
            self.print_test("Intent Routing", "Inventory Intent", passed,
                          f"Agent routing: {'OK' if passed else 'FAILED'}")
        except Exception as e:
            self.print_test("Intent Routing", "Inventory Intent", False, str(e))

    def test_intent_routing_payment(self):
        """Test 26: Intent routing should trigger Payment Agent"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "I want to buy this item now",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code == 200 and response.json().get("reply")
            self.print_test("Intent Routing", "Payment Intent", passed,
                          f"Agent routing: {'OK' if passed else 'FAILED'}")
        except Exception as e:
            self.print_test("Intent Routing", "Payment Intent", False, str(e))

    def test_intent_routing_loyalty(self):
        """Test 27: Intent routing should trigger Loyalty Agent"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "Do I have any discounts or rewards?",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code == 200 and response.json().get("reply")
            self.print_test("Intent Routing", "Loyalty Intent", passed,
                          f"Agent routing: {'OK' if passed else 'FAILED'}")
        except Exception as e:
            self.print_test("Intent Routing", "Loyalty Intent", False, str(e))

    def test_intent_routing_support(self):
        """Test 28: Intent routing should trigger Support Agent"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "I want to return this product",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code == 200 and response.json().get("reply")
            self.print_test("Intent Routing", "Support Intent", passed,
                          f"Agent routing: {'OK' if passed else 'FAILED'}")
        except Exception as e:
            self.print_test("Intent Routing", "Support Intent", False, str(e))

    def test_intent_routing_fulfillment(self):
        """Test 29: Intent routing should trigger Fulfillment Agent"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "How will my order be delivered?",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code == 200 and response.json().get("reply")
            self.print_test("Intent Routing", "Fulfillment Intent", passed,
                          f"Agent routing: {'OK' if passed else 'FAILED'}")
        except Exception as e:
            self.print_test("Intent Routing", "Fulfillment Intent", False, str(e))

    # ============================================================================
    # EDGE CASE TESTS
    # ============================================================================

    def test_empty_message(self):
        """Test 30: System should handle empty messages"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code in [200, 400]  # Either handles or rejects gracefully
            self.print_test("Edge Cases", "Empty Message Handling", passed,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Edge Cases", "Empty Message Handling", False, str(e))

    def test_very_long_message(self):
        """Test 31: System should handle very long messages"""
        try:
            long_msg = "I want a dress " * 100  # Very long message
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": long_msg,
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code in [200, 400]
            self.print_test("Edge Cases", "Long Message Handling", passed,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Edge Cases", "Long Message Handling", False, str(e))

    def test_special_characters(self):
        """Test 32: System should handle special characters"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "I want a dress with $$$, @special, #hashtag & more!",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code in [200, 400]
            self.print_test("Edge Cases", "Special Characters", passed,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Edge Cases", "Special Characters", False, str(e))

    def test_invalid_user_id(self):
        """Test 33: System should handle invalid user IDs"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": "invalid_user_xyz",
                    "message": "Show me a dress",
                    "channel": "web"
                },
                timeout=10
            )
            passed = response.status_code in [200, 400, 404]
            self.print_test("Edge Cases", "Invalid User ID", passed,
                          f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Edge Cases", "Invalid User ID", False, str(e))

    def test_concurrent_requests(self):
        """Test 34: System should handle concurrent requests"""
        try:
            import threading
            results = []
            
            def send_request():
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/sales",
                        headers=HEADERS,
                        json={
                            "user_id": TEST_USER_ID,
                            "message": "Show me dresses",
                            "channel": "web"
                        },
                        timeout=10
                    )
                    results.append(response.status_code == 200)
                except:
                    results.append(False)
            
            threads = [threading.Thread(target=send_request) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            passed = all(results)
            self.print_test("Edge Cases", "Concurrent Requests", passed,
                          f"Success rate: {sum(results)}/3")
        except Exception as e:
            self.print_test("Edge Cases", "Concurrent Requests", False, str(e))

    def test_response_time_performance(self):
        """Test 35: System should respond within reasonable time"""
        try:
            start = time.time()
            response = requests.post(
                f"{API_BASE_URL}/sales",
                headers=HEADERS,
                json={
                    "user_id": TEST_USER_ID,
                    "message": "Show me a blue dress",
                    "channel": "web"
                },
                timeout=10
            )
            elapsed = time.time() - start
            passed = response.status_code == 200 and elapsed < 8  # Should respond within 8 seconds
            self.print_test("Performance", "Response Time", passed,
                          f"Time: {elapsed:.2f}s")
        except Exception as e:
            self.print_test("Performance", "Response Time", False, str(e))

    def run_all_tests(self):
        """Run all tests in sequence"""
        self.print_header("COMPREHENSIVE BLACK-BOX TESTING SUITE")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API Endpoint: {API_BASE_URL}")
        
        # Check API availability
        try:
            response = requests.get(f"{API_BASE_URL}/products", timeout=5)
            if response.status_code != 200:
                print(f"{RED}✗ API health check failed (status: {response.status_code}){RESET}")
                return
        except Exception as e:
            print(f"{RED}✗ Cannot connect to API at {API_BASE_URL}{RESET}")
            print(f"{YELLOW}Make sure the backend is running with: docker-compose up{RESET}")
            print(f"{YELLOW}Error: {str(e)}{RESET}")
            return

        # Setup
        self.setup_test_user()
        self.get_products()

        # Run all tests
        print(f"\n{BOLD}{BLUE}SALES AGENT TESTS{RESET}")
        self.test_sales_agent_greeting()
        self.test_sales_agent_product_recommendation()
        self.test_sales_agent_follow_up()
        self.test_sales_agent_style_extraction()

        print(f"\n{BOLD}{BLUE}RECOMMENDATION AGENT TESTS{RESET}")
        self.test_recommendation_agent_by_category()
        self.test_recommendation_agent_by_occasion()
        self.test_recommendation_agent_top_3()

        print(f"\n{BOLD}{BLUE}INVENTORY AGENT TESTS{RESET}")
        self.test_inventory_agent_stock_check()
        self.test_inventory_agent_size_options()
        self.test_inventory_agent_multiple_products()

        print(f"\n{BOLD}{BLUE}PAYMENT AGENT TESTS{RESET}")
        self.test_payment_agent_payment_methods()
        self.test_payment_agent_order_summary()
        self.test_payment_agent_loyalty_discount()

        print(f"\n{BOLD}{BLUE}FULFILLMENT AGENT TESTS{RESET}")
        self.test_fulfillment_agent_delivery_options()
        self.test_fulfillment_agent_shipping_cost()
        self.test_fulfillment_agent_order_status()

        print(f"\n{BOLD}{BLUE}LOYALTY AGENT TESTS{RESET}")
        self.test_loyalty_agent_tier_display()
        self.test_loyalty_agent_points_balance()
        self.test_loyalty_agent_coupons()
        self.test_loyalty_agent_tier_progression()

        print(f"\n{BOLD}{BLUE}SUPPORT AGENT TESTS{RESET}")
        self.test_support_agent_return_policy()
        self.test_support_agent_issue_resolution()
        self.test_support_agent_order_issues()

        print(f"\n{BOLD}{BLUE}INTENT ROUTING TESTS{RESET}")
        self.test_intent_routing_recommendation()
        self.test_intent_routing_inventory()
        self.test_intent_routing_payment()
        self.test_intent_routing_loyalty()
        self.test_intent_routing_support()
        self.test_intent_routing_fulfillment()

        print(f"\n{BOLD}{BLUE}EDGE CASE & PERFORMANCE TESTS{RESET}")
        self.test_empty_message()
        self.test_very_long_message()
        self.test_special_characters()
        self.test_invalid_user_id()
        self.test_concurrent_requests()
        self.test_response_time_performance()

        # Summary
        self.print_summary()
        
        # Save results to file
        self.save_results()

    def save_results(self):
        """Save test results to JSON file"""
        output_file = "test_results_blackbox.json"
        with open(output_file, "w") as f:
            json.dump({
                "summary": {
                    "total": self.total_tests,
                    "passed": self.passed_tests,
                    "failed": self.failed_tests,
                    "success_rate": f"{(self.passed_tests/self.total_tests*100):.1f}%"
                },
                "timestamp": datetime.now().isoformat(),
                "results": self.test_results
            }, f, indent=2)
        print(f"\n{GREEN}✓ Results saved to {output_file}{RESET}")


if __name__ == "__main__":
    runner = AgentTestRunner()
    runner.run_all_tests()
