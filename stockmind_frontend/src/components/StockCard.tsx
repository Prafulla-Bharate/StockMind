import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown } from "lucide-react";
import { Link } from "react-router-dom";
import { formatCurrency } from "@/lib/utils";

interface StockCardProps {
  symbol: string;
  name: string;
  currency?: string;
  price: number;
  change: number;
  changePercent: number;
}

const StockCard = ({ symbol, name, currency, price, change, changePercent }: StockCardProps) => {
  const isPositive = change >= 0;

  return (
    <Link to={`/stock/${symbol}`}>
      <Card className="hover:shadow-lg transition-all duration-300 border-border bg-card/80 backdrop-blur-sm hover:border-primary/50 cursor-pointer">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl font-bold">{symbol}</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">{name}</p>
            </div>
            {isPositive ? (
              <TrendingUp className="h-5 w-5 text-success" />
            ) : (
              <TrendingDown className="h-5 w-5 text-destructive" />
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="text-3xl font-bold">{formatCurrency(price, currency, 2)}</div>
            <div className={`flex items-center gap-2 text-sm font-medium ${
              isPositive ? "text-success" : "text-destructive"
            }`}>
              <span>{isPositive ? "+" : ""}{change.toFixed(2)}</span>
              <span>({isPositive ? "+" : ""}{changePercent.toFixed(2)}%)</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};

export default StockCard;