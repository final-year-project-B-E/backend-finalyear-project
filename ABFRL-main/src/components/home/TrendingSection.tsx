import { Link } from 'react-router-dom';
import { ArrowRight, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';

const trendingItems = [
  {
    id: 1,
    title: 'Velvet Revival',
    description: 'Luxurious velvet pieces for the season',
    image: 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800',
    link: '/products?material=velvet',
  },
  {
    id: 2,
    title: 'Power Suits',
    description: 'Redefining modern elegance',
    image: 'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=800',
    link: '/products?category=men-suits',
  },
  {
    id: 3,
    title: 'Evening Glamour',
    description: 'Statement pieces for special nights',
    image: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=800',
    link: '/products?occasion=formal',
  },
];

export const TrendingSection = () => {
  return (
    <section className="py-16 md:py-20">
      <div className="container">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-10">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-brand-red/10 via-brand-orange/10 to-gold/10 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-brand-orange" />
            </div>
            <div>
              <h2 className="font-serif text-3xl md:text-4xl">Trending Now</h2>
            </div>
          </div>
          <Button asChild variant="link" className="text-brand-orange p-0 hidden md:flex">
            <Link to="/products">
              View All Trends <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {trendingItems.map((item, index) => (
            <Link
              key={item.id}
              to={item.link}
              className={`group relative overflow-hidden rounded-sm ${
                index === 0 ? 'md:row-span-2 aspect-[3/4] md:aspect-auto' : 'aspect-[4/3]'
              }`}
            >
              <img
                src={item.image}
                alt={item.title}
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-background/20 to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-6">
                <h3 className="font-serif text-xl md:text-2xl text-foreground mb-1">
                  {item.title}
                </h3>
                <p className="text-muted-foreground text-sm mb-3">{item.description}</p>
                <span className="text-brand-orange text-sm flex items-center gap-2 group-hover:gap-3 transition-all">
                  Explore <ArrowRight className="h-4 w-4" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
};
