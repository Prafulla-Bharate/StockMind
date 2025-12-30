#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.market.views import StockDetailView
import json

User = get_user_model()
u, _ = User.objects.get_or_create(email='test@example.com')
factory = APIRequestFactory()
view = StockDetailView.as_view()

for sym in ['AAPL', 'TESLA', 'TATA MOTORS']:
    try:
        req = factory.get(f'/api/market/stock/{sym}')
        force_authenticate(req, user=u)
        resp = view(req, symbol=sym)
        resp.render()
        d = json.loads(resp.content.decode())
        has_symbol = 'symbol' in d.get('data', {})
        print(f"{sym}: status={resp.status_code}, has_symbol={has_symbol}")
        if resp.status_code == 200:
            print(f"  → Price: {d.get('data', {}).get('price')}")
    except Exception as e:
        print(f"{sym}: ERROR - {e}")
