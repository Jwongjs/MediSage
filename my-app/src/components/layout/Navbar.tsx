import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from 'contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';
import { Menu, Activity, LogOut, User, Stethoscope, MessageSquare } from 'lucide-react';

const NAV_LINKS = [
  { label: 'Diagnosis', href: '/diagnosis', icon: Stethoscope },
  { label: 'Chat',      href: '/chatbot',   icon: MessageSquare },
] as const;

export const Navbar: React.FC = () => {
  const { loggedIn, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
    setOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-14 max-w-6xl items-center justify-between px-4">

        <Link to="/" className="flex items-center gap-2 font-semibold hover:opacity-80 transition-opacity">
          <Activity className="h-5 w-5 text-primary" />
          <span className="font-bold text-lg tracking-tight">MediSage</span>
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ label, href }) => (
            <Link key={href} to={href}
              className="px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground rounded-md hover:bg-secondary transition-colors">
              {label}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-2">
          {loggedIn ? (
            <>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/profile"><User className="h-4 w-4 mr-1.5" />Profile</Link>
              </Button>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-1.5" />Log out
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" asChild><Link to="/login">Log in</Link></Button>
              <Button size="sm" asChild><Link to="/register">Get started</Link></Button>
            </>
          )}
        </div>

        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon">
              <Menu className="h-5 w-5" /><span className="sr-only">Open menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-72">
            <div className="flex items-center gap-2 mb-6">
              <Activity className="h-5 w-5 text-primary" />
              <span className="font-bold text-lg">MediSage</span>
            </div>
            <nav className="flex flex-col gap-1">
              {NAV_LINKS.map(({ label, href, icon: Icon }) => (
                <Link key={href} to={href} onClick={() => setOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-secondary transition-colors">
                  <Icon className="h-4 w-4 text-muted-foreground" />{label}
                </Link>
              ))}
              <Separator className="my-3" />
              {loggedIn ? (
                <>
                  <Link to="/profile" onClick={() => setOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-secondary transition-colors">
                    <User className="h-4 w-4 text-muted-foreground" />Profile
                  </Link>
                  <button onClick={handleLogout}
                    className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-secondary transition-colors text-destructive w-full">
                    <LogOut className="h-4 w-4" />Log out
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium rounded-lg hover:bg-secondary transition-colors">
                    Log in
                  </Link>
                  <Link to="/register" onClick={() => setOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium bg-primary text-primary-foreground rounded-lg justify-center mt-1">
                    Get started
                  </Link>
                </>
              )}
            </nav>
          </SheetContent>
        </Sheet>

      </div>
    </header>
  );
};

export default Navbar;
