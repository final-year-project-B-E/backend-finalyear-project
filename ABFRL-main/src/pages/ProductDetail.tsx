import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Heart, Minus, Plus, Truck, RotateCcw, Shield, ChevronRight } from 'lucide-react';
import { Layout } from '@/components/layout';
import { ProductGrid } from '@/components/product';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { mockProducts } from '@/data/mockData';
import { Product } from '@/types';
import { api } from '@/lib/api';
import { useCart } from '@/contexts/CartContext';
import { useWishlist } from '@/contexts/WishlistContext';
import { toast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

const ProductDetail = () => {
  const { id } = useParams();
  const { addItem } = useCart();
  const { isInWishlist, toggleItem } = useWishlist();
  
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [products, setProducts] = useState<Product[]>(mockProducts);

  useEffect(() => {
    api.products().then((res) => setProducts(res.products)).catch(() => undefined);
  }, []);

  const product = useMemo(() => products.find(p => p.id === Number(id)), [id, products]);

  const relatedProducts = useMemo(() => {
    if (!product) return [];
    return products
      .filter(p => p.id !== product.id && p.dress_category === product.dress_category)
      .slice(0, 4);
  }, [product, products]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [id]);

  if (!product) {
    return (
      <Layout>
        <div className="container py-16 text-center">
          <h1 className="text-2xl text-destructive mb-4">Product not found</h1>
          <Link to="/products" className="text-gold hover:text-gold/80">Back to products</Link>
        </div>
      </Layout>
    );
  }

  const sizes = product.available_sizes?.split(',') || [];
  const colors = product.colors?.split(',') || [];
  const isWishlisted = isInWishlist(product.id);

  const handleAddToCart = () => {
    if (!selectedSize) { 
      toast({ title: "Please select a size", variant: "destructive" }); 
      return; 
    }
    if (!selectedColor) { 
      toast({ title: "Please select a color", variant: "destructive" }); 
      return; 
    }
    void addItem(product, quantity, selectedSize, selectedColor);
    toast({ title: "Added to bag", description: `${product.product_name} has been added to your shopping bag.` });
  };

  const formatPrice = (price: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price);

  return (
    <Layout>
      {/* Breadcrumb */}
      <div className="container py-4">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link to="/" className="hover:text-foreground">Home</Link>
          <ChevronRight className="h-4 w-4" />
          <Link to="/products" className="hover:text-foreground">Products</Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-foreground truncate">{product.product_name}</span>
        </nav>
      </div>

      <div className="container pb-16">
        <div className="grid lg:grid-cols-2 gap-12">
          {/* Images */}
          <div className="space-y-4">
            <div className="aspect-[3/4] bg-secondary rounded-sm overflow-hidden">
              <img src={product.image_url || '/placeholder.svg'} alt={product.product_name} className="w-full h-full object-cover" />
            </div>
          </div>

          {/* Product Info */}
          <div className="lg:sticky lg:top-24 lg:self-start">
            <span className="text-sm text-gold uppercase tracking-wider">{product.occasion}</span>
            <h1 className="font-serif text-3xl md:text-4xl mt-2 mb-4">{product.product_name}</h1>
            <p className="font-serif text-2xl text-gold mb-6">{formatPrice(product.price)}</p>
            <p className="text-muted-foreground mb-8 leading-relaxed">{product.description}</p>

            {/* Color Selection */}
            {colors.length > 0 && (
              <div className="mb-6">
                <div className="flex justify-between mb-3">
                  <span className="text-sm font-medium">Color</span>
                  <span className="text-sm text-muted-foreground">{selectedColor || 'Select a color'}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {colors.map((color) => (
                    <button key={color} onClick={() => setSelectedColor(color.trim())} className={cn('px-4 py-2 text-sm border rounded-sm transition-colors', selectedColor === color.trim() ? 'border-gold bg-gold/10' : 'border-border hover:border-foreground')}>
                      {color.trim()}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Size Selection */}
            {sizes.length > 0 && (
              <div className="mb-6">
                <div className="flex justify-between mb-3">
                  <span className="text-sm font-medium">Size</span>
                  <button className="text-sm text-gold underline">Size Guide</button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {sizes.map((size) => (
                    <button key={size} onClick={() => setSelectedSize(size.trim())} className={cn('w-12 h-12 text-sm border rounded-sm transition-colors', selectedSize === size.trim() ? 'border-gold bg-gold/10' : 'border-border hover:border-foreground')}>
                      {size.trim()}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Quantity & Add to Cart */}
            <div className="flex gap-4 mb-6">
              <div className="flex items-center border rounded-sm">
                <Button variant="ghost" size="icon" onClick={() => setQuantity(Math.max(1, quantity - 1))}><Minus className="h-4 w-4" /></Button>
                <span className="w-12 text-center">{quantity}</span>
                <Button variant="ghost" size="icon" onClick={() => setQuantity(quantity + 1)}><Plus className="h-4 w-4" /></Button>
              </div>
              <Button className="flex-1 bg-primary hover:bg-primary/90" size="lg" onClick={handleAddToCart}>Add to Bag</Button>
              <Button variant="outline" size="icon" className="h-12 w-12" onClick={() => toggleItem(product)}>
                <Heart className={cn('h-5 w-5', isWishlisted && 'fill-gold text-gold')} />
              </Button>
            </div>

            {/* Features */}
            <div className="grid grid-cols-3 gap-4 py-6 border-y">
              <div className="text-center"><Truck className="h-5 w-5 mx-auto mb-2 text-gold" /><span className="text-xs">Free Shipping</span></div>
              <div className="text-center"><RotateCcw className="h-5 w-5 mx-auto mb-2 text-gold" /><span className="text-xs">30-Day Returns</span></div>
              <div className="text-center"><Shield className="h-5 w-5 mx-auto mb-2 text-gold" /><span className="text-xs">Secure Payment</span></div>
            </div>

            {/* Details Tabs */}
            <Tabs defaultValue="details" className="mt-8">
              <TabsList className="w-full"><TabsTrigger value="details" className="flex-1">Details</TabsTrigger><TabsTrigger value="care" className="flex-1">Care</TabsTrigger></TabsList>
              <TabsContent value="details" className="text-sm text-muted-foreground space-y-2 mt-4">
                <p><strong>Material:</strong> {product.material}</p>
                <p><strong>Category:</strong> {product.dress_category.replace('-', ' ')}</p>
                {product.stock <= 5 && <p className="text-destructive">Only {product.stock} left in stock!</p>}
              </TabsContent>
              <TabsContent value="care" className="text-sm text-muted-foreground mt-4">
                <p>Dry clean only. Store in a cool, dry place away from direct sunlight.</p>
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Related Products */}
        {relatedProducts.length > 0 && (
          <section className="mt-24">
            <h2 className="font-serif text-2xl mb-8">You May Also Like</h2>
            <ProductGrid products={relatedProducts} columns={4} />
          </section>
        )}
      </div>
    </Layout>
  );
};

export default ProductDetail;
