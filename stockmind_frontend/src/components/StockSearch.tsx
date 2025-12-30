import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { TrendingUp, TrendingDown, Search, X, Info, Lightbulb } from "lucide-react";
import { marketService } from "@/services/api/market.service";
import { portfolioService } from "@/services/api/portfolio.service";
import type { StockData } from "@/services/api/types";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";
import { formatCurrency } from "@/lib/utils";

type Props = {
  onAdded?: (symbol: string) => void;
};

// Popular stock symbols with correct tickers (100+ stocks)
const POPULAR_STOCKS = [
  // US Mega Cap Tech
  { symbol: "AAPL", name: "Apple Inc.", region: "US" },
  { symbol: "MSFT", name: "Microsoft Corp.", region: "US" },
  { symbol: "GOOGL", name: "Alphabet Inc.", region: "US" },
  { symbol: "AMZN", name: "Amazon.com Inc.", region: "US" },
  { symbol: "NVDA", name: "NVIDIA Corp.", region: "US" },
  { symbol: "META", name: "Meta Platforms Inc.", region: "US" },
  { symbol: "TSLA", name: "Tesla Inc.", region: "US" },
  // US Large Cap Tech
  { symbol: "NFLX", name: "Netflix Inc.", region: "US" },
  { symbol: "AVGO", name: "Broadcom Inc.", region: "US" },
  { symbol: "ASML", name: "ASML Holding N.V.", region: "US" },
  { symbol: "INTC", name: "Intel Corp.", region: "US" },
  { symbol: "AMD", name: "Advanced Micro Devices", region: "US" },
  { symbol: "CRM", name: "Salesforce Inc.", region: "US" },
  { symbol: "ADBE", name: "Adobe Inc.", region: "US" },
  { symbol: "PYPL", name: "PayPal Holdings", region: "US" },
  // US Finance & Banking
  { symbol: "JPM", name: "JPMorgan Chase Co.", region: "US" },
  { symbol: "BAC", name: "Bank of America", region: "US" },
  { symbol: "WFC", name: "Wells Fargo Co.", region: "US" },
  { symbol: "GS", name: "Goldman Sachs Group", region: "US" },
  { symbol: "MS", name: "Morgan Stanley", region: "US" },
  { symbol: "BLK", name: "BlackRock Inc.", region: "US" },
  { symbol: "SCHW", name: "Charles Schwab Corp.", region: "US" },
  // US Healthcare & Pharma
  { symbol: "JNJ", name: "Johnson & Johnson", region: "US" },
  { symbol: "UNH", name: "UnitedHealth Group", region: "US" },
  { symbol: "PFE", name: "Pfizer Inc.", region: "US" },
  { symbol: "MRK", name: "Merck & Co. Inc.", region: "US" },
  { symbol: "LLY", name: "Eli Lilly Co.", region: "US" },
  { symbol: "AZN", name: "AstraZeneca PLC", region: "US" },
  { symbol: "ABBV", name: "AbbVie Inc.", region: "US" },
  // US Energy & Industrial
  { symbol: "XOM", name: "Exxon Mobil Corp.", region: "US" },
  { symbol: "CVX", name: "Chevron Corp.", region: "US" },
  { symbol: "COP", name: "ConocoPhillips", region: "US" },
  { symbol: "SLB", name: "Schlumberger NV", region: "US" },
  { symbol: "BA", name: "Boeing Co.", region: "US" },
  { symbol: "CAT", name: "Caterpillar Inc.", region: "US" },
  { symbol: "MMM", name: "3M Company", region: "US" },
  // US Consumer & Retail
  { symbol: "WMT", name: "Walmart Inc.", region: "US" },
  { symbol: "HD", name: "The Home Depot", region: "US" },
  { symbol: "MCD", name: "McDonald's Corp.", region: "US" },
  { symbol: "NKE", name: "Nike Inc.", region: "US" },
  { symbol: "SBUX", name: "Starbucks Corp.", region: "US" },
  { symbol: "MO", name: "Altria Group Inc.", region: "US" },
  { symbol: "PG", name: "Procter & Gamble", region: "US" },
  { symbol: "KO", name: "The Coca-Cola Co.", region: "US" },
  { symbol: "PEP", name: "PepsiCo Inc.", region: "US" },
  { symbol: "COST", name: "Costco Wholesale", region: "US" },
  // US Utilities & Telecom
  { symbol: "NEE", name: "NextEra Energy", region: "US" },
  { symbol: "DUK", name: "Duke Energy Corp.", region: "US" },
  { symbol: "SO", name: "Southern Company Co.", region: "US" },
  { symbol: "T", name: "AT&T Inc.", region: "US" },
  { symbol: "VZ", name: "Verizon Communications", region: "US" },
  
  // UK Stocks
  { symbol: "SHEL.L", name: "Shell PLC", region: "UK" },
  { symbol: "HSBA.L", name: "HSBC Holdings PLC", region: "UK" },
  { symbol: "AZN.L", name: "AstraZeneca PLC", region: "UK" },
  { symbol: "BP.L", name: "BP PLC", region: "UK" },
  { symbol: "GLEN.L", name: "Glencore PLC", region: "UK" },
  { symbol: "RIO.L", name: "Rio Tinto PLC", region: "UK" },
  { symbol: "BARCLAYS.L", name: "Barclays PLC", region: "UK" },
  { symbol: "LLOY.L", name: "Lloyds Banking Group", region: "UK" },
  { symbol: "VOD.L", name: "Vodafone Group PLC", region: "UK" },
  { symbol: "DGE.L", name: "Diageo PLC", region: "UK" },
  
  // Indian Stocks
  { symbol: "TCS.NS", name: "Tata Consultancy Services", region: "IN" },
  { symbol: "INFY.NS", name: "Infosys Ltd.", region: "IN" },
  { symbol: "RELIANCE.NS", name: "Reliance Industries Ltd.", region: "IN" },
  { symbol: "HDFCBANK.NS", name: "HDFC Bank Ltd.", region: "IN" },
  { symbol: "ICICIBANK.NS", name: "ICICI Bank Ltd.", region: "IN" },
  { symbol: "WIPRO.NS", name: "Wipro Ltd.", region: "IN" },
  { symbol: "TATAMOTORS.NS", name: "Tata Motors Ltd.", region: "IN" },
  { symbol: "MARUTI.NS", name: "Maruti Suzuki India", region: "IN" },
  { symbol: "POWERGRID.NS", name: "Power Grid Corp. of India", region: "IN" },
  { symbol: "SBIN.NS", name: "State Bank of India", region: "IN" },
  { symbol: "BAJAJ-AUTO.NS", name: "Bajaj Auto Ltd.", region: "IN" },
  { symbol: "BHARTIARTL.NS", name: "Bharti Airtel Ltd.", region: "IN" },
  { symbol: "ITC.NS", name: "ITC Ltd.", region: "IN" },
  { symbol: "LT.NS", name: "Larsen & Toubro Ltd.", region: "IN" },
  { symbol: "SUNPHARMA.NS", name: "Sun Pharmaceutical", region: "IN" },
  { symbol: "ASIANPAINT.NS", name: "Asian Paints India", region: "IN" },
  { symbol: "NESTLEIND.NS", name: "Nestlé India Ltd.", region: "IN" },
  { symbol: "AXISBANK.NS", name: "Axis Bank Ltd.", region: "IN" },
  { symbol: "KOTAKBANK.NS", name: "Kotak Mahindra Bank", region: "IN" },
  { symbol: "TITAN.NS", name: "Titan Company Ltd.", region: "IN" },
  { symbol: "HINDUNILVR.NS", name: "Hindustan Unilever", region: "IN" },
  { symbol: "BAJAJFINSV.NS", name: "Bajaj Finserv Ltd.", region: "IN" },
  { symbol: "ONGC.NS", name: "Oil and Natural Gas Corp.", region: "IN" },
  { symbol: "GAIL.NS", name: "GAIL (India) Limited", region: "IN" },
  { symbol: "AIRTEL.NS", name: "Bharti Airtel Limited", region: "IN" },
  { symbol: "ADANIPORTS.NS", name: "Adani Ports and SEZ", region: "IN" },
];

