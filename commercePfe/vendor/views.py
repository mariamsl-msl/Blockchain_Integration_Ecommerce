
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from product.models import Order, Product, OrderItem
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models import F
from django.db.models import Count, Sum
from django.db.models.functions import TruncDay
from django.db import transaction
from product.contract_config import w3, contract, account
from django.contrib.auth.decorators import login_required, user_passes_test
import threading
from django.contrib.admin.views.decorators import staff_member_required
from product.views import auto_confirm_delivery
from .forms import ProductForm, LivreurCreationForm, DeliveryAssignmentForm
from django.contrib.auth import logout, get_user_model
from django.views.decorators.http import require_http_methods
from .models import DeliveryAssignment

def trigger_auto_confirm(order_id):
    thread = threading.Thread(target=auto_confirm_delivery, args=(order_id,))
    thread.start()
    
@csrf_exempt
def mark_in_progress(request, order_id):
    try:
        with transaction.atomic():  # Start atomic transaction
            # 1. Get and verify Django order
            order = Order.objects.select_for_update().get(id=order_id)
            
            # 2. Verify blockchain state
            try:
                blockchain_order = contract.functions.orders(order.id).call()
                if blockchain_order[0] == 0:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Order not found in blockchain'
                    })
                
                # Check current blockchain status matches requirements
                if blockchain_order[8] != 2:  # 2 = NotDelivered in your enum
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Order must be in NotDelivered status on blockchain'
                    })
                
                if blockchain_order[7] != 0:  # 0 = NotPaid in your enum
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Payment must be unconfirmed on blockchain'
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Blockchain verification failed: {str(e)}'
                })

            # 3. Prepare blockchain transaction
            delivery_in_progress = (
                f"Order : {order.id} \\ "
                f"payment_status : {order.payment_status} \\ "
                f"delivery_status : in_progress"
            )

            txn = contract.functions.markInProgress(
                order.id,
                delivery_in_progress
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 3000000,
                'gasPrice': w3.eth.gas_price,
            })

            # 4. Execute blockchain transaction
            signed_txn = account.sign_transaction(txn)
            txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

            if receipt.status != 1:
                raise Exception("Blockchain transaction failed")

            # 5. Update Django model
            order.delivery_status = 'in_progress'
            order.transaction_hash = txn_hash.hex()
            order.save()

            return redirect('order_management')

    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'})
    except Exception as e:
        print(f"❌ Error during marking in progress: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})
    
@csrf_exempt
def mark_delivered(request, order_id):
    try:
        with transaction.atomic():  # Start atomic transaction
            # 1. Get and verify Django order
            order = Order.objects.select_for_update().get(id=order_id)
            
            # 2. Verify blockchain state
            try:
                blockchain_order = contract.functions.orders(order.id).call()
                if blockchain_order[0] == 0:
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'Order not found in blockchain'
                    })
                
                # Check current blockchain status matches requirements
                if blockchain_order[8] != 3:  # 3 = InProgress in your enum
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Order must be in InProgress status on blockchain'
                    })
                
                if blockchain_order[7] != 0:  # 0 = NotPaid in your enum
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Payment must be UNCONFIRMED on blockchain'
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Blockchain verification failed: {str(e)}'
                })

            # 3. Prepare blockchain transaction
            formatted_client = f"client : {order.email} \\"
            formatted_data = f"dataClient : {order.full_name}, {order.phone_number}, {order.address}, {order.city} \\"
            delivery_not_confirm = (
                f"Order : {order.id} \\ "
                f"payment_status : {order.payment_status} \\ "
                f"delivery_status : delivered_not_confirm"
            )
            full_payload = f"{formatted_client}\n{formatted_data}\n{delivery_not_confirm}"

            txn = contract.functions.markDelivered(
                order.id,
                full_payload
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 3000000,
                'gasPrice': w3.eth.gas_price,
            })

            # 4. Execute blockchain transaction
            signed_txn = account.sign_transaction(txn)
            txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

            if receipt.status != 1:
                raise Exception("Blockchain transaction failed")

            # 5. Update Django model
            order.delivery_status = 'delivered_not_confirm'
            order.transaction_hash = txn_hash.hex()
            order.save()

            # 6. Launch auto-confirmation timer
            trigger_auto_confirm(order.id)

            return redirect('order_management')

    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'})
    except Exception as e:
        print(f"❌ Error during marking as delivered: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})




# Vérifie si l'utilisateur est un superutilisateur
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def order_management(request):
    # Filtrez les commandes qui ne sont pas encore livrées
    orders = Order.objects.filter(delivery_status__in=['not_delivered', 'in_progress'])
    return render(request, 'vendor/order_management.html', {'orders': orders})

@staff_member_required
def product_control_panel(request):
    # Annotate each product with the number of times it appears in OrderItem
    products = Product.objects.annotate(
        total_orders=Count('orderitem')
    )
    return render(request, 'vendor/product_control.html', {'products': products})

@staff_member_required
def admin_dashboard(request):
    today = now().date()
    month_start = today.replace(day=1)

    total_orders_today = Order.objects.filter(timestamp__date=today).count()
    total_orders_month = Order.objects.filter(timestamp__gte=month_start).count()
    total_buyers = Order.objects.values('email').distinct().count()

    top_products = OrderItem.objects.values('product__name').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:5]

    # Revenu journalier basé sur les OrderItem liés à des Order payés
    daily_revenue_qs = OrderItem.objects.filter(order__payment_status='paid').annotate(
        day=TruncDay('order__timestamp')
    ).values('day').annotate(
        total=Sum(F('product__price') * F('quantity'))
    ).order_by('day')

    # Convert QuerySet to list of dicts with serializable data:
    daily_revenue = [
        {
            'day': item['day'].strftime('%Y-%m-%d'),  # format datetime.date to string
            'total': float(item['total'] or 0)        # ensure decimal -> float
        }
        for item in daily_revenue_qs
    ]

    # Stripe success/failure
    stripe_success = Order.objects.filter(payment_status='paid').count()
    stripe_failure = Order.objects.filter(payment_status='not_paid').count()

    # Recent orders
    recent_orders = Order.objects.all().order_by('-timestamp')[:10]

    context = {
        'total_orders_today': total_orders_today,
        'total_orders_month': total_orders_month,
        'total_buyers': total_buyers,
        'top_products': top_products,
        'daily_revenue': daily_revenue,
        'stripe_success': stripe_success,
        'stripe_failure': stripe_failure,
        'recent_orders': recent_orders,
    }
    return render(request, 'vendor/admin_dashboard.html', context)

