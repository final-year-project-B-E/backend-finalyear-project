import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { Mail, ArrowRight } from 'lucide-react';

export const NewsletterSection = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    
    toast({
      title: 'Successfully subscribed!',
      description: 'Thank you for joining our exclusive list.',
    });
    
    setEmail('');
    setIsLoading(false);
  };

  return (
    <section className="py-20 md:py-28 bg-primary text-primary-foreground">
      <div className="container">
        <div className="max-w-2xl mx-auto text-center">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-br from-brand-red/20 via-brand-orange/20 to-gold/20 mb-6">
            <Mail className="h-7 w-7 text-brand-orange" />
          </div>
          <h2 className="font-serif text-3xl md:text-4xl mb-4">
            Join Our Exclusive List
          </h2>
          <p className="text-primary-foreground/70 mb-8">
            Subscribe to receive early access to new collections, exclusive offers, 
            and curated style inspiration delivered to your inbox.
          </p>
          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
            <Input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-12 bg-primary-foreground/10 border-primary-foreground/20 text-primary-foreground placeholder:text-primary-foreground/50 focus-visible:ring-gold"
              required
            />
            <Button
              type="submit"
              disabled={isLoading}
              className="h-12 px-8 bg-gradient-to-r from-brand-orange to-gold hover:from-brand-orange-dark hover:to-gold-dark text-white whitespace-nowrap shadow-lg"
            >
              {isLoading ? 'Subscribing...' : 'Subscribe'}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </form>
          <p className="text-xs text-primary-foreground/50 mt-4">
            By subscribing, you agree to our Privacy Policy. Unsubscribe anytime.
          </p>
        </div>
      </div>
    </section>
  );
};