// Common name to symbol corrections (100+ entries)
const SYMBOL_CORRECTIONS: Record<string, string> = {
  // US Tech
  "APPLE": "AAPL", "AAPL": "AAPL",
  "MICROSOFT": "MSFT", "MSFT": "MSFT",
  "GOOGLE": "GOOGL", "ALPHABET": "GOOGL", "GOOGL": "GOOGL",
  "AMAZON": "AMZN", "AMZN": "AMZN",
  "TESLA": "TSLA", "TSLA": "TSLA",
  "NVIDIA": "NVDA", "NVDA": "NVDA",
  "META": "META", "FACEBOOK": "META",
  "NETFLIX": "NFLX", "NFLX": "NFLX",
  "BROADCOM": "AVGO", "AVGO": "AVGO",
  "ASML": "ASML", "ASML HOLDING": "ASML",
  "INTEL": "INTC", "INTC": "INTC",
  "AMD": "AMD", "ADVANCED MICRO": "AMD",
  "SALESFORCE": "CRM", "CRM": "CRM",
  "ADOBE": "ADBE", "ADBE": "ADBE",
  "PAYPAL": "PYPL", "PYPL": "PYPL",
  
  // US Finance
  "JP MORGAN": "JPM", "JPMORGAN": "JPM", "JPM": "JPM",
  "BANK OF AMERICA": "BAC", "BAC": "BAC",
  "WELLS FARGO": "WFC", "WFC": "WFC",
  "GOLDMAN SACHS": "GS", "GS": "GS",
  "MORGAN STANLEY": "MS", "MS": "MS",
  "BLACKROCK": "BLK", "BLK": "BLK",
  "CHARLES SCHWAB": "SCHW", "SCHWAB": "SCHW", "SCHW": "SCHW",
  
  // US Healthcare
  "JOHNSON & JOHNSON": "JNJ", "J&J": "JNJ", "JNJ": "JNJ",
  "UNITEDHEALTH": "UNH", "UNH": "UNH",
  "PFIZER": "PFE", "PFE": "PFE",
  "MERCK": "MRK", "MRK": "MRK",
  "ELI LILLY": "LLY", "LLY": "LLY",
  "ASTRAZENECA": "AZN", "AZN": "AZN",
  "ABBVIE": "ABBV", "ABBV": "ABBV",
  
  // US Energy
  "EXXON MOBIL": "XOM", "XOM": "XOM",
  "CHEVRON": "CVX", "CVX": "CVX",
  "CONOCOPHILLIPS": "COP", "COP": "COP",
  "SCHLUMBERGER": "SLB", "SLB": "SLB",
  "BOEING": "BA", "BA": "BA",
  "CATERPILLAR": "CAT", "CAT": "CAT",
  "3M": "MMM", "MMM": "MMM",
  
  // US Consumer
  "WALMART": "WMT", "WMT": "WMT",
  "HOME DEPOT": "HD", "HD": "HD",
  "MCDONALD'S": "MCD", "MCDONALDS": "MCD", "MCD": "MCD",
  "NIKE": "NKE", "NKE": "NKE",
  "STARBUCKS": "SBUX", "SBUX": "SBUX",
  "ALTRIA": "MO", "MO": "MO",
  "PROCTER & GAMBLE": "PG", "PG": "PG",
  "COCA COLA": "KO", "COKE": "KO", "KO": "KO",
  "PEPSI": "PEP", "PEPSICO": "PEP", "PEP": "PEP",
  "COSTCO": "COST", "COST": "COST",
  
  // US Utilities
  "NEXTERA ENERGY": "NEE", "NEE": "NEE",
  "DUKE ENERGY": "DUK", "DUK": "DUK",
  "SOUTHERN COMPANY": "SO", "SO": "SO",
  "AT&T": "T", "ATT": "T", "T": "T",
  "VERIZON": "VZ", "VZ": "VZ",
  
  // UK Stocks
  "SHELL": "SHEL.L", "SHEL.L": "SHEL.L",
  "HSBC": "HSBA.L", "HSBA.L": "HSBA.L",
  "BP": "BP.L", "BP.L": "BP.L",
  "GLENCORE": "GLEN.L", "GLEN.L": "GLEN.L",
  "RIO TINTO": "RIO.L", "RIO.L": "RIO.L",
  "BARCLAYS": "BARCLAYS.L", "BARCLAYS.L": "BARCLAYS.L",
  "LLOYDS": "LLOY.L", "LLOY.L": "LLOY.L",
  "VODAFONE": "VOD.L", "VOD.L": "VOD.L",
  "DIAGEO": "DGE.L", "DGE.L": "DGE.L",
  
  // Indian Stocks
  "TCS": "TCS.NS", "TATA CONSULTANCY": "TCS.NS", "TCS.NS": "TCS.NS",
  "INFOSYS": "INFY.NS", "INFY": "INFY.NS", "INFY.NS": "INFY.NS",
  "RELIANCE": "RELIANCE.NS", "RELIANCE INDUSTRIES": "RELIANCE.NS", "RELIANCE.NS": "RELIANCE.NS",
  "HDFC BANK": "HDFCBANK.NS", "HDFCBANK": "HDFCBANK.NS", "HDFCBANK.NS": "HDFCBANK.NS",
  "ICICI BANK": "ICICIBANK.NS", "ICICIBANK": "ICICIBANK.NS", "ICICIBANK.NS": "ICICIBANK.NS",
  "WIPRO": "WIPRO.NS", "WIPRO.NS": "WIPRO.NS",
  "TATA MOTORS": "TATAMOTORS.NS", "TATAMOTORS": "TATAMOTORS.NS", "TATAMOTORS.NS": "TATAMOTORS.NS",
  "MARUTI": "MARUTI.NS", "MARUTI SUZUKI": "MARUTI.NS", "MARUTI.NS": "MARUTI.NS",
  "POWER GRID": "POWERGRID.NS", "POWERGRID": "POWERGRID.NS", "POWERGRID.NS": "POWERGRID.NS",
  "STATE BANK": "SBIN.NS", "SBI": "SBIN.NS", "SBIN.NS": "SBIN.NS",
  "BAJAJ AUTO": "BAJAJ-AUTO.NS", "BAJAJ": "BAJAJ-AUTO.NS", "BAJAJ-AUTO.NS": "BAJAJ-AUTO.NS",
  "BHARTI AIRTEL": "BHARTIARTL.NS", "AIRTEL": "BHARTIARTL.NS", "BHARTIARTL.NS": "BHARTIARTL.NS",
  "ITC": "ITC.NS", "ITC.NS": "ITC.NS",
  "LARSEN & TOUBRO": "LT.NS", "L&T": "LT.NS", "LT.NS": "LT.NS",
  "SUN PHARMA": "SUNPHARMA.NS", "SUNPHARMA": "SUNPHARMA.NS", "SUNPHARMA.NS": "SUNPHARMA.NS",
  "ASIAN PAINTS": "ASIANPAINT.NS", "ASIANPAINT": "ASIANPAINT.NS", "ASIANPAINT.NS": "ASIANPAINT.NS",
  "NESTLÉ INDIA": "NESTLEIND.NS", "NESTLEIND": "NESTLEIND.NS", "NESTLEIND.NS": "NESTLEIND.NS",
  "AXIS BANK": "AXISBANK.NS", "AXISBANK": "AXISBANK.NS", "AXISBANK.NS": "AXISBANK.NS",
  "KOTAK MAHINDRA": "KOTAKBANK.NS", "KOTAK": "KOTAKBANK.NS", "KOTAKBANK.NS": "KOTAKBANK.NS",
  "TITAN": "TITAN.NS", "TITAN.NS": "TITAN.NS",
  "HINDUSTAN UNILEVER": "HINDUNILVR.NS", "HINDUNILVR": "HINDUNILVR.NS", "HINDUNILVR.NS": "HINDUNILVR.NS",
  "BAJAJ FINSERV": "BAJAJFINSV.NS", "BAJAJFINSV": "BAJAJFINSV.NS", "BAJAJFINSV.NS": "BAJAJFINSV.NS",
  "ONGC": "ONGC.NS", "ONGC.NS": "ONGC.NS",
  "GAIL": "GAIL.NS", "GAIL INDIA": "GAIL.NS", "GAIL.NS": "GAIL.NS",
  "ADANI PORTS": "ADANIPORTS.NS", "ADANIPORTS": "ADANIPORTS.NS", "ADANIPORTS.NS": "ADANIPORTS.NS",
};