@staff_member_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)  # ⛔️ Ne sauvegarde pas tout de suite
            product.seller = request.user      # ✅ Définit le vendeur comme l'utilisateur connecté
            product.save()                     # ✅ Puis sauvegarde le produit
            return redirect('product_panel')
    else:
        form = ProductForm()
    return render(request, 'vendor/add_product.html', {'form': form})

@staff_member_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_panel')
    else:
        form = ProductForm(instance=product)
    return render(request, 'vendor/edit_product.html', {'form': form, 'product': product})

@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('product_panel')
    return render(request, 'vendor/delete_product.html', {'product': product})

@require_http_methods(["GET"])
def logout(request):
    logout(request)
    return redirect('login')  # or 'login' or any other page

@staff_member_required
def add_delivery(request):
    if request.method == 'POST':
        form = LivreurCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Pas besoin de commit=False ni de set manuels
            return redirect('admin_dashboard')
    else:
        form = LivreurCreationForm()
    return render(request, 'vendor/add_delivery_person.html', {'form': form})

from django.contrib.auth import get_user_model

@staff_member_required
def list_delivery_persons(request):
    CustomUser = get_user_model()
    delivery_users = CustomUser.objects.filter(is_livreur=True)
    return render(request, 'vendor/list_delivery_persons.html', {'delivery_users': delivery_users})

@staff_member_required
def assign_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Prevent re-assigning
    if DeliveryAssignment.objects.filter(order=order).exists():
        return redirect('order_management')  # or show a message

    if request.method == 'POST':
        form = DeliveryAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.order = order
            assignment.save()
            order.delivery_status = "in_progress"
            order.save()
            return redirect('order_management')
    else:
        form = DeliveryAssignmentForm()

    return render(request, 'vendor/assign_delivery.html', {'form': form, 'order': order})

@login_required
def role_based_redirect(request):
    user = request.user
    if user.is_superuser or user.is_staff:
        return redirect('admin_dashboard')  # ou '/vendor/order-management/'
    elif user.is_livreur:
        return redirect('livreur_dashboard')  # ou '/vendor/livreur/dashboard/'
    else:
        # autre redirection par défaut
        return redirect('home')  # ou une page d'accueil générale
    
@login_required
def admin_profile(request):
    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return redirect('admin_profile')

    return render(request, 'vendor/admin_profile.html', {'user': user})