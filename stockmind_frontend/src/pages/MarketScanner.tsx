import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { RefreshCw, TrendingUp, TrendingDown, Activity, Volume2, Target, Info } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/auth.context";
import { marketService } from "@/services/api/market.service";
import { formatCurrency } from "@/lib/utils";
import type { MarketScannerResponse, StockScanData } from "@/services/api/types";

const MarketScanner = () => {
  const [timeframe, setTimeframe] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [scanData, setScanData] = useState<MarketScannerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [noData, setNoData] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }
    loadScanData('daily');
  }, [user, navigate]);

  const loadScanData = async (tf: 'daily' | 'weekly' | 'monthly') => {
    setLoading(true);
    setNoData(false);
    setErrorMessage("");
    try {
      const data = await marketService.getMarketScanner(tf);
      setScanData(data);
      setNoData(false);
    } catch (error: any) {
      console.error('Error loading scan data:', error);
      
      const backendMessage = error.response?.data?.message || "";
      
      // Check if it's a 404 "No scan results" error
      if (error.response?.status === 404 || backendMessage.includes('No scan results')) {
        setNoData(true);
        setScanData(null);
        setErrorMessage("Market scanner data is not available yet. Backend scanner needs to run.");
        toast({
          title: "No Scan Data",
          description: "Market scanner data is not available yet. Backend scanner needs to run.",
        });
      } else if (error.response?.status === 500) {
        // Backend internal error
        setNoData(true);
        setScanData(null);
        setErrorMessage(backendMessage || "Scanner service has an internal error. Check backend logs for: 'success_response() got an unexpected keyword argument'");
        toast({
          title: "Backend Error",
          description: "Scanner service is having issues. Please contact support or check backend logs.",
          variant: "destructive",
        });
      } else {
        setNoData(true);
        setScanData(null);
        setErrorMessage(backendMessage || "Failed to load market scanner data");
        toast({
          title: "Error",
          description: backendMessage || "Failed to load market scanner data",
          variant: "destructive",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTimeframeChange = (tf: 'daily' | 'weekly' | 'monthly') => {
    setTimeframe(tf);
    loadScanData(tf);
  };

  const StockRow = ({ stock }: { stock: StockScanData }) => (
    <div
      onClick={() => navigate(`/stock/${stock.symbol}`)}
      className="flex items-center justify-between p-4 border-b border-border hover:bg-accent/50 cursor-pointer transition-colors"
    >
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-bold text-lg">{stock.symbol}</span>
          <Badge variant={stock.trend === 'Bullish' ? 'default' : 'secondary'}>
            {stock.trend}
          </Badge>
        </div>
        <span className="text-sm text-muted-foreground">{stock.name}</span>
      </div>
      <div className="flex items-center gap-6">
        <div className="text-right">
          <div className="font-semibold text-lg">{formatCurrency(stock.price, stock.currency, 2)}</div>
          <div className={`text-sm flex items-center gap-1 ${stock.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {stock.change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
          </div>
        </div>
        {stock.isUnusualVolume && (
          <Badge variant="outline" className="bg-orange-500/10 text-orange-500 border-orange-500/20">
            {stock.volumeRatio.toFixed(1)}x Volume
          </Badge>
        )}
        {stock.isBreakout && (
          <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
            Breakout
          </Badge>
        )}
      </div>
    </div>
  );

  if (!user) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading...</div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading market data...</div>
        </div>
      </div>
    );
  }

  if (noData) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
                Market Scanner
              </h1>
              <p className="text-muted-foreground mt-2">
                Real-time market analysis and opportunity detection
              </p>
            </div>
            <Button onClick={() => loadScanData(timeframe)} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Retry
            </Button>
          </div>

          <Alert className="max-w-2xl mx-auto">
            <Info className="h-4 w-4" />
            <AlertTitle>No Scanner Data Available</AlertTitle>
            <AlertDescription>
              The market scanner hasn't run yet. The backend Celery Beat scheduler runs market scans automatically:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong>Market data:</strong> Every 1 minute</li>
                <li><strong>Technical indicators:</strong> Every 5 minutes</li>
                <li><strong>News updates:</strong> Every 10 minutes</li>
              </ul>
              {errorMessage && (
                <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded text-sm">
                  <strong>Error details:</strong> {errorMessage}
                </div>
              )}
              <p className="mt-3">
                Please wait a few minutes and click "Retry", or ensure the backend Celery services are running.
              </p>
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  if (!scanData) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center">
          <div className="text-muted-foreground">No data available</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="container mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">
              Market Scanner
            </h1>
            <p className="text-muted-foreground mt-2">
              Real-time market analysis and opportunity detection
            </p>
          </div>
          <Button onClick={() => loadScanData(timeframe)} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Market Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Scanned</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{scanData.marketOverview.totalScanned}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Bullish</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">{scanData.marketOverview.bullish}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Bearish</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-500">{scanData.marketOverview.bearish}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Avg Change</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${scanData.marketOverview.avgChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {scanData.marketOverview.avgChange >= 0 ? '+' : ''}{scanData.marketOverview.avgChange}%
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Timeframe Selector */}
        <div className="flex gap-2">
          <Button
            variant={timeframe === 'daily' ? 'default' : 'outline'}
            onClick={() => handleTimeframeChange('daily')}
          >
            Daily
          </Button>
          <Button
            variant={timeframe === 'weekly' ? 'default' : 'outline'}
            onClick={() => handleTimeframeChange('weekly')}
          >
            Weekly
          </Button>
          <Button
            variant={timeframe === 'monthly' ? 'default' : 'outline'}
            onClick={() => handleTimeframeChange('monthly')}
          >
            Monthly
          </Button>
        </div>

        {/* Scanner Results */}
        <Tabs defaultValue="gainers" className="space-y-4">
          <TabsList className="grid grid-cols-5 w-full max-w-2xl">
            <TabsTrigger value="gainers">
              <TrendingUp className="h-4 w-4 mr-2" />
              Gainers
            </TabsTrigger>
            <TabsTrigger value="losers">
              <TrendingDown className="h-4 w-4 mr-2" />
              Losers
            </TabsTrigger>
            <TabsTrigger value="active">
              <Activity className="h-4 w-4 mr-2" />
              Most Active
            </TabsTrigger>
            <TabsTrigger value="volume">
              <Volume2 className="h-4 w-4 mr-2" />
              Unusual Volume
            </TabsTrigger>
            <TabsTrigger value="breakouts">
              <Target className="h-4 w-4 mr-2" />
              Breakouts
            </TabsTrigger>
          </TabsList>

          <TabsContent value="gainers">
            <Card>
              <CardHeader>
                <CardTitle>Top Gainers</CardTitle>
                <CardDescription>Stocks with the highest {timeframe} gains</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {scanData.gainers.map((stock: StockScanData) => (
                  <StockRow key={stock.symbol} stock={stock} />
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="losers">
            <Card>
              <CardHeader>
                <CardTitle>Top Losers</CardTitle>
                <CardDescription>Stocks with the highest {timeframe} losses</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {scanData.losers.map((stock: StockScanData) => (
                  <StockRow key={stock.symbol} stock={stock} />
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="active">
            <Card>
              <CardHeader>
                <CardTitle>Most Active</CardTitle>
                <CardDescription>Stocks with the highest trading volume</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {scanData.mostActive.map((stock: StockScanData) => (
                  <StockRow key={stock.symbol} stock={stock} />
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="volume">
            <Card>
              <CardHeader>
                <CardTitle>Unusual Volume</CardTitle>
                <CardDescription>Stocks with volume significantly above average</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {scanData.unusualVolume.length > 0 ? (
                  scanData.unusualVolume.map((stock: StockScanData) => (
                    <StockRow key={stock.symbol} stock={stock} />
                  ))
                ) : (
                  <div className="p-8 text-center text-muted-foreground">
                    No unusual volume detected
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="breakouts">
            <Card>
              <CardHeader>
                <CardTitle>Breakouts</CardTitle>
                <CardDescription>Stocks breaking through resistance levels</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {scanData.breakouts.length > 0 ? (
                  scanData.breakouts.map((stock: StockScanData) => (
                    <StockRow key={stock.symbol} stock={stock} />
                  ))
                ) : (
                  <div className="p-8 text-center text-muted-foreground">
                    No breakouts detected
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default MarketScanner;
