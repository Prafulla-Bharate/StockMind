import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/auth.context";
import { marketService } from "@/services/api/market.service";
import { portfolioService } from "@/services/api/portfolio.service";
import Navbar from "@/components/Navbar";
import StockChart from "@/components/StockChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ArrowLeft, TrendingUp, TrendingDown, Brain, Plus, Newspaper, Info } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { NewsCard } from "@/components/NewsCard";
import { formatCurrency } from "@/lib/utils";
import type { 
  StockData,
  NewsFeedResponse,
  AIPredictionResponse,
  StatisticalPrediction
} from "@/services/api/types";

const StockDetail = () => {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { user } = useAuth();
  const [stockData, setStockData] = useState<StockData | null>(null);
  const [sentiment, setSentiment] = useState<{
    sentiment: string;
    sentimentScore: number;
    analysis: string;
    timestamp: string;
  } | null>(null);
  const [aiPrediction, setAiPrediction] = useState<AIPredictionResponse | null>(null);
  const [mlPrediction, setMlPrediction] = useState<{ prediction: StatisticalPrediction } | null>(null);
  const [mlAttempted, setMlAttempted] = useState(false);
  const [mlError, setMlError] = useState<string | null>(null);
  const [news, setNews] = useState<NewsFeedResponse['news']>([]);
  const [newsSentiment, setNewsSentiment] = useState<NewsFeedResponse['overallSentiment'] | null>(null);
  const [loading, setLoading] = useState(true);
  const [sentimentLoading, setSentimentLoading] = useState(false);
  const [aiPredictionLoading, setAiPredictionLoading] = useState(false);
  const [mlPredictionLoading, setMlPredictionLoading] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);

  // Safe number formatter to avoid calling .toFixed on undefined
  const formatNumber = (v: number | undefined | null, decimals = 2) => {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
    return Number(v).toFixed(decimals);
  };

  useEffect(() => {
    if (symbol) {
      loadStockData();
    }
  }, [symbol]);

  const loadStockData = async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const data = await marketService.getStockData(symbol);
      setStockData(data);
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

  const loadSentiment = async () => {
    if (!symbol) return;
    
    setSentimentLoading(true);
    try {
      const sentiment = await marketService.getAISentiment(symbol);
      setSentiment(sentiment);
      toast({
        title: "AI Analysis Complete",
        description: "Sentiment analysis has been updated.",
      });
    } catch (error: any) {
      console.error("Error loading sentiment:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to load AI sentiment",
        variant: "destructive",
      });
    } finally {
      setSentimentLoading(false);
    }
  };

  const loadAiPrediction = async () => {
    if (!symbol || !stockData) return;
    
    setAiPredictionLoading(true);
    try {
      const prediction = await marketService.getAIPrediction(symbol, stockData.historicalData);
      setAiPrediction(prediction);
      toast({
        title: "AI Prediction Complete",
        description: "AI-powered price prediction has been generated.",
      });
    } catch (error: any) {
      console.error("Error loading AI prediction:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to generate AI prediction",
        variant: "destructive",
      });
    } finally {
      setAiPredictionLoading(false);
    }
  };

  const loadMlPrediction = async () => {
    if (!symbol || !stockData) return;
    
    setMlPredictionLoading(true);
    try {
      setMlAttempted(true);
      const prediction = await marketService.getStatisticalPrediction(symbol, stockData.historicalData);
      console.log('[StockDetail] ML Prediction response:', prediction);
      
      if (!prediction || prediction === null) {
        setMlError('Backend returned empty prediction. Check if historical data is sufficient.');
        toast({
          title: "No Prediction Data",
          description: "Backend returned empty prediction. Check if historical data is sufficient.",
          variant: "destructive",
        });
        setMlPrediction(null);
        return;
      }

      setMlPrediction({ prediction });
      setMlError(null);
      toast({
        title: "ML Prediction Complete",
        description: "Statistical prediction has been generated.",
      });
    } catch (error: any) {
      console.error("Error loading ML prediction:", error);
      setMlError(error.response?.data?.message || error.message || 'Failed to generate ML prediction. Backend may need more data.');
      toast({
        title: "Error",
        description: error.response?.data?.message || error.message || "Failed to generate ML prediction. Backend may need more data.",
        variant: "destructive",
      });
    } finally {
      setMlPredictionLoading(false);
    }
  };

  const loadNews = async () => {
    if (!symbol) return;
    
    setNewsLoading(true);
    try {
      const newsData = await marketService.getNewsFeed(symbol, stockData?.name);
      setNews(newsData.news);
      setNewsSentiment(newsData.overallSentiment);
      toast({
        title: "News Loaded",
        description: `Found ${newsData.news.length} recent articles.`,
      });
    } catch (error: any) {
      console.error("Error loading news:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to load news feed",
        variant: "destructive",
      });
    } finally {
      setNewsLoading(false);
    }
  };

  const addToWatchlist = async () => {
    if (!user || !symbol) return;

    try {
      await portfolioService.addToWatchlist(symbol);
      toast({
        title: "Added to watchlist",
        description: `${symbol} has been added to your watchlist.`,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to add to watchlist",
        variant: "destructive",
      });
    }
  };

  if (loading || !stockData) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-8 text-center">
          <p className="text-muted-foreground">Loading stock data...</p>
        </div>
      </div>
    );
  }

  const isPositive = stockData.change >= 0;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="container mx-auto px-4 py-8">
        <Button variant="ghost" onClick={() => navigate(-1)} className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>

        <div className="mb-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-5xl font-bold mb-2">{stockData.symbol}</h1>
              <p className="text-xl text-muted-foreground">{stockData.name}</p>
            </div>
            {user && (
              <Button onClick={addToWatchlist} variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Add to Watchlist
              </Button>
            )}
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-5xl font-bold">{formatCurrency(stockData.price, stockData.currency, 2)}</span>
            <div className={`flex items-center gap-2 ${isPositive ? "text-success" : "text-destructive"}`}>
              {isPositive ? <TrendingUp className="h-6 w-6" /> : <TrendingDown className="h-6 w-6" />}
              <span className="text-2xl font-bold">
                {isPositive ? "+" : ""}{formatNumber(stockData.change, 2)} ({isPositive ? "+" : ""}{formatNumber(stockData.changePercent, 2)}%)
              </span>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6 mb-6">
          <Card className="lg:col-span-2 border-border bg-card/80">
            <CardHeader>
              <CardTitle>Price Chart (90 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              <StockChart data={stockData.historicalData} isPositive={isPositive} />
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card className="border-border bg-card/80">
              <CardHeader>
                <CardTitle>Key Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Market Cap</span>
                  <span className="font-bold">{formatCurrency(stockData.marketCap ? stockData.marketCap / 1e9 : undefined, stockData.currency, 2)}B</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Volume</span>
                  <span className="font-bold">{formatNumber(stockData.volume ? stockData.volume / 1e6 : undefined, 2)}M</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">52W High</span>
                  <span className="font-bold">{formatCurrency(stockData.high52w, stockData.currency, 2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">52W Low</span>
                  <span className="font-bold">{formatCurrency(stockData.low52w, stockData.currency, 2)}</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border bg-card/80">
              <CardHeader>
                <CardTitle>Technical Indicators</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">RSI (14)</span>
                  <span className="font-bold">{formatNumber(stockData.indicators?.rsi, 2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">SMA (20)</span>
                  <span className="font-bold">{formatCurrency(stockData.indicators?.sma20, stockData.currency, 2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">SMA (50)</span>
                  <span className="font-bold">{formatCurrency(stockData.indicators?.sma50, stockData.currency, 2)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <Card className="border-border bg-card/80 mb-6">
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-6 w-6 text-primary" />
              <CardTitle>Price Predictions</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="ai" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-4">
                <TabsTrigger value="ai">AI Prediction</TabsTrigger>
                <TabsTrigger value="ml">Statistical ML</TabsTrigger>
              </TabsList>
              
              <TabsContent value="ai">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm text-muted-foreground">AI-powered prediction using Gemini with technical indicators</p>
                  <Button 
                    onClick={loadAiPrediction} 
                    disabled={aiPredictionLoading}
                    className="bg-primary hover:bg-primary/90"
                  >
                    {aiPredictionLoading ? "Predicting..." : "Generate"}
                  </Button>
                </div>
                {aiPrediction ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <div className="whitespace-pre-wrap text-foreground leading-relaxed">
                      {aiPrediction.prediction}
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    Click "Generate" to get AI-powered price predictions with technical analysis.
                  </p>
                )}
              </TabsContent>
              
              <TabsContent value="ml">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm text-muted-foreground">Statistical prediction using linear regression & technical indicators</p>
                  <Button 
                    onClick={loadMlPrediction} 
                    disabled={mlPredictionLoading || (stockData?.historicalData?.length ?? 0) < 30}
                    className="bg-primary hover:bg-primary/90"
                  >
                    {mlPredictionLoading ? "Calculating..." : "Generate"}
                  </Button>
                </div>
                {(mlAttempted && !mlPrediction) && (
                  <Alert className="mb-4">
                    <Info className="h-4 w-4" />
                    <AlertTitle>No prediction available</AlertTitle>
                    <AlertDescription>
                      {mlError || 'The backend did not return prediction data. Try a different symbol or ensure sufficient historical data (e.g., 30+ data points).'}
                    </AlertDescription>
                  </Alert>
                )}
                {mlPrediction ? (
                  <div className="space-y-6">
                    <div className="grid md:grid-cols-3 gap-4">
                      <Card className="border-border">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium">Short-term (1 Week)</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{formatCurrency(mlPrediction?.prediction?.predictions?.shortTerm?.targetPrice, mlPrediction?.prediction?.currency || stockData?.currency, 2)}</div>
                          <div className={`text-sm ${parseFloat(mlPrediction?.prediction?.predictions?.shortTerm?.change ?? "0") > 0 ? 'text-success' : 'text-destructive'}`}>
                            {mlPrediction?.prediction?.predictions?.shortTerm?.change ?? "—"}
                          </div>
                          <div className="text-xs text-muted-foreground mt-2">
                            Confidence: {mlPrediction?.prediction?.predictions?.shortTerm?.confidence ?? "—"}
                          </div>
                          <Badge variant="outline" className="mt-2">{mlPrediction?.prediction?.predictions?.shortTerm?.trend ?? "—"}</Badge>
                        </CardContent>
                      </Card>
                      
                      <Card className="border-border">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium">Medium-term (1 Month)</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{formatCurrency(mlPrediction?.prediction?.predictions?.mediumTerm?.targetPrice, mlPrediction?.prediction?.currency || stockData?.currency, 2)}</div>
                          <div className={`text-sm ${parseFloat(mlPrediction?.prediction?.predictions?.mediumTerm?.change ?? "0") > 0 ? 'text-success' : 'text-destructive'}`}>
                            {mlPrediction?.prediction?.predictions?.mediumTerm?.change ?? "—"}
                          </div>
                          <div className="text-xs text-muted-foreground mt-2">
                            Confidence: {mlPrediction?.prediction?.predictions?.mediumTerm?.confidence ?? "—"}
                          </div>
                          <Badge variant="outline" className="mt-2">{mlPrediction?.prediction?.predictions?.mediumTerm?.trend ?? "—"}</Badge>
                        </CardContent>
                      </Card>
                      
                      <Card className="border-border">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium">Long-term (3 Months)</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">{formatCurrency(mlPrediction?.prediction?.predictions?.longTerm?.targetPrice, mlPrediction?.prediction?.currency || stockData?.currency, 2)}</div>
                          <div className={`text-sm ${parseFloat(mlPrediction?.prediction?.predictions?.longTerm?.change ?? "0") > 0 ? 'text-success' : 'text-destructive'}`}>
                            {mlPrediction?.prediction?.predictions?.longTerm?.change ?? "—"}
                          </div>
                          <div className="text-xs text-muted-foreground mt-2">
                            Confidence: {mlPrediction?.prediction?.predictions?.longTerm?.confidence ?? "—"}
                          </div>
                          <Badge variant="outline" className="mt-2">{mlPrediction?.prediction?.predictions?.longTerm?.trend ?? "—"}</Badge>
                        </CardContent>
                      </Card>
                    </div>
                    
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold mb-3">Technical Indicators</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">RSI:</span>
                            <span>{mlPrediction?.prediction?.technicalIndicators?.rsi ?? "—"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">MACD:</span>
                            <span>{mlPrediction?.prediction?.technicalIndicators?.macd ?? "—"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">SMA20:</span>
                            <span>{formatCurrency(mlPrediction?.prediction?.technicalIndicators?.sma20, mlPrediction?.prediction?.currency || stockData?.currency, 2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">SMA50:</span>
                            <span>{formatCurrency(mlPrediction?.prediction?.technicalIndicators?.sma50, mlPrediction?.prediction?.currency || stockData?.currency, 2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Volatility:</span>
                            <span>{mlPrediction?.prediction?.technicalIndicators?.volatility ?? "—"}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-semibold mb-3">Market Signals</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">MACD Signal:</span>
                            <Badge variant={mlPrediction?.prediction?.signals?.macd === 'Bullish' ? 'default' : 'destructive'}>
                              {mlPrediction?.prediction?.signals?.macd ?? "—"}
                            </Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">RSI Signal:</span>
                            <Badge variant="secondary">{mlPrediction?.prediction?.signals?.rsi ?? "—"}</Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">MA Crossover:</span>
                            <Badge variant={mlPrediction?.prediction?.signals?.ma_cross === 'Bullish' ? 'default' : 'destructive'}>
                              {mlPrediction?.prediction?.signals?.ma_cross ?? "—"}
                            </Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Bollinger:</span>
                            <Badge variant="outline">{mlPrediction?.prediction?.signals?.bollinger ?? "—"}</Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Overall Sentiment:</span>
                            <Badge variant={mlPrediction?.prediction?.overallOutlook?.sentiment === 'Bullish' ? 'default' : mlPrediction?.prediction?.overallOutlook?.sentiment === 'Bearish' ? 'destructive' : 'secondary'}>
                              {mlPrediction?.prediction?.overallOutlook?.sentiment ?? "—"}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="border-t pt-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-sm text-muted-foreground">Bullish Score: </span>
                          <span className="font-bold text-lg">{mlPrediction?.prediction?.overallOutlook?.bullishScore ?? "—"}</span>
                        </div>
                        <div>
                          <span className="text-sm text-muted-foreground">Risk Level: </span>
                          <Badge variant={mlPrediction?.prediction?.overallOutlook?.riskLevel === 'High' ? 'destructive' : mlPrediction?.prediction?.overallOutlook?.riskLevel === 'Medium' ? 'secondary' : 'default'}>
                            {mlPrediction?.prediction?.overallOutlook?.riskLevel ?? "—"}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    Click "Generate" to get statistical ML predictions based on technical analysis.
                  </p>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <Card className="border-border bg-card/80 mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Newspaper className="h-6 w-6 text-primary" />
                <CardTitle>News & Events</CardTitle>
              </div>
              <Button 
                onClick={loadNews} 
                disabled={newsLoading}
                className="bg-primary hover:bg-primary/90"
              >
                {newsLoading ? "Loading..." : "Load News"}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {news.length > 0 ? (
              <div className="space-y-6">
                {newsSentiment && (
                  <Card className="border-border bg-accent/20">
                    <CardHeader>
                      <CardTitle className="text-base">Overall News Sentiment</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <Badge 
                            variant={newsSentiment.label.includes('Bullish') ? 'default' : newsSentiment.label.includes('Bearish') ? 'destructive' : 'secondary'}
                            className="text-lg px-4 py-2"
                          >
                            {newsSentiment.label}
                          </Badge>
                          <span className="text-xl font-bold">Score: {newsSentiment.score}/100</span>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          <div>Bullish: {newsSentiment.bullish} | Neutral: {newsSentiment.neutral} | Bearish: {newsSentiment.bearish}</div>
                          <div>Total Articles: {newsSentiment.totalArticles}</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
                <div className="space-y-4">
                  {news.map((article, index) => (
                    <NewsCard key={index} article={article} />
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground text-center py-8">
                Click "Load News" to see the latest news articles and sentiment analysis for this stock.
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="border-border bg-card/80">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-6 w-6 text-primary" />
                <CardTitle>AI Sentiment Analysis</CardTitle>
              </div>
              <Button 
                onClick={loadSentiment} 
                disabled={sentimentLoading}
                className="bg-primary hover:bg-primary/90"
              >
                {sentimentLoading ? "Analyzing..." : "Analyze with AI"}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {sentiment ? (
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <Badge 
                    variant={sentiment.sentiment === "positive" ? "default" : sentiment.sentiment === "neutral" ? "secondary" : "destructive"}
                    className="text-lg px-4 py-2"
                  >
                    {sentiment.sentiment.toUpperCase()}
                  </Badge>
                  <span className="text-2xl font-bold">
                    Score: {sentiment.sentimentScore}/100
                  </span>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  {sentiment.analysis}
                </p>
                <p className="text-xs text-muted-foreground">
                  Analysis generated: {new Date(sentiment.timestamp).toLocaleString()}
                </p>
              </div>
            ) : (
              <p className="text-muted-foreground text-center py-8">
                Click "Analyze with AI" to get AI-powered sentiment analysis for this stock.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StockDetail;