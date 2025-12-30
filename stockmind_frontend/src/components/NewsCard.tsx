import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink } from "lucide-react";

interface NewsArticle {
  title: string;
  description: string;
  url: string;
  source: string;
  publishedAt: string;
  urlToImage?: string;
  sentiment: {
    score: number;
    label: string;
    explanation: string;
  };
}

interface NewsCardProps {
  article: NewsArticle;
}

export const NewsCard = ({ article }: NewsCardProps) => {
  const getSentimentColor = (label: string) => {
    if (label.includes('Bullish')) return 'text-success';
    if (label.includes('Bearish')) return 'text-destructive';
    return 'text-muted-foreground';
  };

  const getSentimentBadgeVariant = (label: string): "default" | "secondary" | "destructive" | "outline" => {
    if (label.includes('Bullish')) return 'default';
    if (label.includes('Bearish')) return 'destructive';
    return 'secondary';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <Card className="p-4 hover:bg-accent/50 transition-colors">
      <div className="flex gap-4">
        {article.urlToImage && (
          <img 
            src={article.urlToImage} 
            alt={article.title}
            className="w-24 h-24 object-cover rounded-lg"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        )}
        <div className="flex-1 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <a 
              href={article.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="font-semibold text-sm hover:underline line-clamp-2 flex-1"
            >
              {article.title}
            </a>
            <ExternalLink className="w-4 h-4 flex-shrink-0 text-muted-foreground" />
          </div>
          
          {article.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {article.description}
            </p>
          )}
          
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>{article.source}</span>
              <span>•</span>
              <span>{formatDate(article.publishedAt)}</span>
            </div>
            
            <Badge variant={getSentimentBadgeVariant(article.sentiment.label)} className="text-xs">
              {article.sentiment.label}
            </Badge>
          </div>
          
          {article.sentiment.explanation && (
            <p className="text-xs text-muted-foreground italic">
              {article.sentiment.explanation}
            </p>
          )}
        </div>
      </div>
    </Card>
  );
};
