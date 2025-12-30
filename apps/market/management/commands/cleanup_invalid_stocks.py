"""
Management command to clean up invalid stock records from database
Run with: python manage.py cleanup_invalid_stocks
"""
from django.core.management.base import BaseCommand
from apps.market.models import Stock, StockPrice
from services.market_data.fetcher import MarketDataFetcher
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Remove invalid stock records that have no real market data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No records will be deleted'))
        
        fetcher = MarketDataFetcher()
        all_stocks = Stock.objects.all()
        
        invalid_stocks = []
        valid_count = 0
        
        self.stdout.write(f'Checking {all_stocks.count()} stocks...')
        
        for stock in all_stocks:
            # Check if stock has any price records
            has_prices = StockPrice.objects.filter(stock=stock).exists()
            
            if has_prices:
                # Check if latest price is valid (non-zero)
                latest = StockPrice.objects.filter(stock=stock).order_by('-timestamp').first()
                if latest and latest.close > 0:
                    valid_count += 1
                    continue
            
            # Check if symbol lacks exchange suffix and has no data
            if '.' not in stock.symbol:
                # Validate if it has real data
                if not fetcher.validate_symbol_has_data(stock.symbol):
                    invalid_stocks.append(stock)
                    self.stdout.write(
                        self.style.WARNING(f'  Invalid: {stock.symbol} - {stock.name}')
                    )
                    continue
            
            valid_count += 1
        
        self.stdout.write(f'\nValid stocks: {valid_count}')
        self.stdout.write(f'Invalid stocks: {len(invalid_stocks)}')
        
        if invalid_stocks:
            if dry_run:
                self.stdout.write(self.style.WARNING(f'\nWould delete {len(invalid_stocks)} invalid stocks'))
                for stock in invalid_stocks:
                    self.stdout.write(f'  - {stock.symbol}')
            else:
                self.stdout.write(self.style.WARNING(f'\nDeleting {len(invalid_stocks)} invalid stocks...'))
                for stock in invalid_stocks:
                    self.stdout.write(f'  Deleting: {stock.symbol}')
                    stock.delete()
                
                self.stdout.write(self.style.SUCCESS(f'\n✓ Deleted {len(invalid_stocks)} invalid stock records'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ No invalid stocks found'))
