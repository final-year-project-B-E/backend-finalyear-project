# E-Commerce Checkout Implementation

This document describes the complete checkout procedure and payment gateway simulation implementation for the e-commerce platform.

## Overview

The checkout system provides a seamless shopping experience with the following features:

- **Multi-step checkout flow**: Address → Payment → Review → Confirmation
- **Payment gateway simulation**: Realistic payment processing with success/failure scenarios
- **Cart validation**: Real-time validation of items, stock, and pricing
- **Order management**: Complete order lifecycle from creation to cancellation
- **Loyalty system integration**: Automatic discount calculation based on user loyalty score

## Architecture

### Backend Components

#### 1. Payment Gateway Simulation (`backend/payment_gateway.py`)

- **PaymentStatus**: Enum for payment states (pending, success, failed, refunded, cancelled)
- **PaymentMethod**: Enum for supported payment methods (credit_card, debit_card, net_banking, upi, wallet)
- **PaymentGateway**: Main class handling payment processing with realistic success/failure rates

**Key Features:**

- 85% success rate, 10% failure rate, 5% timeout rate
- Card validation (16-digit number, valid expiry, 3-4 digit CVV)
- Transaction ID generation
- Refund processing with 95% success rate

#### 2. Checkout Service (`backend/checkout_service.py`)

- **CheckoutService**: Main service class handling the complete checkout flow
- **CheckoutError**: Custom exception for checkout-related errors

**Checkout Flow:**

1. **Cart Validation**: Validate items, stock, and pricing
2. **Total Calculation**: Apply discounts, taxes, and shipping
3. **Order Creation**: Create order and order items, update stock
4. **Payment Processing**: Process payment through simulated gateway
5. **Order Completion**: Update order status and user loyalty score

**Key Features:**

- Loyalty-based discounts (5% for 500+ points, 10% for 1000+ points)
- Free shipping over ₹1000
- 8.875% tax calculation
- Stock management and validation
- Order cancellation with refund processing

#### 3. API Endpoints (`backend/main.py`)

**New Checkout Endpoints:**

- `POST /checkout` - Complete checkout flow
- `POST /orders/{order_id}/pay` - Process payment for existing order
- `GET /orders/{order_id}/payment-status` - Get payment status
- `PUT /orders/{order_id}/cancel` - Cancel order with refund
- `GET /payment-methods` - Get supported payment methods
- `GET /cart/checkout-preview` - Get checkout preview with totals

### Frontend Components

#### 1. Checkout Page (`src/pages/Checkout.tsx`)

**Multi-step Checkout Flow:**

1. **Address Step**: Shipping and billing address input
2. **Payment Step**: Payment method selection and card details
3. **Review Step**: Order summary and confirmation
4. **Success/Error Steps**: Completion feedback

**Features:**

- Progress indicator showing current step
- Form validation for addresses and payment details
- Real-time total calculation
- Payment method selection with icons
- Card details validation
- Success and error handling

#### 2. Cart Page (`src/pages/Cart.tsx`)

**Full Cart View:**

- Item listing with images, prices, and quantities
- Quantity adjustment controls
- Item removal functionality
- Order summary with subtotal
- Checkout button with authentication check
- Clear cart functionality

#### 3. Updated Components

- **Header**: Added cart page link in user dropdown
- **CartDrawer**: Already had checkout button
- **API**: Added checkout-related endpoints

## Payment Methods

### Supported Payment Methods

1. **Credit Card**: Visa, MasterCard, American Express
2. **Debit Card**: Visa, MasterCard, Rupay
3. **UPI**: Unified Payments Interface
4. **Digital Wallet**: Paytm, PhonePe, Google Pay
5. **Net Banking**: Direct bank transfer

### Card Validation Rules

- **Card Number**: 16 digits
- **Expiry Date**: MM/YYYY format, must be future date
- **CVV**: 3-4 digits
- **Validation**: Real-time validation before submission

## Order Flow

### Order Status Lifecycle

1. **processing** → **confirmed** → **shipped** → **delivered**
2. **processing** → **payment_failed** (if payment fails)
3. **processing/confirmed** → **cancelled** (if cancelled)

