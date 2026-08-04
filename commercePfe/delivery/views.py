import threading
from product.contract_config import w3, contract, account
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from vendor.models import DeliveryAssignment
from product.models import Order
from product.views import auto_confirm_delivery
def is_livreur(user):
    return user.is_authenticated and user.is_livreur

@login_required
@user_passes_test(is_livreur)
def livreur_dashboard(request):
    # Récupérer les commandes assignées à ce livreur
    assignments = DeliveryAssignment.objects.filter(delivery_person=request.user)
    orders = [assignment.order for assignment in assignments]

    context = {
        'orders': orders,
    }
    return render(request, 'delivery/livreur_dashboard.html', context)

def trigger_auto_confirm(order_id):
    thread = threading.Thread(target=auto_confirm_delivery, args=(order_id,))
    thread.start()

def mark_as_delivered(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        # Update local DB
        order.delivery_status = "delivered_not_confirm"
        order.save()

        # 🔁 Lancer l'auto-confirmation automatique après 2 minutes
        trigger_auto_confirm(order.id)

        # Prepare data for blockchain
        deliveryNotConfirm = (
            f"Order : {order.id}\n"
            f"payment_status : {order.payment_status}\n"
            f"delivery_status : {order.delivery_status}\n"
        )

        try:
            txn_hash = contract.functions.markDelivered(order.id, deliveryNotConfirm).transact({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 3000000,
            })

            receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
            if receipt.status == 1:
                print("✅ Blockchain updated successfully!")
            else:
                print("❌ Blockchain transaction failed!")

        except Exception as blockchain_error:
            print(f"[Blockchain Error] {blockchain_error}")

        return redirect('livreur_dashboard')  # ou vers la page où tu veux revenir