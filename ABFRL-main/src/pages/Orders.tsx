import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Package, ArrowLeft } from 'lucide-react';
import { api, ApiOrder } from '@/lib/api';

const Orders: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [orders, setOrders] = useState<ApiOrder[]>([]);

  useEffect(() => {
    if (!user) return;
    api.orders(user.id).then((res) => setOrders(res.orders)).catch(() => undefined);
  }, [user]);

  if (!isAuthenticated || !user) {
    navigate('/auth');
    return null;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <Button variant="ghost" onClick={() => navigate('/')} className="mb-6"><ArrowLeft className="h-4 w-4 mr-2" /> Back to Home</Button>
        <h1 className="text-3xl font-bold mb-8">My Orders</h1>

        {orders.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center"><Package className="h-16 w-16 text-muted-foreground mx-auto mb-4" /><h2 className="text-xl font-semibold mb-2">No orders yet</h2><Button onClick={() => navigate('/products')}>Start Shopping</Button></CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <Card key={order.id}>
                <CardHeader><CardTitle>{order.order_number} · {order.order_status}</CardTitle></CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-2">{new Date(order.created_at).toLocaleString()}</p>
                  <p className="font-semibold mb-3">Total: ${order.final_amount.toFixed(2)}</p>
                  <ul className="text-sm space-y-1">{order.items.map((item) => <li key={item.id}>{item.product_name} × {item.quantity}</li>)}</ul>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Orders;
