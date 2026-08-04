# views.py
import stripe
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Order, OrderItem
from .contract_config import w3, contract, account
from django.http import FileResponse, Http404
import os
import time
from decimal import Decimal
from django.db import transaction
from rest_framework.request import Request
from rest_framework.parsers import JSONParser
from django.contrib.auth import authenticate




# Setup Stripe
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

def product_list(request, template_name='product/list_product.html'):
    target_audience = request.GET.get('target_audience')
    main_category = request.GET.get('main_category')
    category = request.GET.get('category')

    products = Product.objects.all()

    if target_audience:
        products = products.filter(target_audience=target_audience)
    if main_category:
        products = products.filter(main_category=main_category)
    if category:
        products = products.filter(category=category)
        
    for product in products:
        if product.image:
            product.full_image_url = request.build_absolute_uri(product.image.url)
        else:
            product.full_image_url = ''

    return render(request, template_name, {
        'products': products,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_TEST_PUBLISHABLE_KEY
    })

def cart(request):
    return render(request, 'product/cart.html', {
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_TEST_PUBLISHABLE_KEY
    })

@csrf_exempt
def create_payment_intent(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = data.get('cart', [])
            
            if not cart:
                return JsonResponse({'error': 'Cart is empty'}, status=400)

            # Calculate total amount in cents
            total_amount = int(sum(float(item['price']) * int(item['quantity']) * 100 for item in cart))
            
            intent = stripe.PaymentIntent.create(
                amount=total_amount,
                currency='usd',
                capture_method='manual',
                automatic_payment_methods={"enabled": True},
                metadata={
                    'cart': json.dumps(cart),
                    'product_ids': ','.join(str(item['id']) for item in cart)
                }
            )
            
            return JsonResponse({
                'clientSecret': intent['client_secret'],
                'payment_intent_id': intent['id']
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def save_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_intent_id = data.get('payment_intent_id')
            
            if not payment_intent_id:
                return JsonResponse({'error': 'Missing payment_intent_id'}, status=400)
            
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            cart = json.loads(intent.metadata.get('cart', '[]'))

            with transaction.atomic():
                # Create Django order with initial statuses
                order = Order.objects.create(
                    full_name=data['full_name'],
                    email=data['email'],
                    phone_number=data['phone_number'],
                    address=data['address'],
                    city=data['city'],
                    payment_status='not_paid',  # Maps to NotPaid (0)
                    delivery_status='not_delivered',  # Maps to NotDelivered (2)
                    payment_method_id=data.get('payment_method_id'),
                    stripe_payment_intent_id=payment_intent_id
                )

                # Prepare order items and calculate total
                formatted_client = f"client : {data['email']} \\"
                formatted_data = f"dataClient : {data['full_name']}, {data['phone_number']}, {data['address']}, {data['city']} \\"
                running_total = Decimal('0.00')
                
                for item in cart:
                    product = get_object_or_404(Product, id=item['id'])
                    seller_name = product.seller.get_full_name() if product.seller else "Unknown Seller"
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        seller_name=seller_name,
                        quantity=int(item['quantity']),
                        price=float(item['price'])
                    )
                    running_total += Decimal(item['price']) * int(item['quantity'])

                formatted_total = f"total : {running_total} \\"
                formatted_seller = " & ".join(
                    [f"{oi.product.name}:{oi.seller_name}" for oi in order.items.all()]
                )
                
                # Map to your smart contract enum values:
                # Status.NotPaid = 0
                # Status.NotDelivered = 2
                final_payload = f"payment_status : 0 \\ delivery_status : 2"
                
                # Blockchain transaction
                txn = contract.functions.placeOrder(
                    order.id,
                    f"Product_seller : {formatted_seller} \\",
                    formatted_total,
                    formatted_client,
                    formatted_data,
                    final_payload
                ).build_transaction({
                    'from': account.address,
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'gas': 3000000,
                    'gasPrice': w3.eth.gas_price,
                })

                signed_txn = account.sign_transaction(txn)
                txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

                if receipt.status != 1:
                    raise Exception("Blockchain transaction failed")

                # Update order with blockchain data
                order.transaction_hash = txn_hash.hex()
                order.blockchain_order_id = order.id
                order.save()

                return JsonResponse({'status': 'success', 'order_id': order.id})

        except Exception as e:
            print(f"Error saving order: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
                
def confirm_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # Check if email is provided and valid
        if not email:
            return render(request, 'product/confirm_email.html', {
                'error': 'Please enter your email.'
            })

        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'product/confirm_email.html', {
                'error': 'Email format is invalid.'
            })

        # Check if email exists in orders
        if not Order.objects.filter(email=email).exists():
            return render(request, 'product/confirm_email.html', {
                'error': 'This email does not exist in any order.'
            })

        # ✅ Email exists and is valid — save to session and redirect
        request.session['client_email'] = email
        return redirect('confirm_delivery')

    # GET request — render the form
    return render(request, 'product/confirm_email.html')
  
def confirm_delivery(request):
    email = request.session.get('client_email')
    if not email:
        return redirect('confirm_email')

    orders = Order.objects.filter(email=email)
    return render(request, 'product/confirm_delivery.html', {
        'orders': orders,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_TEST_PUBLISHABLE_KEY
    })


@csrf_exempt
def update_order_status(request):
    if request.method == 'POST':
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
        data = json.loads(request.body)

        try:
            with transaction.atomic():  # Start atomic transaction
                # 1. Get and verify Django order
                order = Order.objects.select_for_update().get(id=data['order_id'])

                # 2. Verify blockchain state before proceeding
                try:
                    blockchain_order = contract.functions.orders(order.id).call()
                    if blockchain_order[0] == 0:
                        return JsonResponse({
                            'status': 'error', 
                            'message': 'Order not found in blockchain'
                        })
                    
                    # Check current blockchain status matches requirements
                    if blockchain_order[8] != 4:  # 4 = DeliveredNotConfirm in your enum
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Order must be in DeliveredNotConfirm status on blockchain'
                        })

                    # CHANGED THIS - Now checking for CONFIRMED payment (2) instead of UNCONFIRMED (0)
                    if blockchain_order[7] != 0:  # 0 = NotPaid in your enum
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Payment must be not confirmed on blockchain'
                        })
                        
                except Exception as e:
                    return JsonResponse({
                        'status': 'error', 
                        'message': f'Blockchain verification failed: {str(e)}'
                    })

                # 3. Process Stripe payment if payment intent exists
                if order.stripe_payment_intent_id:
                    try:
                        intent = stripe.PaymentIntent.retrieve(order.stripe_payment_intent_id)
                        if intent['status'] == 'requires_capture':
                            stripe.PaymentIntent.capture(order.stripe_payment_intent_id)
                            print("✅ Stripe payment captured.")
                        else:
                            print(f"⚠️ Stripe PaymentIntent {order.stripe_payment_intent_id} already captured or not capturable. Status: {intent['status']}")
                    except Exception as e:
                        print(f"❌ Stripe capture error: {e}")
                        return JsonResponse({'status': 'error', 'message': f'Stripe capture failed: {e}'})

                # 4. Prepare blockchain transaction
                full_info = (
                    f"client : {order.email} \\ \n"
                    f"dataClient : {order.full_name}, {order.phone_number}, {order.address}, {order.city} \\ \n"
                    f"Order : {order.id} \\ \n"
                    f"payment_status : paid \\ \n"
                    f"delivery_status : delivered_confirm"
                )

                # 5. Execute blockchain transaction
                txn = contract.functions.confirmDelivery(
                    order.id,
                    full_info
                ).build_transaction({
                    'from': account.address,
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'gas': 3000000,
                    'gasPrice': w3.eth.gas_price,
                })

                signed_txn = account.sign_transaction(txn)
                txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

                if receipt.status != 1:
                    raise Exception("Blockchain transaction failed")

                # 6. Update Django model
                order.payment_status = "paid"
                order.delivery_status = "delivered_confirm"
                order.transaction_hash = txn_hash.hex()
                order.save()
                

                print("✅ Order status updated successfully!")
                return JsonResponse({'status': 'success', 'message': 'Payment and delivery confirmed successfully'})

        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found'})
        except Exception as e:
            print(f"❌ Error during order confirmation: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def auto_confirm_delivery(order_id):
    print(f"🕒 Waiting 2 minutes before confirming order {order_id}")
    time.sleep(120)  # Wait 2 minutes

    try:
        order = Order.objects.get(id=order_id)

        if order.delivery_status == 'delivered_not_confirm':  # Not confirmed by buyer yet
            print(f"⏰ Auto-confirming order {order.id}")

            # Capture Stripe payment
            if order.stripe_payment_intent_id:
                stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
                intent = stripe.PaymentIntent.retrieve(order.stripe_payment_intent_id)
                if intent['status'] == 'requires_capture':
                    stripe.PaymentIntent.capture(order.stripe_payment_intent_id)
                    print("✅ Stripe payment captured.")
                else:
                    print("⚠️ Payment already captured or not capturable.")

            # Update order
            order.payment_status = 'paid'
            order.delivery_status = 'delivered_confirm'
            order.save()

            # Send to blockchain
            final_payment = (
                f"Order : {order.id}\n"
                f"payment_status : {order.payment_status}\n"
                f"delivery_status : {order.delivery_status}\n"
            )

            txn_hash = contract.functions.confirmDelivery(order.id, final_payment).transact({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 3000000,
            })

            print("🚀 Blockchain auto-confirm tx sent:", txn_hash.hex())
            receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

            if receipt.status == 1:
                print("✅ Blockchain auto-confirm success")
            else:
                print("❌ Blockchain auto-confirm failed")

    except Exception as e:
        print(f"❌ Auto-confirm error: {e}")
        
@csrf_exempt
def cancel_order(request, order_id):
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
                # Allow cancellation from either NotDelivered (2)
                if blockchain_order[8] not in [2]:  # 2=NotDelivered
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Order can only be cancelled from NotDelivered or InProgress status'
                    })
                
                # Payment status check - consistent with mark_delivered logic
                if blockchain_order[7] != 0:  # 0 = NotPaid
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Payment must be unconfirmed to cancel'
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Blockchain verification failed: {str(e)}'
                })

            # 3. Prepare blockchain transaction with detailed payload like mark_delivered
            formatted_client = f"client : {order.email} \\"
            formatted_data = f"dataClient : {order.full_name}, {order.phone_number}, {order.address}, {order.city} \\"
            cancellation_payload = (
                f"Order : {order.id} \\ "
                f"payment_status : {order.payment_status} \\ "
                f"delivery_status : cancelled"
            )
            full_payload = f"{formatted_client}\n{formatted_data}\n{cancellation_payload}"

            # 4. Execute blockchain transaction with proper error handling
            try:
                txn = contract.functions.deliveryCancelled(
                    order.id,
                    full_payload
                ).build_transaction({
                    'from': account.address,
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'gas': 3000000,
                    'gasPrice': w3.eth.gas_price,
                })

                signed_txn = account.sign_transaction(txn)
                txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

                if receipt.status != 1:
                    raise Exception("Blockchain transaction failed")

                # 5. Update Django model
                order.delivery_status = 'cancelled'
                order.transaction_hash = txn_hash.hex()
                order.save()

                return JsonResponse({
                    'status': 'success', 
                    'message': 'Order cancelled successfully',
                    'txn_hash': txn_hash.hex()
                })

            except Exception as e:
                error_msg = str(e)
                # Handle specific blockchain errors more gracefully
                if "revert Payment must be confirmed" in error_msg:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Payment status mismatch with blockchain'
                    })
                raise

    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'})
    except Exception as e:
        print(f"❌ Error during order cancellation: {str(e)}")
        return JsonResponse({
            'status': 'error', 
            'message': f'Order cancellation failed: {str(e)}'
        })
        
