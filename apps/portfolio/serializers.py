from rest_framework import serializers
from .models import PortfolioHolding, Watchlist
from apps.market.serializers import StockSerializer

class PortfolioHoldingSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    current_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    profit_loss = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    profit_loss_percent = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    
    class Meta:
        model = PortfolioHolding
        fields = [
            'id', 'symbol', 'stock_name', 'shares', 'average_price',
            'purchase_date', 'notes', 'total_cost', 'current_value',
            'profit_loss', 'profit_loss_percent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PortfolioHoldingCreateSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(write_only=True)
    
    class Meta:
        model = PortfolioHolding
        fields = ['symbol', 'shares', 'average_price', 'purchase_date', 'notes']
    
    def validate_symbol(self, value):
        """Validate stock symbol exists"""
        from apps.market.models import Stock
        if not Stock.objects.filter(symbol=value.upper()).exists():
            raise serializers.ValidationError(f"Stock with symbol '{value}' not found")
        return value.upper()
    
    def create(self, validated_data):
        from apps.market.models import Stock
        symbol = validated_data.pop('symbol')
        stock = Stock.objects.get(symbol=symbol)
        user = self.context['request'].user
        
        # Update or create holding
        holding, created = PortfolioHolding.objects.update_or_create(
            user=user,
            stock=stock,
            defaults=validated_data
        )
        return holding

class WatchlistSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    current_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Watchlist
        fields = [
            'id', 'symbol', 'stock_name', 'added_at', 'notes',
            'alert_price_above', 'alert_price_below', 'current_price'
        ]
        read_only_fields = ['id', 'added_at']
    
    def get_current_price(self, obj):
        """Get latest stock price"""
        latest_price = obj.stock.prices.first()
        if latest_price:
            return float(latest_price.close)
        return None

class WatchlistCreateSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(write_only=True)
    
    class Meta:
        model = Watchlist
        fields = ['symbol', 'notes', 'alert_price_above', 'alert_price_below']
    
    def validate_symbol(self, value):
        """Validate stock symbol exists"""
        from apps.market.models import Stock
        if not Stock.objects.filter(symbol=value.upper()).exists():
            raise serializers.ValidationError(f"Stock with symbol '{value}' not found")
        return value.upper()
    
    def create(self, validated_data):
        from apps.market.models import Stock
        symbol = validated_data.pop('symbol')
        stock = Stock.objects.get(symbol=symbol)
        user = self.context['request'].user
        
        watchlist_item, created = Watchlist.objects.get_or_create(
            user=user,
            stock=stock,
            defaults=validated_data
        )
        return watchlist_item