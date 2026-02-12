import { Link } from 'react-router-dom';
import { Heart } from 'lucide-react';
import { Product } from '@/types';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useWishlist } from '@/contexts/WishlistContext';

interface ProductCardProps {
  product: Product;
  className?: string;
}

export const ProductCard = ({ product, className }: ProductCardProps) => {
  const { isInWishlist, toggleItem } = useWishlist();
  const isWishlisted = isInWishlist(product.id);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  return (
    <div className={cn('group relative', className)}>
      {/* Image Container */}
      <Link to={`/product/${product.id}`} className="block">
        <div className="aspect-[3/4] overflow-hidden bg-secondary rounded-sm mb-4">
          <img
            src={product.image_url || '/placeholder.svg'}
            alt={product.product_name}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        </div>
      </Link>

      {/* Wishlist Button */}
      <Button
        variant="ghost"
        size="icon"
        className={cn(
          'absolute top-3 right-3 h-9 w-9 rounded-full bg-background/80 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity',
          isWishlisted && 'opacity-100'
        )}
        onClick={() => toggleItem(product)}
      >
        <Heart
          className={cn(
            'h-4 w-4 transition-colors',
            isWishlisted ? 'fill-brand-red text-brand-red' : 'text-foreground'
          )}
        />
      </Button>

      {/* Featured Badge */}
      {product.featured_dress && (
        <span className="absolute top-3 left-3 px-2 py-1 bg-gradient-to-r from-brand-orange to-gold text-white text-[10px] tracking-wider uppercase font-medium rounded-sm">
          Featured
        </span>
      )}

      {/* Low Stock Badge */}
      {product.stock > 0 && product.stock <= 5 && (
        <span className="absolute top-3 left-3 px-2 py-1 bg-destructive text-destructive-foreground text-[10px] tracking-wider uppercase font-medium rounded-sm">
          Low Stock
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
        <p className="font-serif text-base text-brand-orange">
          {formatPrice(product.price)}
        </p>
      </Link>
    </div>
  );
};
