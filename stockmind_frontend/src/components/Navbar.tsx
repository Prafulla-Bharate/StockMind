import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { TrendingUp, User, LogOut, LineChart, Radar, Home, Briefcase, Sparkles, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/auth.context";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const { user, logout } = useAuth();

  const isActive = (path: string) => location.pathname === path;

  const handleSignOut = async () => {
    await logout();
    toast({
      title: "Signed out successfully",
    });
    navigate("/");
  };

  return (
    <nav className="border-b border-border bg-card/50 backdrop-blur-lg sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo - Always goes to homepage */}
          <Link 
            to="/" 
            className="flex items-center gap-2 group transition-all hover:scale-105"
          >
            <div className="relative">
              <TrendingUp className="h-8 w-8 text-primary transition-transform group-hover:rotate-12" />
              <Sparkles className="h-3 w-3 text-primary/60 absolute -top-1 -right-1 animate-pulse" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-emerald-400 bg-clip-text text-transparent">
              StockMind
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-2">
            {user ? (
              <>
                {/* Main Navigation */}
                <div className="hidden md:flex items-center gap-1 mr-2">
                  <Link to="/">
                    <Button 
                      variant={isActive("/") ? "default" : "ghost"}
                      className="transition-all hover:scale-105"
                    >
                      <Home className="h-4 w-4 mr-2" />
                      Home
                    </Button>
                  </Link>
                  <Link to="/dashboard">
                    <Button 
                      variant={isActive("/dashboard") ? "default" : "ghost"}
                      className="transition-all hover:scale-105"
                    >
                      <LineChart className="h-4 w-4 mr-2" />
                      Dashboard
                    </Button>
                  </Link>
                  <Link to="/scanner">
                    <Button 
                      variant={isActive("/scanner") ? "default" : "ghost"}
                      className="transition-all hover:scale-105"
                    >
                      <Radar className="h-4 w-4 mr-2" />
                      Scanner
                    </Button>
                  </Link>
                  <Link to="/portfolio">
                    <Button 
                      variant={isActive("/portfolio") ? "default" : "ghost"}
                      className="transition-all hover:scale-105"
                    >
                      <Briefcase className="h-4 w-4 mr-2" />
                      Portfolio
                    </Button>
                  </Link>
                </div>

                {/* User Menu */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="rounded-full hover:scale-110 transition-transform"
                    >
                      <Avatar className="h-9 w-9 border-2 border-primary/20">
                        <AvatarFallback className="bg-gradient-to-br from-primary to-emerald-400 text-white font-semibold">
                          {user.email?.charAt(0).toUpperCase() || "U"}
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuLabel>
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium">My Account</p>
                        <p className="text-xs text-muted-foreground truncate">
                          {user.email}
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {/* Mobile Navigation Links */}
                    <div className="md:hidden">
                      <DropdownMenuItem onClick={() => navigate("/")}>
                        <Home className="h-4 w-4 mr-2" />
                        Home
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate("/dashboard")}>
                        <LineChart className="h-4 w-4 mr-2" />
                        Dashboard
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate("/scanner")}>
                        <Radar className="h-4 w-4 mr-2" />
                        Scanner
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => navigate("/portfolio")}>
                        <Briefcase className="h-4 w-4 mr-2" />
                        Portfolio
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                    </div>
                    <DropdownMenuItem onClick={handleSignOut} className="text-destructive">
                      <LogOut className="h-4 w-4 mr-2" />
                      Sign Out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/auth">
                  <Button 
                    variant="ghost"
                    className="transition-all hover:scale-105"
                  >
                    <User className="h-4 w-4 mr-2" />
                    Sign In
                  </Button>
                </Link>
                <Link to="/auth">
                  <Button 
                    className="bg-gradient-to-r from-primary to-emerald-400 hover:from-primary/90 hover:to-emerald-400/90 transition-all hover:scale-105 shadow-lg"
                  >
                    Get Started
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;