from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.livreur_dashboard, name='livreur_dashboard'),
    path('mark-as-delivered/<int:order_id>/', views.mark_as_delivered, name='mark_as_delivered'),
]