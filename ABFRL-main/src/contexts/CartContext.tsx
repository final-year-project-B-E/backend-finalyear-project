import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { Product } from '@/types';
import { useAuth } from './AuthContext';
import { api } from '@/lib/api';

interface CartItemWithProduct {
  id: number;
  product: Product;
  quantity: number;
  size: string;
  color: string;
}

interface CartContextType {
  items: CartItemWithProduct[];
  addItem: (product: Product, quantity: number, size: string, color: string) => Promise<void>;
  removeItem: (id: number) => void;
  updateQuantity: (id: number, quantity: number) => void;
  clearCart: () => void;
  isOpen: boolean;
  openCart: () => void;
  closeCart: () => void;
  totalItems: number;
  subtotal: number;
  isLoading: boolean;
  refreshCart: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);
const STORAGE_KEY = 'cart_items';

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [items, setItems] = useState<CartItemWithProduct[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const refreshCart = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const res = await api.getCart(user.id);
      const backendItems = res.cart_items.map((item: any) => ({
        id: item.id,
        product: item.product,
        quantity: item.quantity,
        size: 'M',
        color: 'Default',
      }));
      setItems(backendItems);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(backendItems));
    } catch {
      // keep local fallback
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        setItems(JSON.parse(saved));
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  useEffect(() => {
    if (user) refreshCart();
  }, [user, refreshCart]);

  const addItem = useCallback(async (product: Product, quantity: number, size: string, color: string) => {
    if (user) {
      await api.addToCart(user.id, product.id, quantity);
      await refreshCart();
      return;
    }

    setItems((prev) => {
      const existingIndex = prev.findIndex((item) => item.product.id === product.id && item.size === size && item.color === color);
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = { ...updated[existingIndex], quantity: updated[existingIndex].quantity + quantity };
        return updated;
      }
      return [...prev, { id: Date.now(), product, quantity, size, color }];
    });
  }, [refreshCart, user]);

  const removeItem = useCallback((id: number) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const updateQuantity = useCallback((id: number, quantity: number) => {
    if (quantity <= 0) return;
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, quantity } : item)));
  }, []);

  const clearCart = useCallback(() => setItems([]), []);

  const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);
  const subtotal = items.reduce((sum, item) => sum + item.product.price * item.quantity, 0);

  return (
    <CartContext.Provider
      value={{
        items,
        addItem,
        removeItem,
        updateQuantity,
        clearCart,
        isOpen,
        openCart: () => setIsOpen(true),
        closeCart: () => setIsOpen(false),
        totalItems,
        subtotal,
        isLoading,
        refreshCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) throw new Error('useCart must be used within a CartProvider');
  return context;
};
