from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('order-management/', views.order_management, name='order_management'),
    path('mark-in-progress/<int:order_id>/', views.mark_in_progress, name='mark_in_progress'),
    path('mark-delivered/<int:order_id>/', views.mark_delivered, name='mark_delivered'),
    path('login/', auth_views.LoginView.as_view(template_name='vendor/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login/'), name='logout'),
    path(' ', views.admin_dashboard, name='admin_dashboard'),
    path('product_panel/', views.product_control_panel, name='product_panel'),
    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('add_delivery/', views.add_delivery, name='add_delivery'),
    path('delivery_persons/', views.list_delivery_persons, name='delivery_persons'),
    path('assign-delivery/<int:order_id>/', views.assign_delivery, name='assign_delivery'),
    path('redirect-after-login/', views.role_based_redirect, name='role_based_redirect'),


]