### Payment Status Lifecycle

1. **pending** → **success** (payment successful)
2. **pending** → **failed** (payment failed)
3. **success** → **refunded** (if order cancelled)

## Database Schema

### Order Table

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    total_amount DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    shipping_amount DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    final_amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(100),
    shipping_address TEXT NOT NULL,
    billing_address TEXT NOT NULL,
    order_status VARCHAR(20) DEFAULT 'processing',
    tracking_number VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Order Items Table

```sql
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Testing

### Test Script (`test_checkout.py`)

Comprehensive test script that validates the entire checkout flow:

1. **User Registration**: Creates test user
2. **User Login**: Authenticates user
3. **Product Retrieval**: Gets available products
4. **Cart Management**: Adds items to cart
5. **Checkout Preview**: Validates totals and items
6. **Payment Methods**: Retrieves supported methods
7. **Checkout Completion**: Processes complete checkout
8. **Order Verification**: Confirms order creation

**Usage:**

```bash
python test_checkout.py
```

**Prerequisites:**

- Backend server running on localhost:8000
- Database with sample products
- Network connectivity

## API Usage Examples

### 1. Checkout Preview

```javascript
const preview = await checkoutAPI.getCheckoutPreview(token);
// Returns: { has_items, item_count, valid_items, totals, user_loyalty }
```

### 2. Complete Checkout

```javascript
const result = await checkoutAPI.checkout(token, {
  shipping_address: "123 Main St, City, State, PIN",
  billing_address: "123 Main St, City, State, PIN",
  payment_method: "credit_card",
  notes: "Special instructions",
  card_details: {
    card_number: "4532015112830366",
    expiry_month: "12",
    expiry_year: "2025",
    cvv: "123",
  },
});
```

### 3. Get Payment Status

```javascript
const status = await checkoutAPI.getPaymentStatus(token, orderId);
// Returns: { order_id, order_number, payment_status, transaction_id, etc. }
```

### 4. Cancel Order

```javascript
const result = await checkoutAPI.cancelOrder(token, orderId);
// Returns: { success, order_id, refund_result }
```

## Error Handling

### Common Error Scenarios

1. **Empty Cart**: "Cart is empty"
2. **Insufficient Stock**: "Insufficient stock for product X"
3. **Invalid Card**: "Invalid card details"
4. **Payment Failed**: "Payment processing failed"
5. **Authentication Required**: "Please login to proceed"

### Error Response Format

```json
{
  "success": false,
  "error": "Error description",
  "error_type": "checkout_error|system_error"
}
```

## Security Features

1. **JWT Authentication**: All checkout endpoints require valid JWT tokens
2. **User Authorization**: Users can only access their own orders
3. **Input Validation**: All inputs are validated server-side
4. **Card Security**: Card details are validated but not stored
5. **Transaction IDs**: Unique transaction IDs for tracking

## Performance Considerations

1. **Database Transactions**: All checkout operations use database transactions
2. **Stock Locking**: Items are reserved during checkout to prevent overselling
3. **Caching**: Payment methods are cached for performance
4. **Validation**: Early validation prevents unnecessary database operations

## Future Enhancements

1. **Multiple Shipping Addresses**: Support different shipping and billing addresses
2. **Gift Cards**: Integration with gift card system
3. **Installments**: EMI payment options
4. **International Shipping**: Multi-currency and international shipping support
5. **Advanced Fraud Detection**: ML-based fraud detection
6. **Real Payment Gateway**: Integration with actual payment providers

## Deployment Notes

1. **Environment Variables**: Ensure SECRET_KEY is set for JWT signing
2. **Database**: Ensure database has proper indexes for performance
3. **Logging**: Configure logging for payment processing
4. **Monitoring**: Monitor checkout conversion rates and error rates
5. **Backup**: Regular database backups for order data

## Support

For issues related to checkout functionality:

1. Check server logs for error details
2. Verify database connectivity
3. Ensure payment gateway is properly configured
4. Test with the provided test script
5. Validate frontend-backend API integration
