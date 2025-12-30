import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/auth.context";
import { marketService } from "@/services/api/market.service";
import { portfolioService } from "@/services/api/portfolio.service";
import Navbar from "@/components/Navbar";
import StockCard from "@/components/StockCard";
import MarketOverview from "@/components/MarketOverview";
import StockSearch from "@/components/StockSearch";
import { marketWS } from "@/services/websocket/market.ws";
import { RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import type { StockData, WatchlistItem } from "@/services/api/types";
import { X } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const Dashboard = () => {
  const [stocksData, setStocksData] = useState<StockData[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();
    // Connect websocket once
    useEffect(() => {
      marketWS.connect();
      return () => {
        marketWS.disconnect();
      };
    }, []);

    // Subscribe to symbols currently displayed
    useEffect(() => {
      const symbols = stocksData.map((s) => s.symbol);
      symbols.forEach((sym) => marketWS.subscribe(sym));
    }, [stocksData]);

    // Handle real-time price updates
    useEffect(() => {
      const handleUpdate = (data: any) => {
        const sym = (data.symbol || data.ticker || "").toUpperCase();
        if (!sym) return;
        setStocksData((prev) =>
          prev.map((s) =>
            s.symbol === sym
              ? {
                  ...s,
                  price: data.price ?? s.price,
                  change: data.change ?? s.change,
                  changePercent: data.changePercent ?? s.changePercent,
                  volume: data.volume ?? s.volume,
                  marketCap: data.marketCap ?? s.marketCap,
                  currency: data.currency ?? s.currency,
                }
              : s
          )
        );
      };

      marketWS.on("price_update", handleUpdate);
      marketWS.on("ticker", handleUpdate);

      return () => {
        marketWS.off("price_update", handleUpdate);
        marketWS.off("ticker", handleUpdate);
      };
    }, []);

    useEffect(() => {
      if (!user) {
        navigate("/auth");
        return;
      }
      loadWatchlist();
    }, [user, navigate]);

  const loadWatchlist = async () => {
    try {
      const watchlistItems = await portfolioService.getWatchlist();
      setWatchlist(watchlistItems);
        // After loading watchlist, load stock data based on it
        const symbols = watchlistItems.map((w) => w.symbol);
        await loadStockData(symbols);
    } catch (error) {
      console.error("Error loading watchlist:", error);
      toast({
        title: "Error",
        description: "Failed to load watchlist",
        variant: "destructive",
      });
    }
  };

    const loadStockData = async (symbols?: string[]) => {
      setLoading(true);
      try {
        const targetSymbols = symbols && symbols.length > 0 ? symbols : [];

        if (targetSymbols.length === 0) {
          setStocksData([]);
          setLoading(false);
          return;
        }

        const promises = targetSymbols.map(async (symbol) => {
          return await marketService.getStockData(symbol);
        });

        const results = await Promise.all(promises);
        setStocksData(results);
      } catch (error) {
        console.error("Error loading stock data:", error);
        toast({
          title: "Error",
          description: "Failed to load stock data",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

  const removeFromWatchlist = async (id: string, symbol: string) => {
    try {
      await portfolioService.removeFromWatchlist(id);
      toast({
        title: "Removed from dashboard",
        description: `${symbol} has been removed from your dashboard.`,
      });
      loadWatchlist();
    } catch (error) {
      console.error("Error removing from watchlist:", error);
      toast({
        title: "Error",
        description: "Failed to remove stock from dashboard",
        variant: "destructive",
      });
    }
  };


  const filteredStocks = stocksData;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold mb-2">Market Dashboard</h1>
            <p className="text-muted-foreground">
              Real-time stock data and analysis powered by AI
            </p>
          </div>
            <Button 
              onClick={() => loadStockData()} 
            variant="outline"
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh Data
          </Button>
        </div>

        {!loading && stocksData.length > 0 && (
          <MarketOverview stocksData={stocksData} />
        )}

        <div className="my-8">
          <h2 className="text-2xl font-bold mb-4">Search Stocks</h2>
          <StockSearch onAdded={() => loadWatchlist()} />
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">Loading market data...</p>
          </div>
        ) : stocksData.length === 0 ? (
          <Card className="border-border bg-card/80">
            <CardContent className="py-16 text-center">
              <p className="text-lg font-semibold text-foreground mb-2">No stocks on your dashboard</p>
              <p className="text-muted-foreground mb-4">Use the search box above to add stocks you want to track.</p>
              <p className="text-sm text-muted-foreground">Search by symbol (e.g., AAPL, GOOGL) or company name.</p>
            </CardContent>
          </Card>
        ) : (
          <div>
            <h2 className="text-2xl font-bold mb-6">Your Dashboard</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredStocks.map((stock) => {
                const watchlistItem = watchlist.find(w => w.symbol === stock.symbol);
                return (
                  <div key={stock.symbol} className="relative group">
                    <StockCard
                      symbol={stock.symbol}
                      name={stock.name}
                      currency={stock.currency}
                      price={stock.price}
                      change={stock.change}
                      changePercent={stock.changePercent}
                    />
                    {user && watchlistItem && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive"
                        onClick={(e) => {
                          e.preventDefault();
                          removeFromWatchlist(watchlistItem.id, stock.symbol);
                        }}
                      >
                        <X className="h-5 w-5" />
                      </Button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;