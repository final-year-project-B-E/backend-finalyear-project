import { useState } from 'react';
import { Navigate, Link } from 'react-router-dom';
import { User, Mail, Phone, MapPin, ArrowLeft, Save, Edit2 } from 'lucide-react';
import { Layout } from '@/components/layout/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

const Profile = () => {
  const { user, isAuthenticated } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    address: user?.address || '',
    city: user?.city || '',
    state: user?.state || '',
    country: user?.country || '',
    postal_code: user?.postal_code || '',
  });

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSave = () => {
    setIsEditing(false);
    toast({ title: "Profile updated", description: "Your profile has been saved locally." });
  };

  return (
    <Layout>
      <div className="container py-8 md:py-12 max-w-4xl">
        <Link to="/" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to Home
        </Link>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <h1 className="font-serif text-3xl md:text-4xl font-bold mb-2">My Profile</h1>
            <p className="text-muted-foreground">Manage your account information</p>
          </div>
          {!isEditing ? (
            <Button onClick={() => setIsEditing(true)} className="bg-gradient-to-r from-brand-red via-brand-orange to-gold text-white">
              <Edit2 className="h-4 w-4 mr-2" /> Edit Profile
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setIsEditing(false)}>Cancel</Button>
              <Button onClick={handleSave} className="bg-gradient-to-r from-brand-red via-brand-orange to-gold text-white">
                <Save className="h-4 w-4 mr-2" /> Save
              </Button>
            </div>
          )}
        </div>

        <div className="bg-card rounded-lg border border-border overflow-hidden">
          <div className="brand-gradient p-6 md:p-8">
            <div className="flex items-center gap-4">
              <div className="h-20 w-20 rounded-full bg-background/20 flex items-center justify-center border-2 border-background/30">
                <User className="h-10 w-10 text-white" />
              </div>
              <div className="text-white">
                <h2 className="font-serif text-2xl font-bold">{user?.first_name || 'User'} {user?.last_name || ''}</h2>
                <p className="text-white/80 text-sm">{user?.email}</p>
              </div>
            </div>
          </div>

          <div className="p-6 md:p-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>First Name</Label>
                <Input name="first_name" value={formData.first_name} onChange={handleChange} disabled={!isEditing} className={cn(!isEditing && "bg-muted")} />
              </div>
              <div className="space-y-2">
                <Label>Last Name</Label>
                <Input name="last_name" value={formData.last_name} onChange={handleChange} disabled={!isEditing} className={cn(!isEditing && "bg-muted")} />
              </div>
            </div>
            <Separator />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Email</Label>
                <Input name="email" value={formData.email} disabled className="bg-muted" />
              </div>
              <div className="space-y-2">
                <Label>Phone</Label>
                <Input name="phone" value={formData.phone} onChange={handleChange} disabled={!isEditing} className={cn(!isEditing && "bg-muted")} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Profile;
