import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useToast } from '../hooks/use-toast';
import { CheckCircle, ArrowLeft } from 'lucide-react';
import { api } from '@/lib/api';

const Checkout: React.FC = () => {
  const navigate = useNavigate();
  const { items, subtotal, clearCart, refreshCart } = useCart();
  const { isAuthenticated, user } = useAuth();
  const { toast } = useToast();
  const [isComplete, setIsComplete] = useState(false);
  const [shippingAddress, setShippingAddress] = useState('');
  const [billingAddress, setBillingAddress] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('card');

  if (!isAuthenticated || !user) {
    navigate('/auth');
    return null;
  }

  if (items.length === 0 && !isComplete) {
    return <div className="container mx-auto px-4 py-12 text-center"><h1 className="text-2xl font-bold mb-4">Your cart is empty</h1><Button onClick={() => navigate('/products')}>Continue Shopping</Button></div>;
  }

  const handleCheckout = async () => {
    try {
      await api.checkout(user.id, {
        shipping_address: shippingAddress || 'Default shipping address',
        billing_address: billingAddress || 'Default billing address',
        payment_method: paymentMethod,
      });
      clearCart();
      await refreshCart();
      setIsComplete(true);
      toast({ title: 'Order Placed!', description: 'Order successfully created in backend.' });
    } catch (error) {
      toast({ title: 'Checkout failed', description: String(error), variant: 'destructive' });
    }
  };

  if (isComplete) {
    return <div className="container mx-auto px-4 py-12 text-center"><CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" /><h1 className="text-3xl font-bold mb-4">Order Confirmed!</h1><p className="text-muted-foreground mb-8">Your order has been saved in MongoDB via backend.</p><Button onClick={() => navigate('/orders')}>View Orders</Button></div>;
  }

  const formatCurrency = (amount: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <Button variant="ghost" onClick={() => navigate('/cart')} className="mb-6"><ArrowLeft className="h-4 w-4 mr-2" /> Back to Cart</Button>
        <Card>
          <CardHeader><CardTitle>Checkout</CardTitle><CardDescription>Complete your order</CardDescription></CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div><Label>Shipping Address</Label><Input placeholder="123 Main St" value={shippingAddress} onChange={(e) => setShippingAddress(e.target.value)} /></div>
              <div><Label>Billing Address</Label><Input placeholder="123 Main St" value={billingAddress} onChange={(e) => setBillingAddress(e.target.value)} /></div>
              <div><Label>Payment Method</Label><Input placeholder="card / upi / netbanking" value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} /></div>
            </div>
            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between"><span>Subtotal</span><span>{formatCurrency(subtotal)}</span></div>
              <div className="flex justify-between"><span>Shipping</span><span>{subtotal < 100 ? '$9.99' : 'Free'}</span></div>
              <div className="flex justify-between font-bold text-lg"><span>Total</span><span>{formatCurrency(subtotal < 100 ? subtotal + 9.99 : subtotal)}</span></div>
            </div>
            <Button onClick={handleCheckout} className="w-full" size="lg">Place Order</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Checkout;
