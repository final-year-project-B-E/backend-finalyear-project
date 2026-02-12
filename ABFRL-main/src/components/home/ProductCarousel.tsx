import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ProductCard } from '@/components/product/ProductCard';
import { Product } from '@/types';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '@/components/ui/carousel';

interface ProductCarouselProps {
  title: string;
  subtitle?: string;
  products: Product[];
  viewAllLink?: string;
  viewAllText?: string;
}

export const ProductCarousel = ({
  title,
  subtitle,
  products,
  viewAllLink = '/products',
  viewAllText = 'View All',
}: ProductCarouselProps) => {
  return (
    <section className="py-12 md:py-16 lg:py-20">
      <div className="container">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-6 md:mb-10">
          <div>
            <h2 className="font-serif text-2xl md:text-3xl lg:text-4xl mb-2">{title}</h2>
            {subtitle && <p className="text-muted-foreground text-sm md:text-base">{subtitle}</p>}
          </div>
          <Button asChild variant="link" className="text-brand-orange p-0 hidden md:flex">
            <Link to={viewAllLink}>
              {viewAllText} <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>

        <Carousel
          opts={{
            align: 'start',
            loop: true,
          }}
          className="w-full"
        >
          <CarouselContent className="-ml-2 md:-ml-4">
            {products.map((product) => (
              <CarouselItem
                key={product.id}
                className="pl-2 md:pl-4 basis-1/2 md:basis-1/3 lg:basis-1/4"
              >
                <ProductCard product={product} />
              </CarouselItem>
            ))}
          </CarouselContent>
          <CarouselPrevious className="hidden md:flex -left-4 bg-background border-border hover:bg-secondary" />
          <CarouselNext className="hidden md:flex -right-4 bg-background border-border hover:bg-secondary" />
        </Carousel>

        <div className="mt-8 text-center md:hidden">
          <Button asChild variant="outline">
            <Link to={viewAllLink}>{viewAllText}</Link>
          </Button>
        </div>
      </div>
    </section>
  );
};
