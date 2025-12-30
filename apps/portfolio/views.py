from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from .models import PortfolioHolding, Watchlist
from .serializers import (
    PortfolioHoldingSerializer,
    PortfolioHoldingCreateSerializer,
    WatchlistSerializer,
    WatchlistCreateSerializer
)
from utils.responses import success_response, error_response

class PortfolioSummaryView(APIView):
    """Portfolio summary with currency breakdown"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET /api/portfolio/summary - Returns portfolio value broken down by currency"""
        holdings = PortfolioHolding.objects.filter(user=request.user).select_related('stock')
        
        # Group holdings by currency
        currency_breakdown = {}
        total_holdings = 0
        
        for holding in holdings:
            currency = holding.stock.currency or 'USD'
            
            # Get latest price
            latest_price = holding.stock.prices.first()
            current_value = float(holding.shares * latest_price.close) if latest_price else float(holding.total_cost)
            total_cost = float(holding.total_cost)
            profit_loss = current_value - total_cost
            
            if currency not in currency_breakdown:
                currency_breakdown[currency] = {
                    'currency': currency,
                    'totalValue': 0,
                    'totalCost': 0,
                    'profitLoss': 0,
                    'profitLossPercent': 0,
                    'holdings': 0
                }
            
            currency_breakdown[currency]['totalValue'] += current_value
            currency_breakdown[currency]['totalCost'] += total_cost
            currency_breakdown[currency]['profitLoss'] += profit_loss
            currency_breakdown[currency]['holdings'] += 1
            total_holdings += 1
        
        # Calculate percentages for each currency
        for currency_data in currency_breakdown.values():
            if currency_data['totalCost'] > 0:
                currency_data['profitLossPercent'] = round(
                    (currency_data['profitLoss'] / currency_data['totalCost']) * 100, 2
                )
            # Round values
            currency_data['totalValue'] = round(currency_data['totalValue'], 2)
            currency_data['totalCost'] = round(currency_data['totalCost'], 2)
            currency_data['profitLoss'] = round(currency_data['profitLoss'], 2)
        
        return Response(success_response(data={
            'totalHoldings': total_holdings,
            'currencyBreakdown': list(currency_breakdown.values()),
            'note': 'Values are separated by currency. Convert to a common currency for total portfolio value.'
        }))

class PortfolioHoldingsView(APIView):
    """Portfolio holdings list and create"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET /api/portfolio/holdings"""
        holdings = PortfolioHolding.objects.filter(user=request.user).select_related('stock')
        serializer = PortfolioHoldingSerializer(holdings, many=True)
        return Response(success_response(data=serializer.data))
    
    def post(self, request):
        """POST /api/portfolio/holdings"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Portfolio POST data: {request.data}")
        logger.info(f"Content-Type: {request.content_type}")
        
        serializer = PortfolioHoldingCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            holding = serializer.save()
            response_serializer = PortfolioHoldingSerializer(holding)
            return Response(
                success_response(
                    data=response_serializer.data,
                    message='Holding added successfully'
                ),
                status=status.HTTP_201_CREATED
            )
        
        logger.error(f"Portfolio validation errors: {serializer.errors}")
        return Response(
            error_response(
                message='Failed to add holding',
                errors=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

class PortfolioHoldingDetailView(APIView):
    """Portfolio holding detail, update, delete"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, holding_id, user):
        """Get holding object"""
        return get_object_or_404(PortfolioHolding, id=holding_id, user=user)
    
    def get(self, request, holding_id):
        """GET /api/portfolio/holdings/{id}"""
        holding = self.get_object(holding_id, request.user)
        serializer = PortfolioHoldingSerializer(holding)
        return Response(success_response(data=serializer.data))
    
    def patch(self, request, holding_id):
        """PATCH /api/portfolio/holdings/{id}"""
        holding = self.get_object(holding_id, request.user)
        
        # Update allowed fields
        if 'shares' in request.data:
            holding.shares = request.data['shares']
        if 'average_price' in request.data or 'averagePrice' in request.data:
            holding.average_price = request.data.get('average_price') or request.data.get('averagePrice')
        if 'notes' in request.data:
            holding.notes = request.data['notes']
        
        holding.save()
        
        serializer = PortfolioHoldingSerializer(holding)
        return Response(
            success_response(
                data=serializer.data,
                message='Holding updated successfully'
            )
        )
    
    def delete(self, request, holding_id):
        """DELETE /api/portfolio/holdings/{id}"""
        holding = self.get_object(holding_id, request.user)
        holding.delete()
        
        return Response(
            success_response(message='Holding deleted successfully'),
            status=status.HTTP_200_OK
        )

class WatchlistView(APIView):
    """Watchlist list and create"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET /api/portfolio/watchlist"""
        watchlist = Watchlist.objects.filter(user=request.user).select_related('stock')
        serializer = WatchlistSerializer(watchlist, many=True)
        return Response(success_response(data=serializer.data))
    
    def post(self, request):
        """POST /api/portfolio/watchlist"""
        serializer = WatchlistCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            watchlist_item = serializer.save()
            response_serializer = WatchlistSerializer(watchlist_item)
            return Response(
                success_response(
                    data=response_serializer.data,
                    message='Stock added to watchlist'
                ),
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            error_response(
                message='Failed to add to watchlist',
                errors=serializer.errors
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

class WatchlistDetailView(APIView):
    """Watchlist detail, update, delete"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, watchlist_id, user):
        """Get watchlist object"""
        return get_object_or_404(Watchlist, id=watchlist_id, user=user)
    
    def get(self, request, watchlist_id):
        """GET /api/portfolio/watchlist/{id}"""
        watchlist_item = self.get_object(watchlist_id, request.user)
        serializer = WatchlistSerializer(watchlist_item)
        return Response(success_response(data=serializer.data))
    
    def patch(self, request, watchlist_id):
        """PATCH /api/portfolio/watchlist/{id}"""
        watchlist_item = self.get_object(watchlist_id, request.user)
        
        # Update allowed fields
        if 'notes' in request.data:
            watchlist_item.notes = request.data['notes']
        if 'alert_price_above' in request.data:
            watchlist_item.alert_price_above = request.data['alert_price_above']
        if 'alert_price_below' in request.data:
            watchlist_item.alert_price_below = request.data['alert_price_below']
        
        watchlist_item.save()
        
        serializer = WatchlistSerializer(watchlist_item)
        return Response(
            success_response(
                data=serializer.data,
                message='Watchlist item updated'
            )
        )
    
    def delete(self, request, watchlist_id):
        """DELETE /api/portfolio/watchlist/{id}"""
        watchlist_item = self.get_object(watchlist_id, request.user)
        watchlist_item.delete()
        
        return Response(
            success_response(message='Removed from watchlist'),
            status=status.HTTP_200_OK
        )
