from django.core.management.base import BaseCommand
from apps.market.models import Stock, StockPrice
from services.market_data.fetcher import MarketDataFetcher
from datetime import datetime


class Command(BaseCommand):
    help = 'Populate historical stock data for all active stocks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            nargs='+',
            type=str,
            help='Specific stock symbols to fetch (e.g., AAPL MSFT)',
        )
        parser.add_argument(
            '--period',
            type=str,
            default='1y',
            help='Time period for historical data (default: 1y)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh even if data exists',
        )

    def handle(self, *args, **options):
        symbols = options.get('symbols')
        period = options.get('period')
        force = options.get('force')

        # Get stocks to process
        if symbols:
            stocks = Stock.objects.filter(symbol__in=symbols, is_active=True)
            if not stocks.exists():
                self.stdout.write(self.style.WARNING(f'No active stocks found for symbols: {symbols}'))
                return
        else:
            stocks = Stock.objects.filter(is_active=True)

        total = stocks.count()
        self.stdout.write(self.style.SUCCESS(f'Processing {total} stocks...'))
        self.stdout.write('')

        fetcher = MarketDataFetcher()
        success_count = 0
        skipped_count = 0
        failed_stocks = []

        for idx, stock in enumerate(stocks, 1):
            self.stdout.write(f'[{idx}/{total}] Processing {stock.symbol}...', ending=' ')

            try:
                # Check existing data
                if not force:
                    existing_count = StockPrice.objects.filter(stock=stock).count()
                    if existing_count >= 100:
                        self.stdout.write(self.style.WARNING(f'SKIP (has {existing_count} records)'))
                        skipped_count += 1
                        continue

                # Fetch historical data
                historical = fetcher.fetch_historical_data(stock.symbol, period=period, interval='1d')

                if not historical:
                    self.stdout.write(self.style.ERROR('FAILED (no data)'))
                    failed_stocks.append(stock.symbol)
                    continue

                # Save to database
                records_saved = 0
                for item in historical:
                    try:
                        timestamp = item['date']
                        if not isinstance(timestamp, datetime):
                            timestamp = datetime.combine(timestamp, datetime.min.time())

                        StockPrice.objects.update_or_create(
                            stock=stock,
                            timestamp=timestamp,
                            defaults={
                                'open': item['open'],
                                'high': item['high'],
                                'low': item['low'],
                                'close': item['close'],
                                'volume': item['volume']
                            }
                        )
                        records_saved += 1
                    except Exception as e:
                        continue

                if records_saved > 0:
                    self.stdout.write(self.style.SUCCESS(f'✓ ({records_saved} records)'))
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR('FAILED (no records saved)'))
                    failed_stocks.append(stock.symbol)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'ERROR: {str(e)}'))
                failed_stocks.append(stock.symbol)
                continue

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Total stocks processed: {total}')
        self.stdout.write(self.style.SUCCESS(f'✓ Success: {success_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'⊘ Skipped: {skipped_count}'))
        if failed_stocks:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {len(failed_stocks)}'))
            self.stdout.write(self.style.ERROR(f'  Failed symbols: {", ".join(failed_stocks)}'))
        self.stdout.write('')

        # Verification
        if success_count > 0:
            self.stdout.write(self.style.SUCCESS('Verifying data...'))
            for stock in stocks:
                count = StockPrice.objects.filter(stock=stock).count()
                status = '✓' if count >= 100 else '✗'
                color = self.style.SUCCESS if count >= 100 else self.style.WARNING
                self.stdout.write(color(f'  {status} {stock.symbol}: {count} records'))
