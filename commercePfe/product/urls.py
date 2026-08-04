from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),  # 📌 Affiche la liste des produits
    path('cart/', views.cart, name='cart'),  # 📦 Affiche les détails d'un produit
    path('create_payment_intent/', views.create_payment_intent, name='create_payment_intent'),  # 🛒 Crée un paiement Stripe (non capturé)
    path('save_order/', views.save_order, name='save_order'),  # 💾 Enregistre la commande en base et sur blockchain
    path('confirm_email/', views.confirm_email, name='confirm_email'),  # 📧 Confirme l'email de l'utilisateur
    path('confirm_delivery/', views.confirm_delivery, name='confirm_delivery'),
    path('update_order_status/', views.update_order_status, name='update_order_status'),  # ✅ Affiche la page de succès de commande
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),  # ❌ Annule la commande
    path('return_order/<int:order_id>/', views.return_requested, name='return_order'),  # 🔄 Demande de retour de commande

]