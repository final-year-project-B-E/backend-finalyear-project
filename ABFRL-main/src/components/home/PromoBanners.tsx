import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

const banners = [
  {
    id: 1,
    title: "Women's Collection",
    description: 'Elegant designs for every occasion',
    image: 'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=800',
    link: '/products?category=women',
    color: 'from-rose-900/80',
  },
  {
    id: 2,
    title: "Men's Essentials",
    description: 'Timeless pieces, modern fit',
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800',
    link: '/products?category=men',
    color: 'from-slate-900/80',
  },
];

export const PromoBanners = () => {
  return (
    <section className="py-8 md:py-16 lg:py-20">
      <div className="container">
        <div className="grid md:grid-cols-2 gap-3 md:gap-6">
          {banners.map((banner) => (
            <Link
              key={banner.id}
              to={banner.link}
              className="group relative aspect-[4/3] md:aspect-[16/9] overflow-hidden rounded-sm"
            >
              <img
                src={banner.image}
                alt={banner.title}
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className={`absolute inset-0 bg-gradient-to-r ${banner.color} via-transparent to-transparent`} />
              <div className="absolute inset-0 flex flex-col justify-center p-4 md:p-8 lg:p-12">
                <h3 className="font-serif text-xl md:text-2xl lg:text-3xl text-white mb-2">
                  {banner.title}
                </h3>
                <p className="text-white/80 text-xs md:text-sm lg:text-base mb-3 md:mb-4">
                  {banner.description}
                </p>
                <span className="text-brand-orange text-xs md:text-sm flex items-center gap-2 group-hover:gap-3 transition-all w-fit">
                  Shop Now <ArrowRight className="h-4 w-4" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
};

export const BigPromoBanner = () => {
  return (
    <section className="py-12 md:py-24 lg:py-32 relative overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1920)' }}
      />
      <div className="absolute inset-0 bg-primary/85" />
      <div className="container relative z-10 text-center text-primary-foreground px-4">
        <span className="text-brand-orange text-xs md:text-sm tracking-[0.3em] uppercase mb-2 md:mb-4 block">
          Limited Time Offer
        </span>
        <h2 className="font-serif text-3xl md:text-4xl lg:text-6xl mb-3 md:mb-4">
          Complimentary Shipping
        </h2>
        <p className="text-primary-foreground/70 max-w-lg mx-auto mb-6 md:mb-8 text-sm md:text-base lg:text-lg">
          Enjoy free shipping on all orders over $500. Plus, free returns within 30 days.
        </p>
        <div className="flex gap-2 md:gap-4 justify-center flex-wrap">
          <Button asChild size="lg" className="bg-gradient-to-r from-brand-red via-brand-orange to-gold hover:from-brand-red-dark hover:via-brand-orange-dark hover:to-gold-dark text-white px-8 shadow-lg">
            <Link to="/products">Shop Now</Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground/10">
            <Link to="/products?featured=true">View Featured</Link>
          </Button>
        </div>
      </div>
    </section>
  );
};
