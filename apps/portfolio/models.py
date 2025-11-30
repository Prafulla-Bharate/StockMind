import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.market.models import Stock

User = get_user_model()

class PortfolioHolding(models.Model):
    """User's stock holdings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    shares = models.DecimalField(max_digits=12, decimal_places=4)
    average_price = models.DecimalField(max_digits=12, decimal_places=4)
    purchase_date = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'portfolio_holdings'
        unique_together = ['user', 'stock']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'stock']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Portfolio Holding'
        verbose_name_plural = 'Portfolio Holdings'
    
    def __str__(self):
        return f"{self.user.email} - {self.stock.symbol} ({self.shares} shares)"
    
    @property
    def total_cost(self):
        """Calculate total investment cost"""
        return self.shares * self.average_price
    
    @property
    def current_value(self):
        """Calculate current value (requires latest stock price)"""
        latest_price = self.stock.prices.first()
        if latest_price:
            return self.shares * latest_price.close
        return self.total_cost
    
    @property
    def profit_loss(self):
        """Calculate profit/loss"""
        return self.current_value - self.total_cost
    
    @property
    def profit_loss_percent(self):
        """Calculate profit/loss percentage"""
        if self.total_cost > 0:
            return ((self.current_value - self.total_cost) / self.total_cost) * 100
        return 0

class Watchlist(models.Model):
    """User's stock watchlist"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    alert_price_above = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    alert_price_below = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    
    class Meta:
        db_table = 'watchlists'
        unique_together = ['user', 'stock']
        indexes = [
            models.Index(fields=['user', 'added_at']),
        ]
        ordering = ['-added_at']
        verbose_name = 'Watchlist Item'
        verbose_name_plural = 'Watchlist Items'
    
    def __str__(self):
        return f"{self.user.email} - {self.stock.symbol}"