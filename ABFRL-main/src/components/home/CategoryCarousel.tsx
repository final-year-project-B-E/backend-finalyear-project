import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel';

const categoryItems = [
  { id: 'women-dresses', name: 'Dresses', image: 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600', count: 48 },
  { id: 'women-tops', name: 'Tops', image: 'https://images.unsplash.com/photo-1485968579580-b6d095142e6e?w=600', count: 36 },
  { id: 'men-suits', name: 'Suits', image: 'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600', count: 24 },
  { id: 'men-shirts', name: 'Shirts', image: 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=600', count: 52 },
  { id: 'women-outerwear', name: 'Outerwear', image: 'https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=600', count: 18 },
  { id: 'men-outerwear', name: "Men's Jackets", image: 'https://images.unsplash.com/photo-1544923246-77307dd628b8?w=600', count: 22 },
  { id: 'kids-girls', name: 'Girls', image: 'https://images.unsplash.com/photo-1518831959646-742c3a14ebf7?w=600', count: 30 },
  { id: 'kids-boys', name: 'Boys', image: 'https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?w=600', count: 28 },
];

export const CategoryCarousel = () => {
  return (
    <section className="py-12 md:py-16 lg:py-20 bg-secondary/30">
      <div className="container">
        <div className="text-center mb-6 md:mb-10">
          <h2 className="font-serif text-2xl md:text-3xl lg:text-4xl mb-2">Shop by Category</h2>
          <p className="text-muted-foreground text-sm md:text-base">Explore our curated collections</p>
        </div>

        <Carousel
          opts={{
            align: 'start',
            loop: true,
          }}
          className="w-full"
        >
          <CarouselContent className="-ml-2 md:-ml-4">
            {categoryItems.map((category) => (
              <CarouselItem
                key={category.id}
                className="pl-2 md:pl-4 basis-1/2 md:basis-1/4 lg:basis-1/5"
              >
                <Link
                  to={`/products?category=${category.id}`}
                  className="group block"
                >
                  <div className="relative aspect-square overflow-hidden rounded-full mb-4 border-2 border-transparent group-hover:border-brand-orange transition-colors">
                    <img
                      src={category.image}
                      alt={category.name}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-background/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <div className="text-center">
                    <h3 className="font-medium text-sm md:text-base group-hover:text-brand-orange transition-colors">
                      {category.name}
                    </h3>
                    <p className="text-xs text-muted-foreground">{category.count} items</p>
                  </div>
                </Link>
              </CarouselItem>
            ))}
          </CarouselContent>
          <CarouselPrevious className="hidden md:flex -left-4 bg-background border-border hover:bg-secondary" />
          <CarouselNext className="hidden md:flex -right-4 bg-background border-border hover:bg-secondary" />
        </Carousel>
      </div>
    </section>
  );
};
