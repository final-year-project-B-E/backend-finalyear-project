export interface User {
  id: number;
  email: string;
  password_hash: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  postal_code: string | null;
  loyalty_score: number;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: number;
  product_name: string;
  description: string | null;
  dress_category: string;
  occasion: string | null;
  price: number;
  stock: number;
  material: string | null;
  available_sizes: string | null;
  colors: string | null;
  image_url: string | null;
  featured_dress: boolean;
  created_at: string;
  updated_at: string;
}

export interface CartItem {
  id: number;
  user_id: number;
  product_id: number;
  quantity: number;
  size: string;
  color: string;
  added_at: string;
  product?: Product;
}

export interface Order {
  id: number;
  order_number: string;
  user_id: number;
  total_amount: number;
  tax_amount: number;
  shipping_amount: number;
  discount_amount: number;
  final_amount: number;
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded' | 'cancelled';
  payment_method: string | null;
  transaction_id: string | null;
  shipping_address: string;
  billing_address: string;
  order_status: 'processing' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled' | 'returned';
  tracking_number: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  order_items: OrderItem[];
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  created_at: string;
}

export type DressCategory = 
  | 'women-dresses' 
  | 'women-tops' 
  | 'women-bottoms' 
  | 'women-outerwear'
  | 'men-shirts' 
  | 'men-pants' 
  | 'men-suits' 
  | 'men-outerwear'
  | 'kids-girls' 
  | 'kids-boys' 
  | 'kids-baby';

export type Occasion = 
  | 'casual' 
  | 'formal' 
  | 'party' 
  | 'wedding' 
  | 'office' 
  | 'vacation' 
  | 'sports';

export interface FilterState {
  category: string | null;
  occasion: string | null;
  priceRange: [number, number];
  sizes: string[];
  colors: string[];
  sortBy: 'newest' | 'price-low' | 'price-high' | 'featured';
}
