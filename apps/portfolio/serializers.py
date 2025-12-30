from rest_framework import serializers
from .models import PortfolioHolding, Watchlist
from apps.market.serializers import StockSerializer

class PortfolioHoldingSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    currency = serializers.CharField(source='stock.currency', read_only=True)
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    current_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    profit_loss = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    profit_loss_percent = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    
    class Meta:
        model = PortfolioHolding
        fields = [
            'id', 'symbol', 'stock_name', 'currency', 'shares', 'average_price',
            'purchase_date', 'notes', 'total_cost', 'current_value',
            'profit_loss', 'profit_loss_percent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class PortfolioHoldingCreateSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(write_only=True)
    averagePrice = serializers.DecimalField(
        max_digits=12, decimal_places=4, write_only=True, required=False, source='average_price'
    )
    purchaseDate = serializers.DateTimeField(write_only=True, required=False, source='purchase_date')
    
    class Meta:
        model = PortfolioHolding
        fields = ['symbol', 'shares', 'average_price', 'purchase_date', 'notes', 'averagePrice', 'purchaseDate']
        extra_kwargs = {
            'average_price': {'required': False},
            'purchase_date': {'required': False},
            'notes': {'required': False, 'allow_blank': True, 'allow_null': True},
        }
    
    def validate(self, data):
        """Ensure at least one format is provided for price and date"""
        # Check if we have either snake_case or camelCase for average_price
        if 'average_price' not in data:
            raise serializers.ValidationError({
                'average_price': 'This field is required (use average_price or averagePrice)'
            })
        
        # Check if we have either snake_case or camelCase for purchase_date
        if 'purchase_date' not in data:
            raise serializers.ValidationError({
                'purchase_date': 'This field is required (use purchase_date or purchaseDate)'
            })
        
        return data
    
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
        
        # Convert None to empty string for notes
        if validated_data.get('notes') is None:
            validated_data['notes'] = ''
        
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
    currency = serializers.CharField(source='stock.currency', read_only=True)
    current_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Watchlist
        fields = [
            'id', 'symbol', 'stock_name', 'currency', 'added_at', 'notes',
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