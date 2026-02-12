import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useToast } from '../hooks/use-toast';
import { CheckCircle, ArrowLeft } from 'lucide-react';
import { useState } from 'react';

const Checkout: React.FC = () => {
  const navigate = useNavigate();
  const { items, subtotal, clearCart } = useCart();
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [isComplete, setIsComplete] = useState(false);

  if (!isAuthenticated) {
    navigate('/auth');
    return null;
  }

  if (items.length === 0 && !isComplete) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <h1 className="text-2xl font-bold mb-4">Your cart is empty</h1>
        <Button onClick={() => navigate('/products')}>Continue Shopping</Button>
      </div>
    );
  }

  const handleCheckout = () => {
    clearCart();
    setIsComplete(true);
    toast({
      title: "Order Placed!",
      description: "Thank you for your order. This is a demo checkout.",
    });
  };

  if (isComplete) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
        <h1 className="text-3xl font-bold mb-4">Order Confirmed!</h1>
        <p className="text-muted-foreground mb-8">Thank you for your order. This is a demo - no actual order was placed.</p>
        <Button onClick={() => navigate('/products')}>Continue Shopping</Button>
      </div>
    );
  }

  const formatCurrency = (amount: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <Button variant="ghost" onClick={() => navigate('/cart')} className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Cart
        </Button>
        
        <Card>
          <CardHeader>
            <CardTitle>Checkout</CardTitle>
            <CardDescription>Complete your order (Demo Mode)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div>
                <Label>Shipping Address</Label>
                <Input placeholder="123 Main St, City, State 12345" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Card Number</Label>
                  <Input placeholder="4111 1111 1111 1111" />
                </div>
                <div>
                  <Label>CVV</Label>
                  <Input placeholder="123" />
                </div>
              </div>
            </div>

            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between">
                <span>Subtotal</span>
                <span>{formatCurrency(subtotal)}</span>
              </div>
              <div className="flex justify-between">
                <span>Shipping</span>
                <span>Free</span>
              </div>
              <div className="flex justify-between font-bold text-lg">
                <span>Total</span>
                <span>{formatCurrency(subtotal)}</span>
              </div>
            </div>

            <Button onClick={handleCheckout} className="w-full" size="lg">
              Place Order (Demo)
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Checkout;
