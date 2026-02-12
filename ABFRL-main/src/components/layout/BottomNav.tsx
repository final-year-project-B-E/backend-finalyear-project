import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, ShoppingBag, Heart, User, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCart } from '@/contexts/CartContext';
import { useAuth } from '@/contexts/AuthContext';
import { useWishlist } from '@/contexts/WishlistContext';
import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { categories } from '@/data/mockData';

export const BottomNav = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { totalItems, openCart } = useCart();
  const { isAuthenticated } = useAuth();
  const { items: wishlistItems } = useWishlist();
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCategoryOpen, setIsCategoryOpen] = useState(false);

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery)}`);
      setSearchQuery('');
      setIsSearchOpen(false);
    }
  };

  const handleOpenSearch = () => {
    setIsSearchOpen(true);
  };

  const handleCategorySelect = (categoryId: string) => {
    navigate(`/products?category=${categoryId}`);
    setIsCategoryOpen(false);
  };

  const handleAllProducts = () => {
    navigate('/products');
    setIsCategoryOpen(false);
  };

  return (
    <>
      {/* Spacer for main content */}
      <div className="h-20 md:h-0" />

      {/* Bottom Navigation - Mobile only */}
      <nav className="fixed md:hidden bottom-0 left-0 right-0 z-50 bg-background border-t border-border/50 shadow-lg">
        <div className="flex items-center justify-around h-20">
          {/* Home */}
          <Link to="/" className="flex flex-col items-center justify-center w-full h-full hover:bg-secondary/50 transition-colors">
            <Home
              className={`h-6 w-6 ${
                isActive('/') ? 'text-brand-orange' : 'text-muted-foreground'
              }`}
            />
            <span className={`text-xs mt-1 ${
              isActive('/') ? 'text-brand-orange font-medium' : 'text-muted-foreground'
            }`}>
              Home
            </span>
          </Link>

          {/* Search */}
          <button
            onClick={handleOpenSearch}
            className="flex flex-col items-center justify-center w-full h-full hover:bg-secondary/50 transition-colors"
          >
            <Search className="h-6 w-6 text-muted-foreground" />
            <span className="text-xs mt-1 text-muted-foreground">Search</span>
          </button>

          {/* Shop */}
          <button
            onClick={() => setIsCategoryOpen(true)}
            className="flex flex-col items-center justify-center w-full h-full hover:bg-secondary/50 transition-colors"
          >
            <ShoppingBag
              className={`h-6 w-6 ${
                isActive('/products') ? 'text-brand-orange' : 'text-muted-foreground'
              }`}
            />
            <span className={`text-xs mt-1 ${
              isActive('/products') ? 'text-brand-orange font-medium' : 'text-muted-foreground'
            }`}>
              Shop
            </span>
          </button>

          {/* Wishlist */}
          <Link to="/wishlist" className="flex flex-col items-center justify-center w-full h-full hover:bg-secondary/50 transition-colors relative">
            <Heart
              className={`h-6 w-6 ${
                isActive('/wishlist') ? 'text-brand-orange' : 'text-muted-foreground'
              }`}
            />
            {wishlistItems.length > 0 && (
              <span className="absolute top-2 right-2 h-4 w-4 rounded-full bg-brand-red text-[10px] font-bold text-white flex items-center justify-center">
                {wishlistItems.length}
              </span>
            )}
            <span className={`text-xs mt-1 ${
              isActive('/wishlist') ? 'text-brand-orange font-medium' : 'text-muted-foreground'
            }`}>
              Wishlist
            </span>
          </Link>

          {/* Profile/Cart */}
          <Link
            to={isAuthenticated ? "/profile" : "/auth"}
            className="flex flex-col items-center justify-center w-full h-full hover:bg-secondary/50 transition-colors relative"
          >
            <User
              className={`h-6 w-6 ${
                isActive(isAuthenticated ? '/profile' : '/auth') ? 'text-brand-orange' : 'text-muted-foreground'
              }`}
            />
            {totalItems > 0 && (
              <span className="absolute top-2 right-2 h-4 w-4 rounded-full bg-brand-red text-[10px] font-bold text-white flex items-center justify-center">
                {totalItems}
              </span>
            )}
            <span className={`text-xs mt-1 ${
              isActive(isAuthenticated ? '/profile' : '/auth') ? 'text-brand-orange font-medium' : 'text-muted-foreground'
            }`}>
              {isAuthenticated ? 'Profile' : 'Login'}
            </span>
          </Link>
        </div>
      </nav>

      {/* Search Dialog */}
      <Dialog open={isSearchOpen} onOpenChange={setIsSearchOpen}>
        <DialogContent className="top-1/3">
          <DialogHeader>
            <DialogTitle>Search Products</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search products..."
              className="flex-1 h-10 px-4 text-sm bg-secondary rounded-sm border-0 focus:outline-none focus:ring-1 focus:ring-brand-orange"
              autoFocus
            />
            <Button type="submit" className="bg-brand-orange hover:bg-brand-orange-dark">
              Search
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* Category Selection Dialog */}
      <Dialog open={isCategoryOpen} onOpenChange={setIsCategoryOpen}>
        <DialogContent className="top-1/3 max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Shop by Category</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            {/* All Products */}
            <button
              onClick={handleAllProducts}
              className="w-full text-left px-4 py-3 rounded-lg hover:bg-secondary/30 transition-colors font-medium border border-transparent hover:border-brand-orange"
            >
              All Products
            </button>

            {/* Categories */}
            {categories.map((category) => (
              <div key={category.id}>
                <button
                  onClick={() => handleCategorySelect(category.id)}
                  className="w-full text-left px-4 py-3 rounded-lg hover:bg-secondary/30 transition-colors font-medium border border-transparent hover:border-brand-orange"
                >
                  {category.name}
                </button>
                {/* Subcategories */}
                <div className="ml-4 space-y-2 mt-2">
                  {category.subcategories.map((sub) => (
                    <button
                      key={sub.id}
                      onClick={() => handleCategorySelect(sub.id)}
                      className="w-full text-left px-4 py-2 rounded-lg hover:bg-secondary/50 transition-colors text-sm text-muted-foreground hover:text-foreground"
                    >
                      {sub.name}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
