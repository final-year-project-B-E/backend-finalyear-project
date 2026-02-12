import { Layout } from '@/components/layout';
import { mockProducts } from '@/data/mockData';
import {
  HeroCarousel,
  ProductCarousel,
  CategoryCarousel,
  PromoBanners,
  BigPromoBanner,
  FeaturesBar,
  TestimonialCarousel,
  NewsletterSection,
  TrendingSection,
  InstagramFeed,
} from '@/components/home';

const Index = () => {
  const featuredProducts = mockProducts.filter((p) => p.featured_dress);
  const newArrivals = [...mockProducts].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ).slice(0, 8);
  const womenProducts = mockProducts.filter((p) => p.dress_category.startsWith('women')).slice(0, 8);
  const menProducts = mockProducts.filter((p) => p.dress_category.startsWith('men')).slice(0, 8);
  const bestSellers = mockProducts.filter((p) => p.stock < 30).slice(0, 8);

  return (
    <Layout>
      {/* Hero Carousel */}
      <HeroCarousel />

      {/* Features Bar */}
      <FeaturesBar />

      {/* Category Carousel */}
      <CategoryCarousel />

      {/* New Arrivals Carousel */}
      <ProductCarousel
        title="New Arrivals"
        subtitle="Fresh from our latest collection"
        products={newArrivals}
        viewAllLink="/products?sort=newest"
        viewAllText="Shop New"
      />

      {/* Promo Banners */}
      <PromoBanners />

      {/* Featured Products Carousel */}
      <div className="bg-secondary/30">
        <ProductCarousel
          title="Featured Collection"
          subtitle="Handpicked pieces for the discerning taste"
          products={featuredProducts}
          viewAllLink="/products?featured=true"
          viewAllText="View All Featured"
        />
      </div>

      {/* Trending Section */}
      <TrendingSection />

      {/* Best Sellers Carousel */}
      <ProductCarousel
        title="Best Sellers"
        subtitle="Our most-loved pieces"
        products={bestSellers}
        viewAllLink="/products?sort=popular"
        viewAllText="Shop Best Sellers"
      />

      {/* Big Promo Banner */}
      <BigPromoBanner />

      {/* Women's Collection Carousel */}
      <ProductCarousel
        title="Women's Edit"
        subtitle="Elegant designs for every occasion"
        products={womenProducts}
        viewAllLink="/products?category=women"
        viewAllText="Shop Women"
      />

      {/* Men's Collection Carousel */}
      <div className="bg-secondary/30">
        <ProductCarousel
          title="Men's Essentials"
          subtitle="Timeless pieces, modern fit"
          products={menProducts}
          viewAllLink="/products?category=men"
          viewAllText="Shop Men"
        />
      </div>

      {/* Testimonials */}
      <TestimonialCarousel />

      {/* Newsletter */}
      <NewsletterSection />

      {/* Instagram Feed */}
      <InstagramFeed />
    </Layout>
  );
};

export default Index;
