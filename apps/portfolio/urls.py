from django.urls import path, re_path
from .views import (
    PortfolioSummaryView,
    PortfolioHoldingsView,
    PortfolioHoldingDetailView,
    WatchlistView,
    WatchlistDetailView
)

app_name = 'portfolio'

urlpatterns = [
        # Simple index for portfolio API root
        path('', lambda request: __import__('django.http').http.HttpResponse(
                """
                <html>
                    <head><title>Portfolio API</title></head>
                    <body>
                        <h1>Portfolio API</h1>
                        <ul>
                            <li><a href='summary/'>Summary (Currency Breakdown)</a></li>
                            <li><a href='holdings/'>Holdings</a></li>
                            <li><a href='watchlist/'>Watchlist</a></li>
                        </ul>
                    </body>
                </html>
                """
        )),
    # Portfolio summary
    path('summary/', PortfolioSummaryView.as_view(), name='summary'),
    re_path(r'^summary/?$', PortfolioSummaryView.as_view(), name='summary-noslash'),
    
    # Holdings
    path('holdings/', PortfolioHoldingsView.as_view(), name='holdings-list'),
    re_path(r'^holdings/?$', PortfolioHoldingsView.as_view(), name='holdings-list-noslash'),
    path('holdings/<uuid:holding_id>/', PortfolioHoldingDetailView.as_view(), name='holding-detail'),
    re_path(r'^holdings/(?P<holding_id>[0-9a-fA-F\-]{36})/?$', PortfolioHoldingDetailView.as_view(), name='holding-detail-noslash'),
    
    # Watchlist
    path('watchlist/', WatchlistView.as_view(), name='watchlist-list'),
    re_path(r'^watchlist/?$', WatchlistView.as_view(), name='watchlist-list-noslash'),
    path('watchlist/<uuid:watchlist_id>/', WatchlistDetailView.as_view(), name='watchlist-detail'),
    re_path(r'^watchlist/(?P<watchlist_id>[0-9a-fA-F\-]{36})/?$', WatchlistDetailView.as_view(), name='watchlist-detail-noslash'),
]