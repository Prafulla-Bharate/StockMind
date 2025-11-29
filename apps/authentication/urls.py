from django.urls import path
from django.http import HttpResponse
from .views import RegisterView, LoginView,  LogoutView, ProfileView

app_name = 'authentication'


def index(request):
        html = """
        <html>
            <head><title>Auth API</title></head>
            <body>
                <h1>Authentication API</h1>
                <ul>
                    <li><a href='register/'>Register</a></li>
                    <li><a href='login/'>Login</a></li>
                    <li><a href='logout/'>Logout</a></li>
                    <li><a href='profile/'>Profile</a></li>
                </ul>
            </body>
        </html>
        """
        return HttpResponse(html)


urlpatterns = [
        path('', index, name='index'),
        path('register/', RegisterView.as_view(), name='register'),
        path('login/', LoginView.as_view(), name='login'),
        path('logout/', LogoutView.as_view(), name='logout'),
        path('profile/', ProfileView.as_view(), name='profile'),
]

