from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/',views.register,name='register'),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('profile/',views.profile,name='profile'),
    path('password-change/',views.password_change,name='password_change'),
    path('translate/', views.translate_page, name='translate_page'),
    path('api/translate/', views.translate_api, name='translate_api'),
    path('search/', views.search, name='search'),
    path('dashboard/', views.dashboard, name='dashboard'),
]