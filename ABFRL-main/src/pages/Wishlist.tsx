import { Link } from 'react-router-dom';
import { Heart, ShoppingBag, Trash2, ArrowRight } from 'lucide-react';
import { Layout } from '@/components/layout/Layout';
import { Button } from '@/components/ui/button';
import { useWishlist } from '@/contexts/WishlistContext';
import { useCart } from '@/contexts/CartContext';
import { toast } from '@/hooks/use-toast';
import { Product } from '@/types';

const Wishlist = () => {
  const { items, removeItem, toggleItem, isInWishlist, isLoading } = useWishlist();
  const { addItem: addToCart } = useCart();

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const handleAddToCart = (product: Product) => {
    const colors = product.colors?.split(',') || ['Default'];
    addToCart(product, 1, 'M', colors[0].trim());
    toast({
      title: "Added to bag",
      description: `${product.product_name} has been added to your shopping bag.`,
    });
  };

  const handleRemove = (product: Product) => {
    removeItem(product.id);
    toast({
      title: "Removed from wishlist",
      description: `${product.product_name} has been removed from your wishlist.`,
    });
  };

  const handleToggleWishlist = (product: Product) => {
    toggleItem(product);
    const wasInWishlist = isInWishlist(product.id);
    toast({
      title: wasInWishlist ? "Removed from wishlist" : "Added to wishlist",
      description: `${product.product_name} has been ${wasInWishlist ? 'removed from' : 'added to'} your wishlist.`,
    });
  };

  return (
    <Layout>
      <div className="container py-8 md:py-12">
        {/* Header */}
        <div className="mb-8 md:mb-12">
          <h1 className="font-serif text-3xl md:text-4xl lg:text-5xl font-bold mb-3">
            My Wishlist
          </h1>
          <p className="text-muted-foreground">
            {items.length === 0
              ? "Your wishlist is empty"
              : `${items.length} item${items.length > 1 ? 's' : ''} saved for later`}
          </p>
        </div>

        {items.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-24 h-24 rounded-full bg-secondary flex items-center justify-center mb-6">
              <Heart className="h-12 w-12 text-muted-foreground" />
            </div>
            <h2 className="font-serif text-2xl mb-3">No saved items yet</h2>
            <p className="text-muted-foreground mb-8 max-w-md">
              Start exploring our collections and save your favorite pieces to your wishlist.
            </p>
            <Button asChild className="bg-gradient-to-r from-brand-red via-brand-orange to-gold hover:from-brand-red-dark hover:via-brand-orange-dark hover:to-gold-dark text-white">
              <Link to="/products">
                Explore Collections
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        ) : (
          /* Wishlist Grid */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 md:gap-8">
            {items.map((product) => (
              <div key={product.id} className="group relative">
                {/* Image */}
                <Link to={`/product/${product.id}`} className="block">
                  <div className="aspect-[3/4] overflow-hidden bg-secondary rounded-sm mb-4 relative">
                    <img
                      src={product.image_url || '/placeholder.svg'}
                      alt={product.product_name}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                    {/* Overlay on hover */}
                    <div className="absolute inset-0 bg-foreground/0 group-hover:bg-foreground/10 transition-colors" />
                  </div>
                </Link>

                {/* Wishlist heart indicator */}
                <div className="absolute top-3 right-3 h-9 w-9 rounded-full bg-background/80 backdrop-blur-sm flex items-center justify-center">
                  <button
                    onClick={() => handleToggleWishlist(product)}
                    disabled={isLoading}
                  >
                    <Heart className={`h-4 w-4 ${isInWishlist(product.id) ? 'fill-brand-red text-brand-red' : 'text-muted-foreground'}`} />
                  </button>
                </div>

                {/* Featured Badge */}
                {product.featured_dress && (
                  <span className="absolute top-3 left-3 px-2 py-1 bg-gradient-to-r from-brand-orange to-gold text-white text-[10px] tracking-wider uppercase font-medium rounded-sm">
                    Featured
                  </span>
                )}

                {/* Product Info */}
                <Link to={`/product/${product.id}`}>
                  <h3 className="font-medium text-sm leading-tight mb-1 group-hover:text-brand-orange transition-colors line-clamp-2">
                    {product.product_name}
                  </h3>
                  <p className="text-xs text-muted-foreground mb-2 capitalize">
                    {product.occasion}
                  </p>
                  <p className="font-serif text-base text-brand-orange mb-4">
                    {formatPrice(product.price)}
                  </p>
                </Link>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleAddToCart(product)}
                    className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground text-sm"
                    size="sm"
                  >
                    <ShoppingBag className="h-4 w-4 mr-2" />
                    Add to Bag
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRemove(product)}
                    className="border-destructive/30 text-destructive hover:bg-destructive hover:text-destructive-foreground"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Continue Shopping */}
        {items.length > 0 && (
          <div className="mt-12 pt-8 border-t border-border text-center">
            <Link 
              to="/products" 
              className="inline-flex items-center text-sm font-medium text-brand-orange hover:text-brand-orange-dark transition-colors"
            >
              Continue Shopping
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Wishlist;