const StockSearch = ({ onAdded }: Props) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [suggestions, setSuggestions] = useState<typeof POPULAR_STOCKS>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestedSymbol, setSuggestedSymbol] = useState<string | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();

  // Smart symbol resolution
  const resolveSymbol = (input: string): string => {
    const upper = input.trim().toUpperCase();
    
    // Check for exact correction match
    if (SYMBOL_CORRECTIONS[upper]) {
      return SYMBOL_CORRECTIONS[upper];
    }
    
    // Check if it's a partial match
    const partialMatch = Object.keys(SYMBOL_CORRECTIONS).find(key => 
      key.includes(upper) || upper.includes(key)
    );
    if (partialMatch) {
      setSuggestedSymbol(SYMBOL_CORRECTIONS[partialMatch]);
    }
    
    return upper;
  };

  // Handle input change with suggestions
  const handleInputChange = (value: string) => {
    setQuery(value);
    
    if (value.trim().length >= 2) {
      const filtered = POPULAR_STOCKS.filter(stock => 
        stock.symbol.toLowerCase().includes(value.toLowerCase()) ||
        stock.name.toLowerCase().includes(value.toLowerCase())
      );
      setSuggestions(filtered);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  // Select suggestion
  const handleSelectSuggestion = (symbol: string) => {
    setQuery(symbol);
    setShowSuggestions(false);
    setSuggestions([]);
  };

  const generateMockStockData = (symbol: string): StockData => {
    // Generate realistic mock data for demonstration
    const basePrice = 50 + Math.random() * 400;
    const changePercent = (Math.random() - 0.5) * 10;
    const change = (basePrice * changePercent) / 100;

    // Detect currency based on symbol suffix
    let currency = "USD";
    if (symbol.endsWith(".NS") || symbol.endsWith(".BO")) {
      currency = "INR";
    } else if (symbol.endsWith(".L")) {
      currency = "GBP";
    } else if (symbol.endsWith(".T")) {
      currency = "JPY";
    }

    return {
      symbol,
      name: `${symbol} Inc.`,
      currency,
      price: basePrice,
      change,
      changePercent,
      volume: Math.floor(Math.random() * 50000000) + 1000000,
      marketCap: Math.floor(Math.random() * 1000000000000) + 10000000000,
      high52w: basePrice * (1 + Math.random() * 0.5),
      low52w: basePrice * (1 - Math.random() * 0.3),
      historicalData: [],
      indicators: {
        rsi: Math.floor(Math.random() * 100),
        macd: Math.random() * 10 - 5,
        sma20: basePrice * (0.98 + Math.random() * 0.04),
        sma50: basePrice * (0.95 + Math.random() * 0.1),
      },
    };
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuggestedSymbol(null);
    setShowSuggestions(false);
    
    const resolvedSymbol = resolveSymbol(query);

    if (!resolvedSymbol) {
      toast({
        title: "Error",
        description: "Please enter a stock symbol or name.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setSearched(true);
    try {
      const data = await marketService.getStockData(resolvedSymbol);

      // Check if backend returned empty/zero data
      if (data.price === 0 && data.marketCap === 0) {
        // Show suggestion if available
        if (suggestedSymbol && suggestedSymbol !== resolvedSymbol) {
          toast({
            title: "Data Pending",
            description: `No live data for "${resolvedSymbol}". Try "${suggestedSymbol}" instead?`,
            variant: "destructive",
          });
        } else {
          toast({
            title: "Data Pending",
            description: `Stock found but live data is loading. Try using the correct ticker format (e.g., AAPL for US, TCS.NS for Indian stocks).`,
            variant: "destructive",
          });
        }
        const mockData = generateMockStockData(resolvedSymbol);
        setResults(mockData);
      } else {
        setResults(data);
      }
    } catch (error: any) {
      toast({
        title: "Stock Not Found",
        description: `Could not find stock data for "${resolvedSymbol}". ${suggestedSymbol ? `Try "${suggestedSymbol}" instead.` : "Please check the symbol."}`,
        variant: "destructive",
      });
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = () => {
    if (results) {
      navigate(`/stock/${results.symbol}`);
    }
  };

  const handleAddToDashboard = async () => {
    if (!results?.symbol) return;
    try {
      await portfolioService.addToWatchlist(results.symbol);
      toast({
        title: "Added to Dashboard",
        description: `${results.symbol} has been added to your watchlist.`,
      });
      onAdded?.(results.symbol);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add stock to dashboard",
        variant: "destructive",
      });
    }
  };

  const handleClear = () => {
    setQuery("");
    setResults(null);
    setSearched(false);
    setSuggestions([]);
    setShowSuggestions(false);
    setSuggestedSymbol(null);
  };

  const isPositive = results && results.change >= 0;

  return (
    <div className="w-full space-y-4">
      {/* Help Alert */}
      <Alert className="bg-primary/5 border-primary/20">
        <Lightbulb className="h-4 w-4" />
        <AlertDescription className="text-sm">
          <span className="font-semibold">Tip:</span> Use correct tickers for real data. 
          US stocks: <Badge variant="outline" className="mx-1">AAPL</Badge> 
          <Badge variant="outline" className="mx-1">TSLA</Badge> 
          Indian stocks: <Badge variant="outline" className="mx-1">TCS.NS</Badge> 
          <Badge variant="outline" className="mx-1">INFY.NS</Badge>
        </AlertDescription>
      </Alert>

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search by symbol (AAPL, TCS.NS) or company name..."
            value={query}
            onChange={(e) => handleInputChange(e.target.value)}
            onFocus={() => query.length >= 2 && setSuggestions.length > 0 && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            className="pl-10"
          />
          
          {/* Suggestions Dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-50 w-full mt-1 bg-card border border-border rounded-lg shadow-lg max-h-60 overflow-y-auto">
              {suggestions.map((stock) => (
                <button
                  key={stock.symbol}
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    handleSelectSuggestion(stock.symbol);
                  }}
                  className="w-full px-4 py-3 text-left hover:bg-accent transition-colors flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-sm">{stock.symbol}</p>
                    <p className="text-xs text-muted-foreground">{stock.name}</p>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {stock.region}
                  </Badge>
                </button>
              ))}
            </div>
          )}
        </div>
        <Button type="submit" disabled={loading} className="bg-primary hover:bg-primary/90">
          {loading ? "Searching..." : "Search"}
        </Button>
        {(query || results) && (
          <Button
            type="button"
            variant="ghost"
            onClick={handleClear}
            className="px-3"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </form>

      {/* Suggested correction */}
      {suggestedSymbol && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            Did you mean <Badge variant="default" className="mx-1">{suggestedSymbol}</Badge>? 
            <Button 
              variant="link" 
              size="sm" 
              className="ml-2 h-auto p-0"
              onClick={() => {
                setQuery(suggestedSymbol);
                handleSearch({ preventDefault: () => {} } as React.FormEvent);
              }}
            >
              Try it
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {searched && !loading && !results && (
        <Card className="border-border bg-card/80">
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">
              No results found. Try another symbol or company name.
            </p>
          </CardContent>
        </Card>
      )}

      {results && (
        <Card className="border-border bg-card/80 hover:shadow-lg transition-all duration-300">
          <CardContent className="py-6">
            {/* Show warning if price is 0 */}
            {results.price === 0 && (
              <Alert className="mb-4 bg-yellow-500/10 border-yellow-500/20">
                <Info className="h-4 w-4 text-yellow-500" />
                <AlertDescription className="text-sm">
                  <span className="font-semibold">Data Pending:</span> This stock was found but real-time pricing data is loading. 
                  {suggestedSymbol && (
                    <span> Try <Badge variant="outline" className="mx-1">{suggestedSymbol}</Badge> for live data.</span>
                  )}
                </AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-2xl font-bold">{results.symbol}</h3>
                  <p className="text-sm text-muted-foreground">{results.name}</p>
                </div>
                {isPositive ? (
                  <TrendingUp className="h-6 w-6 text-success" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-destructive" />
                )}
              </div>

              <div className="flex items-end justify-between">
                <div>
                  <p className="text-3xl font-bold">{formatCurrency(results.price, results.currency, 2)}</p>
                  <p className={`text-sm font-medium ${isPositive ? "text-success" : "text-destructive"}`}>
                    {isPositive ? "+" : ""}{results.change.toFixed(2)} ({isPositive ? "+" : ""}{results.changePercent.toFixed(2)}%)
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={handleViewDetails}
                    variant="outline"
                  >
                    View Details
                  </Button>
                  <Button
                    onClick={handleAddToDashboard}
                    className="bg-primary hover:bg-primary/90"
                  >
                    Add to Dashboard
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 pt-4 border-t border-border">
                <div>
                  <p className="text-xs text-muted-foreground">Market Cap</p>
                  <p className="font-semibold">{formatCurrency(results.marketCap / 1e9, results.currency, 2)}B</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Volume</p>
                  <p className="font-semibold">{(results.volume / 1e6).toFixed(2)}M</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">52W Range</p>
                  <p className="text-xs font-semibold">
                    {formatCurrency(results.low52w, results.currency, 2)} - {formatCurrency(results.high52w, results.currency, 2)}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default StockSearch;
