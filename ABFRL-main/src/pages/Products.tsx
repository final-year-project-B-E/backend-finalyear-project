import { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Filter, X, Package } from 'lucide-react';
import { Layout } from '@/components/layout';
import { ProductGrid } from '@/components/product';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { mockProducts } from '@/data/mockData';
import { api } from '@/lib/api';
import { Product } from '@/types';

const Products = () => {
  const [searchParams] = useSearchParams();
  const categoryParam = searchParams.get('category');
  const searchQuery = searchParams.get('search');
  
  const [sortBy, setSortBy] = useState('newest');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(categoryParam);
  const [selectedOccasions, setSelectedOccasions] = useState<string[]>([]);
  const [priceRange, setPriceRange] = useState<[number, number]>([0, 5000]);
  const [products, setProducts] = useState<Product[]>(mockProducts);

  useEffect(() => {
    api.products().then((res) => setProducts(res.products)).catch(() => undefined);
  }, []);

  // Define categories for the frontend
  const categories = [
    { 
      id: 'women', 
      name: 'Women', 
      subcategories: [
        { id: 'women-dresses', name: 'Dresses' },
        { id: 'women-tops', name: 'Tops & Blouses' },
        { id: 'women-bottoms', name: 'Bottoms' },
        { id: 'women-outerwear', name: 'Outerwear' }
      ]
    },
    { 
      id: 'men', 
      name: 'Men', 
      subcategories: [
        { id: 'men-shirts', name: 'Shirts' },
        { id: 'men-pants', name: 'Pants' },
        { id: 'men-suits', name: 'Suits' },
        { id: 'men-outerwear', name: 'Outerwear' }
      ]
    },
    { 
      id: 'kids', 
      name: 'Kids', 
      subcategories: [
        { id: 'kids-girls', name: 'Girls' },
        { id: 'kids-boys', name: 'Boys' },
        { id: 'kids-baby', name: 'Baby' }
      ]
    }
  ];

  const occasions = [
    { id: 'wedding', name: 'Wedding' },
    { id: 'party', name: 'Party' },
    { id: 'casual', name: 'Casual' },
    { id: 'formal', name: 'Formal' },
    { id: 'office', name: 'Office' },
    { id: 'vacation', name: 'Vacation' }
  ];

  const clearFilters = () => {
    setSelectedCategory(null);
    setSelectedOccasions([]);
    setPriceRange([0, 5000]);
    setSortBy('newest');
  };

  const filteredProducts = useMemo(() => {
    let result = [...products];
    
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(p => 
        p.product_name.toLowerCase().includes(query) ||
        p.description?.toLowerCase().includes(query) ||
        p.dress_category.toLowerCase().includes(query)
      );
    }
    
    // Category filter
    if (selectedCategory) {
      if (selectedCategory === 'women') {
        result = result.filter(p => p.dress_category.startsWith('women-'));
      } else if (selectedCategory === 'men') {
        result = result.filter(p => p.dress_category.startsWith('men-'));
      } else if (selectedCategory === 'kids') {
        result = result.filter(p => p.dress_category.startsWith('kids-'));
      } else {
        result = result.filter(p => p.dress_category === selectedCategory);
      }
    }
    
    // Occasion filter
    if (selectedOccasions.length > 0) {
      result = result.filter(p => p.occasion && selectedOccasions.includes(p.occasion));
    }
    
    // Price filter
    result = result.filter(p => p.price >= priceRange[0] && p.price <= priceRange[1]);
    
    // Sorting
    switch (sortBy) {
      case 'price-low': 
        result.sort((a, b) => a.price - b.price); 
        break;
      case 'price-high': 
        result.sort((a, b) => b.price - a.price); 
        break;
      case 'featured': 
        result.sort((a, b) => (b.featured_dress ? 1 : 0) - (a.featured_dress ? 1 : 0)); 
        break;
      case 'newest': 
        result.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        ); 
        break;
    }
    
    return result;
  }, [products, searchQuery, selectedCategory, selectedOccasions, priceRange, sortBy]);

  const getCategoryTitle = () => {
    if (searchQuery) return `Search: "${searchQuery}"`;
    if (!selectedCategory) return 'All Products';
    
    // Check main categories
    const mainCat = categories.find(c => c.id === selectedCategory);
    if (mainCat) return mainCat.name;
    
    // Check subcategories
    for (const cat of categories) {
      const sub = cat.subcategories.find(s => s.id === selectedCategory);
      if (sub) return `${cat.name} - ${sub.name}`;
    }
    
    return 'Products';
  };

  // Add Badge component
  const Badge = ({ children, variant = 'default', className = '', ...props }: any) => (
    <span 
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        variant === 'secondary' 
          ? 'bg-secondary text-secondary-foreground' 
          : 'bg-primary text-primary-foreground'
      } ${className}`}
      {...props}
    >
      {children}
    </span>
  );

  const FilterContent = () => (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Filters</h3>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={clearFilters}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          Clear all
        </Button>
      </div>
      
      {/* Category Filter */}
      <div>
        <h4 className="font-medium mb-3 text-sm">Category</h4>
        <div className="space-y-2">
          <Button
            variant="ghost"
            onClick={() => setSelectedCategory(null)}
            className={`w-full justify-start text-sm px-2 ${!selectedCategory ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:text-foreground'}`}
          >
            All Products
          </Button>
          {categories.map((cat) => (
            <div key={cat.id} className="space-y-1">
              <Button
                variant="ghost"
                onClick={() => setSelectedCategory(cat.id)}
                className={`w-full justify-start text-sm px-2 ${selectedCategory === cat.id ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:text-foreground'}`}
              >
                {cat.name}
              </Button>
              <div className="ml-3 space-y-1">
                {cat.subcategories.map((sub) => (
                  <Button
                    key={sub.id}
                    variant="ghost"
                    onClick={() => setSelectedCategory(sub.id)}
                    className={`w-full justify-start text-xs px-2 ${selectedCategory === sub.id ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:text-foreground'}`}
                  >
                    {sub.name}
                  </Button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Price Range Filter */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-sm">Price Range</h4>
          <span className="text-xs text-muted-foreground">
            ${priceRange[0]} - ${priceRange[1]}
          </span>
        </div>
        <Slider
          value={priceRange}
          min={0}
          max={5000}
          step={100}
          onValueChange={(value) => setPriceRange(value as [number, number])}
          className="mb-4"
        />
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label htmlFor="min-price" className="text-xs">Min</Label>
            <Input
              id="min-price"
              type="number"
              value={priceRange[0]}
              onChange={(e) => setPriceRange([parseInt(e.target.value) || 0, priceRange[1]])}
              className="h-8 text-sm"
              min={0}
              max={priceRange[1]}
            />
          </div>
          <div>
            <Label htmlFor="max-price" className="text-xs">Max</Label>
            <Input
              id="max-price"
              type="number"
              value={priceRange[1]}
              onChange={(e) => setPriceRange([priceRange[0], parseInt(e.target.value) || 5000])}
              className="h-8 text-sm"
              min={priceRange[0]}
              max={5000}
            />
          </div>
        </div>
      </div>
      
      {/* Occasion Filter */}
      <div>
        <h4 className="font-medium mb-3 text-sm">Occasion</h4>
        <div className="space-y-2">
          {occasions.map((occ) => (
            <div key={occ.id} className="flex items-center space-x-2">
              <Checkbox
                id={`occasion-${occ.id}`}
                checked={selectedOccasions.includes(occ.id)}
                onCheckedChange={(checked) => {
                  if (checked) {
                    setSelectedOccasions(prev => [...prev, occ.id]);
                  } else {
                    setSelectedOccasions(prev => prev.filter(o => o !== occ.id));
                  }
                }}
              />
              <Label
                htmlFor={`occasion-${occ.id}`}
                className="text-sm font-normal cursor-pointer"
              >
                {occ.name}
              </Label>
            </div>
          ))}
        </div>
      </div>
      
      {/* Active Filters */}
      {(selectedCategory || selectedOccasions.length > 0 || priceRange[0] > 0 || priceRange[1] < 5000) && (
        <div className="pt-4 border-t">
          <h4 className="font-medium mb-2 text-sm">Active Filters</h4>
          <div className="flex flex-wrap gap-2">
            {selectedCategory && (
              <Badge variant="secondary" className="flex items-center gap-1">
                {getCategoryTitle()}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => setSelectedCategory(null)}
                />
              </Badge>
            )}
            {selectedOccasions.map(occasion => (
              <Badge key={occasion} variant="secondary" className="flex items-center gap-1">
                {occasions.find(o => o.id === occasion)?.name}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => setSelectedOccasions(prev => prev.filter(o => o !== occasion))}
                />
              </Badge>
            ))}
            {(priceRange[0] > 0 || priceRange[1] < 5000) && (
              <Badge variant="secondary" className="flex items-center gap-1">
                Price: ${priceRange[0]} - ${priceRange[1]}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => setPriceRange([0, 5000])}
                />
              </Badge>
            )}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <Layout>
      <div className="min-h-screen bg-background">
        <div className="container py-6 md:py-8">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 md:mb-8 gap-4">
            <div>
              <h1 className="font-serif text-2xl md:text-3xl lg:text-4xl mb-2">{getCategoryTitle()}</h1>
              <p className="text-sm md:text-base text-muted-foreground">
                {filteredProducts.length} products found
              </p>
            </div>
            <div className="flex items-center gap-2 md:gap-3 w-full md:w-auto">
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="flex-1 md:flex-none md:w-[180px] text-sm">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="newest">Newest Arrivals</SelectItem>
                  <SelectItem value="price-low">Price: Low to High</SelectItem>
                  <SelectItem value="price-high">Price: High to Low</SelectItem>
                  <SelectItem value="featured">Featured</SelectItem>
                </SelectContent>
              </Select>
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" size="icon" className="flex-shrink-0">
                    <Filter className="h-4 w-4" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="w-[300px] sm:w-[400px]">
                  <SheetHeader>
                    <SheetTitle>Filters</SheetTitle>
                  </SheetHeader>
                  <div className="mt-6">
                    <FilterContent />
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
          
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Desktop Filters */}
            <aside className="hidden lg:block w-64 flex-shrink-0">
              <div className="sticky top-24">
                <FilterContent />
              </div>
            </aside>
            
            {/* Main Content */}
            <div className="flex-1">
              {filteredProducts.length > 0 ? (
                <>
                  {/* Mobile Active Filters */}
                  <div className="lg:hidden mb-6">
                    <div className="flex flex-wrap gap-2">
                      {selectedCategory && (
                        <Badge variant="secondary" className="flex items-center gap-1">
                          {getCategoryTitle()}
                          <X 
                            className="h-3 w-3 cursor-pointer" 
                            onClick={() => setSelectedCategory(null)}
                          />
                        </Badge>
                      )}
                      {selectedOccasions.map(occasion => (
                        <Badge key={occasion} variant="secondary" className="flex items-center gap-1">
                          {occasions.find(o => o.id === occasion)?.name}
                          <X 
                            className="h-3 w-3 cursor-pointer" 
                            onClick={() => setSelectedOccasions(prev => prev.filter(o => o !== occasion))}
                          />
                        </Badge>
                      ))}
                      {(priceRange[0] > 0 || priceRange[1] < 5000) && (
                        <Badge variant="secondary" className="flex items-center gap-1">
                          Price: ${priceRange[0]} - ${priceRange[1]}
                          <X 
                            className="h-3 w-3 cursor-pointer" 
                            onClick={() => setPriceRange([0, 5000])}
                          />
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  {/* Product Grid */}
                  <ProductGrid products={filteredProducts} columns={3} />
                </>
              ) : (
                <div className="text-center py-16">
                  <div className="mb-6">
                    <Package className="h-16 w-16 text-muted-foreground/30 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold mb-2">No products found</h3>
                    <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                      Try adjusting your filters or search term to find what you're looking for.
                    </p>
                  </div>
                  <Button onClick={clearFilters}>Clear All Filters</Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Products;