@csrf_exempt
def return_requested(request, order_id):
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
                if blockchain_order[8] != 4:  # 4= DeliveredNotConfirm
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Order can only be returned for DeliveredNotConfirm status'
                    })
                
                # Payment status check - consistent with mark_delivered logic
                if blockchain_order[7] != 0:  # 0 = NotPaid
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Payment must be unconfirmed to return requested'
                    })
                    
            except Exception as e:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Blockchain verification failed: {str(e)}'
                })

            # 3. Prepare blockchain transaction with detailed payload like mark_delivered
            formatted_client = f"client : {order.email} \\"
            formatted_data = f"dataClient : {order.full_name}, {order.phone_number}, {order.address}, {order.city} \\"
            cancellation_payload = (
                f"Order : {order.id} \\ "
                f"payment_status : {order.payment_status} \\ "
                f"delivery_status : return_requested"
            )
            full_payload = f"{formatted_client}\n{formatted_data}\n{cancellation_payload}"

            # 4. Execute blockchain transaction with proper error handling
            try:
                txn = contract.functions.requestReturn(
                    order.id,
                    full_payload
                ).build_transaction({
                    'from': account.address,
                    'nonce': w3.eth.get_transaction_count(account.address),
                    'gas': 3000000,
                    'gasPrice': w3.eth.gas_price,
                })

                signed_txn = account.sign_transaction(txn)
                txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

                if receipt.status != 1:
                    raise Exception("Blockchain transaction failed")

                # 5. Update Django model
                order.delivery_status = 'return_requested'
                order.transaction_hash = txn_hash.hex()
                order.save()

                return JsonResponse({
                    'status': 'success', 
                    'message': 'Order cancelled successfully',
                    'txn_hash': txn_hash.hex()
                })

            except Exception as e:
                error_msg = str(e)
                # Handle specific blockchain errors more gracefully
                if "revert Payment must be confirmed" in error_msg:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Payment status mismatch with blockchain'
                    })
                raise

    except Order.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Order not found'})
    except Exception as e:
        print(f"❌ Error during order return request: {str(e)}")
        return JsonResponse({
            'status': 'error', 
            'message': f'Order return request failed: {str(e)}'
        })
        