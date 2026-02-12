import {
  Carousel,
  CarouselContent,
  CarouselItem,
} from '@/components/ui/carousel';
import Autoplay from 'embla-carousel-autoplay';
import { useRef } from 'react';

const brands = [
  { id: 1, name: 'Gucci', logo: 'GUCCI' },
  { id: 2, name: 'Prada', logo: 'PRADA' },
  { id: 3, name: 'Versace', logo: 'VERSACE' },
  { id: 4, name: 'Armani', logo: 'ARMANI' },
  { id: 5, name: 'Dior', logo: 'DIOR' },
  { id: 6, name: 'Chanel', logo: 'CHANEL' },
  { id: 7, name: 'Burberry', logo: 'BURBERRY' },
  { id: 8, name: 'Hermès', logo: 'HERMÈS' },
];

export const BrandCarousel = () => {
  const plugin = useRef(
    Autoplay({ delay: 2000, stopOnInteraction: false })
  );

  return (
    <section className="py-12 border-y border-border/50">
      <div className="container">
        <p className="text-center text-xs tracking-[0.3em] uppercase text-muted-foreground mb-8">
          As Featured In
        </p>
        <Carousel
          plugins={[plugin.current]}
          opts={{
            align: 'start',
            loop: true,
          }}
          className="w-full"
        >
          <CarouselContent className="-ml-4">
            {brands.map((brand) => (
              <CarouselItem
                key={brand.id}
                className="pl-4 basis-1/3 md:basis-1/4 lg:basis-1/6"
              >
                <div className="flex items-center justify-center h-16 px-4">
                  <span className="font-serif text-lg md:text-xl tracking-[0.2em] text-muted-foreground/50 hover:text-foreground transition-colors cursor-pointer">
                    {brand.logo}
                  </span>
                </div>
              </CarouselItem>
            ))}
          </CarouselContent>
        </Carousel>
      </div>
    </section>
  );
};
