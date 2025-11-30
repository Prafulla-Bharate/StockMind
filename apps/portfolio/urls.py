from django.urls import path
from .views import (
    PortfolioHoldingsView,
    PortfolioHoldingDetailView,
    WatchlistView,
    WatchlistDetailView
)

app_name = 'portfolio'

urlpatterns = [
    # Holdings
    path('holdings/', PortfolioHoldingsView.as_view(), name='holdings-list'),
    path('holdings/<uuid:holding_id>/', PortfolioHoldingDetailView.as_view(), name='holding-detail'),
    
    # Watchlist
    path('watchlist/', WatchlistView.as_view(), name='watchlist-list'),
    path('watchlist/<uuid:watchlist_id>/', WatchlistDetailView.as_view(), name='watchlist-detail'),
]