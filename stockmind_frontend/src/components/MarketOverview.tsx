import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Activity, DollarSign } from "lucide-react";

interface MarketOverviewProps {
  stocksData: any[];
}

const MarketOverview = ({ stocksData }: MarketOverviewProps) => {
  const totalStocks = stocksData.length;
  const gainers = stocksData.filter(s => s.change > 0).length;
  const losers = stocksData.filter(s => s.change < 0).length;
  const avgChange = stocksData.reduce((sum, s) => sum + s.changePercent, 0) / totalStocks;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <Card className="border-border bg-card/80">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Stocks</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalStocks}</div>
          <p className="text-xs text-muted-foreground">
            Tracking popular stocks
          </p>
        </CardContent>
      </Card>
      
      <Card className="border-border bg-card/80">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Gainers</CardTitle>
          <TrendingUp className="h-4 w-4 text-success" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-success">{gainers}</div>
          <p className="text-xs text-muted-foreground">
            Stocks trading up
          </p>
        </CardContent>
      </Card>
      
      <Card className="border-border bg-card/80">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Losers</CardTitle>
          <TrendingDown className="h-4 w-4 text-destructive" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-destructive">{losers}</div>
          <p className="text-xs text-muted-foreground">
            Stocks trading down
          </p>
        </CardContent>
      </Card>
      
      <Card className="border-border bg-card/80">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Change</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className={`text-2xl font-bold ${avgChange >= 0 ? 'text-success' : 'text-destructive'}`}>
            {avgChange >= 0 ? '+' : ''}{avgChange.toFixed(2)}%
          </div>
          <p className="text-xs text-muted-foreground">
            Market average
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default MarketOverview;