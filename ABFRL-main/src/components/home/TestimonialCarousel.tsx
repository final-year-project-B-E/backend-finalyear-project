import { useState } from 'react';
import { ChevronLeft, ChevronRight, Star, Quote } from 'lucide-react';
import { cn } from '@/lib/utils';

const testimonials = [
  {
    id: 1,
    name: 'Sarah Johnson',
    location: 'New York, NY',
    rating: 5,
    text: "The quality of the fabrics and the attention to detail is exceptional. I've never felt more elegant than when wearing pieces from this collection.",
    image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150',
  },
  {
    id: 2,
    name: 'Michael Chen',
    location: 'Los Angeles, CA',
    rating: 5,
    text: 'Finally found a brand that understands modern luxury. The bespoke suit I ordered fits perfectly and the service was impeccable.',
    image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
  },
  {
    id: 3,
    name: 'Emily Williams',
    location: 'Chicago, IL',
    rating: 5,
    text: 'From browsing to delivery, the entire experience was seamless. The evening gown I purchased exceeded all my expectations.',
    image: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150',
  },
  {
    id: 4,
    name: 'David Thompson',
    location: 'Miami, FL',
    rating: 5,
    text: "Outstanding craftsmanship and customer service. The cashmere overcoat is simply stunning. I'm a customer for life.",
    image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150',
  },
];

export const TestimonialCarousel = () => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const next = () => {
    setCurrentIndex((prev) => (prev + 1) % testimonials.length);
  };

  const prev = () => {
    setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  };

  return (
    <section className="py-20 md:py-28 bg-secondary/30">
      <div className="container">
        <div className="text-center mb-12">
          <h2 className="font-serif text-3xl md:text-4xl mb-2">What Our Clients Say</h2>
          <p className="text-muted-foreground">Trusted by thousands of discerning customers</p>
        </div>

        <div className="relative max-w-4xl mx-auto">
          {/* Quote Icon */}
          <div className="absolute -top-6 left-1/2 -translate-x-1/2">
            <Quote className="h-12 w-12 text-gold/20" />
          </div>

          {/* Testimonials */}
          <div className="relative overflow-hidden">
            <div
              className="flex transition-transform duration-500 ease-out"
              style={{ transform: `translateX(-${currentIndex * 100}%)` }}
            >
              {testimonials.map((testimonial) => (
                <div
                  key={testimonial.id}
                  className="w-full flex-shrink-0 px-4 md:px-12"
                >
                  <div className="text-center">
                    <div className="flex justify-center gap-1 mb-6">
                      {Array.from({ length: testimonial.rating }).map((_, i) => (
                        <Star key={i} className="h-5 w-5 fill-brand-orange text-brand-orange" />
                      ))}
                    </div>
                    <blockquote className="text-lg md:text-xl text-foreground/90 mb-8 italic leading-relaxed">
                      "{testimonial.text}"
                    </blockquote>
                    <div className="flex items-center justify-center gap-4">
                      <img
                        src={testimonial.image}
                        alt={testimonial.name}
                        className="h-14 w-14 rounded-full object-cover border-2 border-brand-orange/30"
                      />
                      <div className="text-left">
                        <div className="font-medium">{testimonial.name}</div>
                        <div className="text-sm text-muted-foreground">{testimonial.location}</div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Navigation */}
          <button
            onClick={prev}
            className="absolute left-0 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full bg-background border border-border flex items-center justify-center hover:bg-secondary transition-colors"
            aria-label="Previous testimonial"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <button
            onClick={next}
            className="absolute right-0 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full bg-background border border-border flex items-center justify-center hover:bg-secondary transition-colors"
            aria-label="Next testimonial"
          >
            <ChevronRight className="h-5 w-5" />
          </button>

          {/* Dots */}
          <div className="flex justify-center gap-2 mt-8">
            {testimonials.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={cn(
                  'h-2 w-2 rounded-full transition-all',
                  index === currentIndex ? 'w-6 bg-gradient-to-r from-brand-orange to-gold' : 'bg-foreground/20 hover:bg-foreground/40'
                )}
                aria-label={`Go to testimonial ${index + 1}`}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
