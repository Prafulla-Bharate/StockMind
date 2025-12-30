import logging
from typing import List, Dict, Optional
from django.core.cache import cache
from django.db.models import Q
from apps.market.models import Stock
import requests

logger = logging.getLogger(__name__)


def _cache_key(query: str, limit: int) -> str:
    return f"symbol_resolve:{query.strip().lower()}:{limit}"


def _validate_symbol_has_data(symbol: str, skip_validation: bool = False) -> bool:
    """
    Quick validation: check if a symbol has fetchable real market data.
    If skip_validation=True, accept symbols from trusted sources (e.g., Yahoo search) even if yfinance fails.
    """
    if skip_validation:
        # Trust that if Yahoo returned it, it's valid
        return True
        
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Check if we have currentPrice or can get fast_info
        if info and info.get('currentPrice'):
            return True
        
        # Try fast_info as fallback
        fast_info = ticker.fast_info
        if fast_info and fast_info.get('last_price'):
            return True
            
        return False
    except Exception as e:
        logger.debug(f"Validation failed for '{symbol}': {e}")
        return False


def resolve_symbol_or_name(query: str, limit: int = 10) -> Dict[str, object]:
    query = (query or "").strip()
    if not query:
        return {"canonical": None, "candidates": []}

    ck = _cache_key(query, limit)
    cached = cache.get(ck)
    if cached:
        return cached

    candidates: List[Dict[str, object]] = []
    seen = set()

    q_upper = query.upper()
    q_lower = query.lower()
    
    # Determine if query is ambiguous (no exchange suffix like .NS, .BO, etc.)
    is_ambiguous = '.' not in q_upper and not any(q_upper.endswith(x) for x in ['^', '='])

    # For ambiguous queries (raw symbols or names), prioritize Yahoo search
    # to get exchange-qualified results first
    if is_ambiguous:
        try:
            resp = requests.get(
                "https://query2.finance.yahoo.com/v1/finance/search",
                params={"q": query, "quotesCount": limit * 2, "newsCount": 0},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            quotes = data.get("quotes", [])
            
            # Prioritize equity/ETF results with proper exchanges
            for i, q in enumerate(quotes):
                sym = q.get("symbol")
                if not sym or sym in seen:
                    continue
                
                display_name = q.get("longname") or q.get("shortname") or sym
                exchange = q.get("exchDisp") or q.get("exchange")
                qt = (q.get("quoteType") or "").upper()
                
                # Filter: prefer equity/ETF with exchange info
                if qt not in ("EQUITY", "ETF", "INDEX"):
                    continue
                
                # For Yahoo search results, trust the source; skip expensive validation
                # Validation failures are often due to yfinance timeouts, not bad symbols
                # Accept the symbol; yfinance will retry if needed
                    
                # Boost score for exchange-qualified symbols
                base_score = float(q.get("score") or 0.5)
                if '.' in sym or exchange:
                    score = min(1.0, base_score + 0.3)
                else:
                    score = base_score * 0.7
                
                candidates.append({
                    "symbol": sym,
                    "displayName": display_name,
                    "exchange": exchange,
                    "quoteType": qt,
                    "score": score,
                })
                seen.add(sym)
                
                if len(candidates) >= limit:
                    break
        except Exception as e:
            logger.warning(f"Yahoo search failed for '{query}': {e}")
            # Don't return; fall through to DB search
            quotes = []

    # Local DB exact symbol match (only if query has exchange suffix or Yahoo failed)
    if not candidates or not is_ambiguous:
        try:
            s = Stock.objects.filter(symbol=q_upper).first()
            if s and s.symbol not in seen:
                candidates.append({
                    "symbol": s.symbol,
                    "displayName": s.name or s.symbol,
                    "exchange": None,
                    "quoteType": "EQUITY",
                    "score": 1.0 if '.' in s.symbol else 0.8,
                })
                seen.add(s.symbol)
        except Exception:
            pass

    # Local DB name/symbol contains (supplemental results)
    if len(candidates) < limit:
        try:
            qs = Stock.objects.filter(
                Q(name__icontains=query) | Q(symbol__icontains=query)
            ).exclude(symbol__in=seen)[:limit]
            
            for s in qs:
                # For DB records, still validate to prefer fresh data
                # But don't skip if validation times out; DB entries are trusted
                try:
                    if not _validate_symbol_has_data(s.symbol, skip_validation=False):
                        logger.debug(f"DB record '{s.symbol}' - validation inconclusive, including anyway")
                except Exception as e:
                    logger.debug(f"DB record '{s.symbol}' - validation error, including anyway: {e}")
                
                # Skip symbols without exchange suffix if we already have better candidates
                if candidates and '.' not in s.symbol:
                    continue
                    
                candidates.append({
                    "symbol": s.symbol,
                    "displayName": s.name or s.symbol,
                    "exchange": None,
                    "quoteType": "EQUITY",
                    "score": 0.6 if '.' in s.symbol else 0.3,
                })
                seen.add(s.symbol)
                
                if len(candidates) >= limit:
                    break
        except Exception:
            pass

    # Last resort: if no candidates and query is bare symbol (AAPL, MSFT, TESLA), try it as-is
    if not candidates and is_ambiguous:
        logger.info(f"No candidates found for '{query}'; attempting bare symbol lookup")
        candidates.append({
            "symbol": q_upper,
            "displayName": q_upper,
            "exchange": None,
            "quoteType": "EQUITY",
            "score": 0.5,
        })
    
    # Rank candidates by score descending
    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Choose canonical: prefer exchange-qualified symbols
    canonical = None
    if candidates:
        # Find first candidate with exchange suffix
        for c in candidates:
            if '.' in c["symbol"]:
                canonical = c["symbol"]
                break
        # Fallback to highest scored
        if not canonical:
            canonical = candidates[0]["symbol"]

    result = {"canonical": canonical, "candidates": candidates}
    cache.set(ck, result, 24 * 3600)
    
    if canonical:
        logger.info(f"Resolved '{query}' -> '{canonical}' with {len(candidates)} candidate(s)")
    else:
        logger.warning(f"Failed to resolve '{query}'; searched Yahoo and local DB with {len(candidates)} candidates")
    
    return result
