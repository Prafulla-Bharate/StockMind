"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from django.http import HttpResponse


def index(request):
        """Simple root landing page for development.

        Returns a small HTML page linking to the admin UI and API endpoints.
        This prevents the default 404 for the empty path during local development.
        """
        html = """
        <html>
            <head><title>StockMind Backend</title></head>
            <body>
                <h1>StockMind Backend</h1>
                <p>Available endpoints:</p>
                <ul>
                    <li><a href='/admin/'>Admin</a></li>
                    <li><a href='/api/auth/'>Auth API</a></li>
                    <li><a href='/api/market/'>Market API</a></li>
                    <li><a href='/api/portfolio/'>Portfolio API</a></li>
                    <li><a href='/api/analytics/'>Analytics API</a></li>
                </ul>
                <p>Token refresh: <code>/api/token/refresh/</code></p>
            </body>
        </html>
        """
        return HttpResponse(html)

urlpatterns = [
    path('', index),
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/market/', include('apps.market.urls')),
    path('api/portfolio/', include('apps.portfolio.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    
    # JWT token refresh
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)