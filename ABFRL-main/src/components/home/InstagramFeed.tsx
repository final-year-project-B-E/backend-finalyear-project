import { Instagram } from 'lucide-react';

const instagramPosts = [
  'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400',
  'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=400',
  'https://images.unsplash.com/photo-1445205170230-053b83016050?w=400',
  'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400',
  'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400',
  'https://images.unsplash.com/photo-1539533018447-63fcce2678e3?w=400',
];

export const InstagramFeed = () => {
  return (
    <section className="py-16 md:py-20">
      <div className="container">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-2">
            <Instagram className="h-5 w-5 text-brand-orange" />
            <span className="text-sm tracking-[0.2em] uppercase text-muted-foreground">
              @luxefashion
            </span>
          </div>
          <h2 className="font-serif text-3xl md:text-4xl">Follow Our Journey</h2>
        </div>

        <div className="grid grid-cols-3 md:grid-cols-6 gap-2 md:gap-4">
          {instagramPosts.map((post, index) => (
            <a
              key={index}
              href="https://instagram.com"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative aspect-square overflow-hidden"
            >
              <img
                src={post}
                alt={`Instagram post ${index + 1}`}
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
              />
              <div className="absolute inset-0 bg-primary/0 group-hover:bg-primary/60 transition-colors flex items-center justify-center">
                <Instagram className="h-8 w-8 text-primary-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
};
