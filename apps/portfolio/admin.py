from django.contrib import admin
from .models import PortfolioHolding, Watchlist

@admin.register(PortfolioHolding)
class PortfolioHoldingAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'shares', 'average_price', 'total_cost', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'stock__symbol', 'stock__name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'total_cost', 'current_value', 'profit_loss']
    
    fieldsets = (
        ('User & Stock', {'fields': ('user', 'stock')}),
        ('Investment Details', {'fields': ('shares', 'average_price', 'purchase_date')}),
        ('Calculated Values', {'fields': ('total_cost', 'current_value', 'profit_loss')}),
        ('Notes', {'fields': ('notes',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'added_at', 'alert_price_above', 'alert_price_below']
    list_filter = ['added_at']
    search_fields = ['user__email', 'stock__symbol', 'stock__name']
    date_hierarchy = 'added_at'
    readonly_fields = ['added_at']
    
    fieldsets = (
        ('User & Stock', {'fields': ('user', 'stock')}),
        ('Alerts', {'fields': ('alert_price_above', 'alert_price_below')}),
        ('Notes', {'fields': ('notes',)}),
        ('Timestamp', {'fields': ('added_at',)}),
    )