import { Link } from 'react-router-dom';
import { Facebook, Instagram, Twitter, Youtube, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useState } from 'react';
import { toast } from '@/hooks/use-toast';

export const Footer = () => {
  const [email, setEmail] = useState('');

  const handleNewsletterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
            toast({
        title: "Welcome to our newsletter",
        description: "Thank you for subscribing to our newsletter.",
      });
      setEmail('');
    }
  };

  return (
    <footer className="bg-primary text-primary-foreground">
      {/* Newsletter Section */}
      <div className="border-b border-primary-foreground/10">
        <div className="w-full px-4 md:px-0">
        <div className="md:container py-8 md:py-12">
          <div className="max-w-2xl mx-auto text-center">
            <h3 className="font-serif text-xl md:text-3xl mb-2">Join Our Newsletter</h3>
            <p className="text-primary-foreground/70 mb-6 text-sm">
              Subscribe to receive exclusive offers, early access to new collections, and style inspiration.
            </p>
            <form onSubmit={handleNewsletterSubmit} className="flex flex-col md:flex-row gap-2 max-w-md mx-auto">
              <Input
                type="email"
                placeholder="Your email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-primary-foreground/10 border-primary-foreground/20 text-primary-foreground placeholder:text-primary-foreground/50 focus:border-gold"
                required
              />
              <Button 
                type="submit" 
                className="bg-gradient-to-r from-brand-orange to-gold hover:from-brand-orange-dark hover:to-gold-dark text-white px-6 whitespace-nowrap"
              >
                Subscribe
              </Button>
            </form>
          </div>
        </div>
        </div>
      </div>

      {/* Main Footer */}
      <div className="w-full px-4 md:px-0">
        <div className="md:container py-8 md:py-12">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
          {/* Brand */}
          <div>
            <Link to="/" className="font-serif text-2xl tracking-[0.2em] mb-4 inline-block">
              RETAIL
            </Link>
            <p className="text-primary-foreground/70 text-sm leading-relaxed mb-4">
              Your destination for premium fashion, quality apparel, and the latest trends. 
              Bringing style, quality, and innovation to every wardrobe.
            </p>
            <div className="flex gap-4">
              <a href="#" className="text-primary-foreground/60 hover:text-brand-orange transition-colors">
                <Instagram className="h-5 w-5" />
              </a>
              <a href="#" className="text-primary-foreground/60 hover:text-brand-orange transition-colors">
                <Facebook className="h-5 w-5" />
              </a>
              <a href="#" className="text-primary-foreground/60 hover:text-brand-orange transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="#" className="text-primary-foreground/60 hover:text-brand-orange transition-colors">
                <Youtube className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Shop */}
          <div>
            <h4 className="font-serif text-lg mb-4">Shop</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/products?category=women" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Women
                </Link>
              </li>
              <li>
                <Link to="/products?category=men" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Men
                </Link>
              </li>
              <li>
                <Link to="/products?category=kids" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Kids
                </Link>
              </li>
              <li>
                <Link to="/products?featured=true" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  New Arrivals
                </Link>
              </li>
              <li>
                <Link to="/products" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  All Collections
                </Link>
              </li>
            </ul>
          </div>

          {/* Customer Care */}
          <div>
            <h4 className="font-serif text-lg mb-4">Customer Care</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/contact" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link to="/shipping" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Shipping & Returns
                </Link>
              </li>
              <li>
                <Link to="/size-guide" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Size Guide
                </Link>
              </li>
              <li>
                <Link to="/faq" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  FAQ
                </Link>
              </li>
              <li>
                <Link to="/track-order" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Track Your Order
                </Link>
              </li>
            </ul>
          </div>

          {/* About */}
          <div>
            <h4 className="font-serif text-lg mb-4">About Us</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/about" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Our Story
                </Link>
              </li>
              <li>
                <Link to="/sustainability" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Sustainability
                </Link>
              </li>
              <li>
                <Link to="/careers" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Careers
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/terms" className="text-primary-foreground/70 hover:text-gold transition-colors">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-primary-foreground/10 pb-20 md:pb-0">
        <div className="w-full px-4 md:px-0">
          <div className="md:container py-4 md:py-6">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <p className="text-primary-foreground/50 text-xs text-center md:text-left">
                © {new Date().getFullYear()} Premium Fashion & Retail. All rights reserved.
              </p>
              <div className="flex gap-4 text-xs text-primary-foreground/50">
                <span>Visa</span>
                <span>Mastercard</span>
                <span>Amex</span>
                <span>PayPal</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};
