import { Truck, RotateCcw, Shield, Gift } from 'lucide-react';

const features = [
  {
    icon: Truck,
    title: 'Free Shipping',
    description: 'On orders over $500',
  },
  {
    icon: RotateCcw,
    title: 'Easy Returns',
    description: '30-day return policy',
  },
  {
    icon: Shield,
    title: 'Secure Payment',
    description: '100% secure checkout',
  },
  {
    icon: Gift,
    title: 'Gift Wrapping',
    description: 'Complimentary wrapping',
  },
];

export const FeaturesBar = () => {
  return (
    <section className="border-y border-border/50 bg-secondary/20">
      <div className="container py-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="flex flex-col md:flex-row items-center text-center md:text-left gap-3"
            >
              <div className="h-12 w-12 rounded-full bg-gradient-to-br from-brand-red/10 via-brand-orange/10 to-gold/10 flex items-center justify-center">
                <feature.icon className="h-5 w-5 text-brand-orange" />
              </div>
              <div>
                <h4 className="font-medium text-sm">{feature.title}</h4>
                <p className="text-xs text-muted-foreground">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
