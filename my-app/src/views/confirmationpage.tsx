import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AuthService } from 'services/auth';
import { useAuth } from 'contexts/AuthContext';
import { PageLayout } from 'components/layout/PageLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Activity, Mail, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

const ConfirmationPending: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();

  const registrationData = location.state?.registrationData;

  useEffect(() => {
    if (!registrationData) {
      navigate('/register');
      return;
    }
    processRegistration();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const processRegistration = async () => {
    if (!registrationData) return;
    setLoading(true);
    setError(null);
    try {
      const response = await AuthService.register(registrationData);
      if (response.email_confirmation_required) {
        setSuccess('Registration successful! Please check your email to confirm your account, then try logging in.');
      } else {
        await login();
        navigate('/');
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  if (!registrationData) return <div>Redirecting…</div>;

  return (
    <PageLayout className="flex items-center justify-center py-16 px-4">
      <div className="w-full max-w-sm animate-fade-in-up">
        <div className="flex justify-center mb-6">
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            <span className="font-bold text-xl">MediSage</span>
          </div>
        </div>

        <Card className="shadow-sm text-center">
          {loading && (
            <>
              <CardHeader className="pb-3">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Loader2 className="h-6 w-6 text-primary animate-spin" />
                </div>
                <CardTitle className="text-xl">Creating your account…</CardTitle>
                <CardDescription>Please wait while we set up your medical profile.</CardDescription>
              </CardHeader>
              <CardContent />
            </>
          )}

          {error && (
            <>
              <CardHeader className="pb-3">
                <CardTitle className="text-xl text-destructive">Registration failed</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
                <Button className="w-full" onClick={() => navigate('/register')}>
                  Try again
                </Button>
              </CardContent>
            </>
          )}

          {success && (
            <>
              <CardHeader className="pb-3">
                <div className="w-12 h-12 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Mail className="h-6 w-6 text-accent" />
                </div>
                <CardTitle className="text-xl">Check your inbox</CardTitle>
                <CardDescription>
                  We sent a confirmation link to your email. Click it to activate your account.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-accent justify-center">
                  <CheckCircle className="h-4 w-4" />Account created successfully
                </div>
                <p className="text-sm text-muted-foreground">{success}</p>
                <Button variant="outline" className="w-full" asChild>
                  <Link to="/login">Go to sign in</Link>
                </Button>
              </CardContent>
            </>
          )}
        </Card>
      </div>
    </PageLayout>
  );
};

export default ConfirmationPending;
