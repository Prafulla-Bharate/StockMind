import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/auth.context";
import { portfolioService } from "@/services/api/portfolio.service";
import Navbar from "@/components/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Trash2, Info } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { formatCurrency, getCurrencySymbol } from "@/lib/utils";
import type { PortfolioHolding, WatchlistItem, PortfolioSummary } from "@/services/api/types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

const Portfolio = () => {
  const [holdings, setHoldings] = useState<PortfolioHolding[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    symbol: "",
    shares: "",
    averagePrice: "",
  });
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    if (!user) {
      navigate("/auth");
      return;
    }
    loadPortfolio();
    loadWatchlist();
    loadSummary();
  }, [user, navigate]);

  const loadPortfolio = async () => {
    try {
      const holdings = await portfolioService.getHoldings();
      setHoldings(holdings);
    } catch (error: any) {
      toast({
        title: "Error",
        description: "Failed to load portfolio",
        variant: "destructive",
      });
    }
  };

  const loadWatchlist = async () => {
    try {
      const watchlist = await portfolioService.getWatchlist();
      setWatchlist(watchlist);
    } catch (error: any) {
      toast({
        title: "Error",
        description: "Failed to load watchlist",
        variant: "destructive",
      });
    }
  };

  const addHolding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    try {
      await portfolioService.addHolding({
        symbol: formData.symbol.toUpperCase(),
        shares: parseFloat(formData.shares),
        averagePrice: parseFloat(formData.averagePrice),
        notes: null,
        purchaseDate: new Date().toISOString(),
      });

      toast({
        title: "Holding added",
        description: `${formData.symbol.toUpperCase()} has been added to your portfolio.`,
      });
      setIsDialogOpen(false);
      setFormData({ symbol: "", shares: "", averagePrice: "" });
      loadPortfolio();
      loadSummary();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to add holding",
        variant: "destructive",
      });
    }
  };

  const removeHolding = async (id: string) => {
    try {
      await portfolioService.deleteHolding(id);
      toast({
        title: "Holding removed",
        description: "The holding has been removed from your portfolio.",
      });
      loadPortfolio();
      loadSummary();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to remove holding",
        variant: "destructive",
      });
    }
  };

  const removeFromWatchlist = async (id: string) => {
    try {
      await portfolioService.removeFromWatchlist(id);
      toast({
        title: "Removed from watchlist",
      });
      loadWatchlist();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to remove from watchlist",
        variant: "destructive",
      });
    }
  };

  const loadSummary = async () => {
    try {
      const data = await portfolioService.getSummary();
      setSummary(data);
    } catch (error: any) {
      console.error("Failed to load portfolio summary:", error);
    }
  };

  const totalValue = holdings.reduce((sum, holding) => {
    return sum + (holding.shares * holding.averagePrice);
  }, 0);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">My Portfolio</h1>
          <p className="text-muted-foreground">
            Manage your investments and track performance
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Multi-Currency Summary */}
          {summary && summary.currencyBreakdown.length > 0 ? (
            <Card className="border-border bg-card/80 lg:col-span-2">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CardTitle>Currency Breakdown</CardTitle>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {summary.currencyBreakdown.map((breakdown) => {
                    const isPositive = breakdown.profitLoss >= 0;
                    return (
                      <div key={breakdown.currency} className="p-4 border border-border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm text-muted-foreground">Currency</p>
                          <p className="text-lg font-bold">{getCurrencySymbol(breakdown.currency)}</p>
                        </div>
                        <p className="text-2xl font-bold mb-1">
                          {formatCurrency(breakdown.totalValue, breakdown.currency, 2)}
                        </p>
                        <p className={`text-sm font-semibold ${
                          isPositive ? "text-success" : "text-destructive"
                        }`}>
                          {isPositive ? "+" : ""}{formatCurrency(breakdown.profitLoss, breakdown.currency, 2)} ({isPositive ? "+" : ""}{breakdown.profitLossPercent.toFixed(2)}%)
                        </p>
                        <p className="text-xs text-muted-foreground mt-2">
                          {breakdown.holdings} holding{breakdown.holdings !== 1 ? "s" : ""}
                        </p>
                      </div>
                    );
                  })}
                </div>
                <Alert className="mt-4 bg-blue-500/10 border-blue-500/20">
                  <Info className="h-4 w-4 text-blue-500" />
                  <AlertDescription className="text-xs">
                    {summary.note}
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          ) : (
            <>
              <Card className="border-border bg-card/80">
                <CardHeader>
                  <CardTitle>Total Holdings</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-4xl font-bold">{holdings.length}</p>
                </CardContent>
              </Card>
              
              <Card className="border-border bg-card/80">
                <CardHeader>
                  <CardTitle>Watchlist</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-4xl font-bold">{watchlist.length}</p>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        <Card className="border-border bg-card/80 mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>My Holdings</CardTitle>
              <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="bg-primary hover:bg-primary/90">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Holding
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Holding</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={addHolding} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="symbol">Stock Symbol</Label>
                      <Input
                        id="symbol"
                        value={formData.symbol}
                        onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                        placeholder="AAPL"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="shares">Number of Shares</Label>
                      <Input
                        id="shares"
                        type="number"
                        step="0.01"
                        value={formData.shares}
                        onChange={(e) => setFormData({ ...formData, shares: e.target.value })}
                        placeholder="10"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="price">Average Price</Label>
                      <Input
                        id="price"
                        type="number"
                        step="0.01"
                        value={formData.averagePrice}
                        onChange={(e) => setFormData({ ...formData, averagePrice: e.target.value })}
                        placeholder="150.00"
                        required
                      />
                    </div>
                    <Button type="submit" className="w-full bg-primary hover:bg-primary/90">
                      Add Holding
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </CardHeader>
          <CardContent>
            {holdings.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                No holdings yet. Add your first holding to start tracking.
              </p>
            ) : (
              <div className="space-y-4">
                {holdings.map((holding) => (
                  <div key={holding.id} className="flex items-center justify-between p-4 border border-border rounded-lg">
                    <div>
                      <h3 className="text-xl font-bold">{holding.symbol}</h3>
                      <p className="text-sm text-muted-foreground">
                        {holding.shares} shares @ {formatCurrency(holding.averagePrice, holding.currency, 2)}
                      </p>
                      <p className="text-lg font-semibold mt-1">
                        Total: {formatCurrency(holding.shares * holding.averagePrice, holding.currency, 2)}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeHolding(holding.id)}
                    >
                      <Trash2 className="h-5 w-5 text-destructive" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-border bg-card/80">
          <CardHeader>
            <CardTitle>Watchlist</CardTitle>
          </CardHeader>
          <CardContent>
            {watchlist.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                No stocks in your watchlist yet.
              </p>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {watchlist.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-4 border border-border rounded-lg">
                    <span className="text-lg font-bold">{item.symbol}</span>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeFromWatchlist(item.id)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Portfolio;