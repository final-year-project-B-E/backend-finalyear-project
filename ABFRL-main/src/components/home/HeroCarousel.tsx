import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const heroSlides = [
  {
    id: 1,
    title: 'Winter Collection',
    subtitle: 'Timeless Elegance',
    description: 'Discover our curated collection of luxury fashion pieces, crafted with exceptional materials.',
    image: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1920',
    cta: 'Shop Now',
    link: '/products?collection=winter',
  },
  {
    id: 2,
    title: 'New Arrivals',
    subtitle: 'Spring 2024',
    description: 'Fresh styles for the new season. Be the first to explore our latest designs.',
    image: 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=1920',
    cta: 'Explore',
    link: '/products?new=true',
  },
  {
    id: 3,
    title: 'Exclusive Sale',
    subtitle: 'Up to 50% Off',
    description: 'Limited time offer on selected premium items. Elevate your wardrobe for less.',
    image: 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=1920',
    cta: 'Shop Sale',
    link: '/products?sale=true',
  },
];

export const HeroCarousel = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  const nextSlide = useCallback(() => {
    setCurrentSlide((prev) => (prev + 1) % heroSlides.length);
  }, []);

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + heroSlides.length) % heroSlides.length);
  };

  useEffect(() => {
    if (!isAutoPlaying) return;
    const interval = setInterval(nextSlide, 5000);
    return () => clearInterval(interval);
  }, [isAutoPlaying, nextSlide]);

  return (
    <section 
      className="relative h-screen md:h-[85vh] min-h-[500px] md:min-h-[600px] overflow-hidden"
      onMouseEnter={() => setIsAutoPlaying(false)}
      onMouseLeave={() => setIsAutoPlaying(true)}
    >
      {heroSlides.map((slide, index) => (
        <div
          key={slide.id}
          className={cn(
            'absolute inset-0 transition-opacity duration-1000',
            index === currentSlide ? 'opacity-100 z-10' : 'opacity-0 z-0'
          )}
        >
          <div
            className="absolute inset-0 bg-cover bg-center transform scale-105 animate-[zoom_20s_ease-in-out_infinite]"
            style={{ backgroundImage: `url(${slide.image})` }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-background/70 via-background/40 to-background" />
          <div className="absolute inset-0 bg-gradient-to-r from-background/60 via-transparent to-transparent" />
          
          <div className="relative z-10 container h-full flex items-center px-4 md:px-0">
            <div className="max-w-2xl">
              <span 
                className={cn(
                  'inline-block text-brand-orange text-xs md:text-sm tracking-[0.3em] uppercase mb-2 md:mb-4 transition-all duration-700 delay-200',
                  index === currentSlide ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                )}
              >
                {slide.subtitle}
              </span>
              <h1
                className={cn(
                  'font-serif text-3xl md:text-5xl lg:text-7xl font-bold mb-3 md:mb-6 transition-all duration-700 delay-300',
                  index === currentSlide ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                )}
              >
                {slide.title}
              </h1>
              <p 
                className={cn(
                  'text-muted-foreground text-sm md:text-lg lg:text-xl mb-4 md:mb-8 transition-all duration-700 delay-400',
                  index === currentSlide ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                )}
              >
                {slide.description}
              </p>
              <div 
                className={cn(
                  'flex gap-2 md:gap-4 transition-all duration-700 delay-500 flex-wrap',
                  index === currentSlide ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
                )}
              >
                <Button asChild size="sm" className="bg-gradient-to-r from-brand-red via-brand-orange to-gold hover:from-brand-red-dark hover:via-brand-orange-dark hover:to-gold-dark text-white px-4 md:px-8 shadow-lg">
                  <Link to={slide.link}>{slide.cta}</Link>
                </Button>
                <Button asChild variant="outline" size="sm" className="border-foreground/20 hover:bg-foreground/5 px-4 md:px-8">
                  <Link to="/products">View All</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      ))}

      {/* Navigation Arrows */}
      <button
        onClick={prevSlide}
        className="absolute left-4 md:left-8 top-1/2 -translate-y-1/2 z-20 h-12 w-12 rounded-full bg-background/20 backdrop-blur-sm border border-border/30 flex items-center justify-center hover:bg-background/40 transition-colors"
        aria-label="Previous slide"
      >
        <ChevronLeft className="h-6 w-6" />
      </button>
      <button
        onClick={nextSlide}
        className="absolute right-4 md:right-8 top-1/2 -translate-y-1/2 z-20 h-12 w-12 rounded-full bg-background/20 backdrop-blur-sm border border-border/30 flex items-center justify-center hover:bg-background/40 transition-colors"
        aria-label="Next slide"
      >
        <ChevronRight className="h-6 w-6" />
      </button>

      {/* Dots Indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex gap-3">
        {heroSlides.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentSlide(index)}
            className={cn(
              'h-2 rounded-full transition-all duration-300',
              index === currentSlide ? 'w-8 bg-gradient-to-r from-brand-orange to-gold' : 'w-2 bg-foreground/30 hover:bg-foreground/50'
            )}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>
    </section>
  );
};
