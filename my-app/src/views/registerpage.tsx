import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { PageLayout } from 'components/layout/PageLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Activity, AlertCircle, Loader2 } from 'lucide-react';

const AGE_OPTIONS = ['Under 18', '18-25', '26-35', '36-45', '46-60', '61+'];
const GENDER_OPTIONS = ['Male', 'Female', 'Prefer not to say'];

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) { setError('Passwords do not match.'); return; }
    if (!name || !email || !password || !age || !gender) { setError('All fields are required.'); return; }
    setError(null);
    setLoading(true);
    navigate('/confirmation-pending', {
      state: { registrationData: { name, email, age, gender, password } },
    });
  };

  return (
    <PageLayout className="flex items-center justify-center py-16 px-4">
      <div className="w-full max-w-sm animate-fade-in-up">
        <div className="flex justify-center mb-6">
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            <span className="font-bold text-xl">MediSage</span>
          </div>
        </div>
        <Card className="shadow-sm">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-xl">Create your account</CardTitle>
            <CardDescription>Free to use. No personal health data required.</CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="reg-name">Username</Label>
                <Input id="reg-name" type="text" placeholder="Your name" autoComplete="name"
                  value={name} onChange={e => setName(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="reg-email">Email address</Label>
                <Input id="reg-email" type="email" placeholder="you@example.com" autoComplete="email"
                  value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Age range</Label>
                  <Select value={age} onValueChange={setAge}>
                    <SelectTrigger><SelectValue placeholder="Select age" /></SelectTrigger>
                    <SelectContent>
                      {AGE_OPTIONS.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Gender</Label>
                  <Select value={gender} onValueChange={setGender}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {GENDER_OPTIONS.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="reg-password">Password</Label>
                <Input id="reg-password" type="password" placeholder="At least 8 characters" autoComplete="new-password"
                  value={password} onChange={e => setPassword(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="reg-confirm">Confirm password</Label>
                <Input id="reg-confirm" type="password" placeholder="Repeat your password" autoComplete="new-password"
                  value={confirm} onChange={e => setConfirm(e.target.value)} required />
              </div>
            </CardContent>
            <CardFooter className="flex-col gap-4 pt-2">
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Creating account…</> : 'Create account'}
              </Button>
              <p className="text-sm text-muted-foreground text-center">
                Already have an account?{' '}
                <Link to="/login" className="text-primary hover:underline font-medium">Sign in</Link>
              </p>
              <p className="text-xs text-muted-foreground text-center">
                Do not enter real personal health information. Data is processed by Groq and stored on Supabase.
              </p>
            </CardFooter>
          </form>
        </Card>
      </div>
    </PageLayout>
  );
};

export default RegisterPage;
