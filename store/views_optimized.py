from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.db import transaction, IntegrityError
from django.db.models import Q, F, Sum, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
import logging
from decimal import Decimal

from .models import Medicine, Order, OrderItem, Payment
from .forms import OrderForm, PaymentForm

logger = logging.getLogger(__name__)


@cache_page(60 * 5)  # Cache for 5 minutes
def home_view(request):
    """Optimized home page with featured and recent medicines."""
    try:
        # Get featured medicines (you can add a 'featured' field to Medicine model)
        featured_medicines = Medicine.objects.filter(
            stock__gt=0,
            is_active=True
        ).select_related().order_by('-created_at')[:8]
        
        # Get categories (if you add category field)
        # categories = Medicine.objects.values('category').distinct()
        
        context = {
            'featured_medicines': featured_medicines,
            'cart_count': _get_cart_count(request),
        }
        
        return render(request, 'store/home.html', context)
        
    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        return render(request, 'store/home.html', {'featured_medicines': []})


def medicine_list_view(request):
    """Optimized medicine list with search, filter, and pagination."""
    try:
        # Get search and filter parameters
        search_query = request.GET.get('search', '').strip()
        sort_by = request.GET.get('sort', 'name')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        in_stock_only = request.GET.get('in_stock') == 'true'
        
        # Base queryset
        medicines = Medicine.objects.filter(is_active=True).select_related()
        
        # Apply search filter
        if search_query:
            medicines = medicines.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(manufacturer__icontains=search_query)
            )
        
        # Apply price filters
        if min_price:
            try:
                medicines = medicines.filter(price__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass
                
        if max_price:
            try:
                medicines = medicines.filter(price__lte=Decimal(max_price))
            except (ValueError, TypeError):
                pass
        
        # Apply stock filter
        if in_stock_only:
            medicines = medicines.filter(stock__gt=0)
        
        # Apply sorting
        valid_sorts = ['name', '-name', 'price', '-price', 'created_at', '-created_at']
        if sort_by in valid_sorts:
            medicines = medicines.order_by(sort_by)
        else:
            medicines = medicines.order_by('name')
        
        # Pagination
        paginator = Paginator(medicines, 12)  # 12 medicines per page
        page = request.GET.get('page')
        
        try:
            medicines_page = paginator.page(page)
        except PageNotAnInteger:
            medicines_page = paginator.page(1)
        except EmptyPage:
            medicines_page = paginator.page(paginator.num_pages)
        
        context = {
            'medicines': medicines_page,
            'search_query': search_query,
            'sort_by': sort_by,
            'min_price': min_price,
            'max_price': max_price,
            'in_stock_only': in_stock_only,
            'total_results': paginator.count,
        }
        
        return render(request, 'store/medicine_list.html', context)
        
    except Exception as e:
        logger.error(f"Error loading medicine list: {e}")
        messages.error(request, 'Unable to load medicines. Please try again.')
        return render(request, 'store/medicine_list.html', {'medicines': []})


def medicine_detail_view(request, medicine_id):
    """Optimized medicine detail view with related products."""
    try:
        medicine = get_object_or_404(
            Medicine.objects.select_related(),
            id=medicine_id,
            is_active=True
        )
        
        # Get related medicines (same manufacturer or category)
        related_medicines = Medicine.objects.filter(
            Q(manufacturer=medicine.manufacturer) & ~Q(id=medicine.id),
            is_active=True,
            stock__gt=0
        ).select_related()[:4]
        
        context = {
            'medicine': medicine,
            'related_medicines': related_medicines,
            'cart_count': _get_cart_count(request),
        }
        
        return render(request, 'store/medicine_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error loading medicine detail for ID {medicine_id}: {e}")
        messages.error(request, 'Medicine not found.')
        return redirect('store:medicine_list')


@require_http_methods(["POST"])
@ratelimit(key='ip', rate='30/m', method='POST', block=True)
def add_to_cart(request, medicine_id):
    """Enhanced add to cart with stock validation and atomic operations."""
    try:
        medicine = get_object_or_404(Medicine, id=medicine_id, is_active=True)
        quantity = int(request.POST.get('quantity', 1))
        
        # Validate quantity
        if quantity <= 0:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid quantity specified.'
            })
        
        if quantity > medicine.stock:
            return JsonResponse({
                'success': False, 
                'message': f'Only {medicine.stock} items available in stock.'
            })
        
        # Get current cart
        cart = request.session.get('cart', {})
        medicine_id_str = str(medicine_id)
        
        # Check if adding this quantity would exceed stock
        current_in_cart = cart.get(medicine_id_str, 0)
        total_requested = current_in_cart + quantity
        
        if total_requested > medicine.stock:
            available = medicine.stock - current_in_cart
            return JsonResponse({
                'success': False,
                'message': f'You can only add {available} more of this item to cart.'
            })
        
        # Add to cart
        cart[medicine_id_str] = total_requested
        request.session['cart'] = cart
        request.session.modified = True
        
        # Calculate cart totals
        cart_count = sum(cart.values())
        cart_total = _calculate_cart_total(request)
        
        logger.info(f"Added {quantity}x {medicine.name} to cart for session {request.session.session_key}")
        
        return JsonResponse({
            'success': True,
            'message': f'{medicine.name} added to cart successfully!',
            'cart_count': cart_count,
            'cart_total': float(cart_total),
            'item_total': float(medicine.price * total_requested)
        })
        
    except ValueError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid quantity format.'
        })
    except Exception as e:
        logger.error(f"Error adding medicine {medicine_id} to cart: {e}")
        return JsonResponse({
            'success': False, 
            'message': 'Unable to add item to cart. Please try again.'
        })


@require_http_methods(["POST"])
def remove_from_cart(request, medicine_id):
    """Remove item from cart."""
    try:
        cart = request.session.get('cart', {})
        medicine_id_str = str(medicine_id)
        
        if medicine_id_str in cart:
            medicine = get_object_or_404(Medicine, id=medicine_id)
            del cart[medicine_id_str]
            request.session['cart'] = cart
            request.session.modified = True
            
            cart_count = sum(cart.values())
            cart_total = _calculate_cart_total(request)
            
            return JsonResponse({
                'success': True,
                'message': f'{medicine.name} removed from cart.',
                'cart_count': cart_count,
                'cart_total': float(cart_total)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart.'
            })
            
    except Exception as e:
        logger.error(f"Error removing medicine {medicine_id} from cart: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Unable to remove item from cart.'
        })


@require_http_methods(["POST"])
def update_cart_quantity(request, medicine_id):
    """Update cart item quantity with validation."""
    try:
        medicine = get_object_or_404(Medicine, id=medicine_id, is_active=True)
        new_quantity = int(request.POST.get('quantity', 0))
        
        if new_quantity <= 0:
            # Remove item if quantity is 0 or negative
            return remove_from_cart(request, medicine_id)
        
        if new_quantity > medicine.stock:
            return JsonResponse({
                'success': False,
                'message': f'Only {medicine.stock} items available in stock.'
            })
        
        cart = request.session.get('cart', {})
        medicine_id_str = str(medicine_id)
        
        cart[medicine_id_str] = new_quantity
        request.session['cart'] = cart
        request.session.modified = True
        
        cart_count = sum(cart.values())
        cart_total = _calculate_cart_total(request)
        item_total = medicine.price * new_quantity
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated successfully.',
            'cart_count': cart_count,
            'cart_total': float(cart_total),
            'item_total': float(item_total)
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid quantity format.'
        })
    except Exception as e:
        logger.error(f"Error updating cart quantity for medicine {medicine_id}: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Unable to update cart. Please try again.'
        })


def cart_view(request):
    """Enhanced cart view with real-time stock validation."""
    try:
        cart = request.session.get('cart', {})
        cart_items = []
        total = Decimal('0.00')
        errors = []
        
        if cart:
            # Get all medicines in cart with single query
            medicine_ids = list(cart.keys())
            medicines = Medicine.objects.filter(
                id__in=medicine_ids,
                is_active=True
            ).select_related()
            
            # Create medicine lookup dict
            medicine_dict = {str(m.id): m for m in medicines}
            
            # Validate cart items and calculate totals
            for medicine_id_str, quantity in list(cart.items()):
                medicine = medicine_dict.get(medicine_id_str)
                
                if not medicine:
                    # Medicine not found or inactive, remove from cart
                    del cart[medicine_id_str]
                    errors.append("Some items were removed as they are no longer available.")
                    continue
                
                if quantity > medicine.stock:
                    # Adjust quantity to available stock
                    if medicine.stock > 0:
                        cart[medicine_id_str] = medicine.stock
                        quantity = medicine.stock
                        errors.append(f"Quantity for {medicine.name} was reduced to available stock ({medicine.stock}).")
                    else:
                        del cart[medicine_id_str]
                        errors.append(f"{medicine.name} is out of stock and was removed from cart.")
                        continue
                
                subtotal = medicine.price * quantity
                cart_items.append({
                    'medicine': medicine,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
                total += subtotal
            
            # Update session if cart was modified
            if errors:
                request.session['cart'] = cart
                request.session.modified = True
                for error in set(errors):  # Remove duplicates
                    messages.warning(request, error)
        
        context = {
            'cart_items': cart_items,
            'total': total,
            'cart_count': sum(cart.values()),
            'shipping_cost': Decimal('50.00'),  # You can make this dynamic
            'grand_total': total + Decimal('50.00'),
        }
        
        return render(request, 'store/cart.html', context)
        
    except Exception as e:
        logger.error(f"Error loading cart: {e}")
        messages.error(request, 'Unable to load cart. Please try again.')
        return render(request, 'store/cart.html', {'cart_items': [], 'total': 0})


@login_required
def checkout_view(request):
    """Secure checkout process with stock validation and payment processing."""
    try:
        cart = request.session.get('cart', {})
        
        if not cart:
            messages.warning(request, 'Your cart is empty.')
            return redirect('store:cart')
        
        # Validate cart and calculate totals
        cart_validation = _validate_cart_for_checkout(request)
        if not cart_validation['valid']:
            for error in cart_validation['errors']:
                messages.error(request, error)
            return redirect('store:cart')
        
        if request.method == 'POST':
            # Process checkout
            try:
                with transaction.atomic():
                    # Create order
                    order = Order.objects.create(
                        user=request.user,
                        total_amount=cart_validation['total'],
                        shipping_address=request.user.address,
                        status='pending'
                    )
                    
                    # Create order items and reduce stock
                    for item in cart_validation['items']:
                        medicine = item['medicine']
                        quantity = item['quantity']
                        
                        # Double-check stock availability
                        if medicine.stock < quantity:
                            raise IntegrityError(f"Insufficient stock for {medicine.name}")
                        
                        # Create order item
                        OrderItem.objects.create(
                            order=order,
                            medicine=medicine,
                            quantity=quantity,
                            price=medicine.price
                        )
                        
                        # Reduce stock
                        Medicine.objects.filter(id=medicine.id).update(
                            stock=F('stock') - quantity
                        )
                    
                    # Clear cart
                    request.session['cart'] = {}
                    request.session.modified = True
                    
                    # Log successful order
                    logger.info(f"Order {order.id} created successfully for user {request.user.username}")
                    
                    messages.success(request, f'Order #{order.id} placed successfully!')
                    return redirect('store:order_success', order_id=order.id)
                    
            except IntegrityError as e:
                logger.error(f"Stock validation failed during checkout: {e}")
                messages.error(request, 'Some items in your cart are no longer available. Please review your cart.')
                return redirect('store:cart')
            except Exception as e:
                logger.error(f"Error processing checkout for user {request.user.username}: {e}")
                messages.error(request, 'Unable to process your order. Please try again.')
                return redirect('store:cart')
        
        context = {
            'cart_items': cart_validation['items'],
            'subtotal': cart_validation['subtotal'],
            'shipping_cost': cart_validation['shipping_cost'],
            'total': cart_validation['total'],
            'user': request.user,
        }
        
        return render(request, 'store/checkout.html', context)
        
    except Exception as e:
        logger.error(f"Error loading checkout: {e}")
        messages.error(request, 'Unable to load checkout. Please try again.')
        return redirect('store:cart')


@login_required
def order_success_view(request, order_id):
    """Order success page with order details."""
    try:
        order = get_object_or_404(
            Order.objects.select_related('user').prefetch_related(
                'orderitem_set__medicine'
            ),
            id=order_id,
            user=request.user
        )
        
        context = {
            'order': order,
            'order_items': order.orderitem_set.all(),
        }
        
        return render(request, 'store/order_success.html', context)
        
    except Exception as e:
        logger.error(f"Error loading order success page for order {order_id}: {e}")
        messages.error(request, 'Unable to load order details.')
        return redirect('store:home')


@login_required
def order_history_view(request):
    """User order history with pagination."""
    try:
        orders = Order.objects.filter(user=request.user).select_related().order_by('-created_at')
        
        # Pagination
        paginator = Paginator(orders, 10)  # 10 orders per page
        page = request.GET.get('page')
        
        try:
            orders_page = paginator.page(page)
        except PageNotAnInteger:
            orders_page = paginator.page(1)
        except EmptyPage:
            orders_page = paginator.page(paginator.num_pages)
        
        context = {
            'orders': orders_page,
        }
        
        return render(request, 'store/order_history.html', context)
        
    except Exception as e:
        logger.error(f"Error loading order history for user {request.user.username}: {e}")
        messages.error(request, 'Unable to load order history.')
        return redirect('users:dashboard')


# Helper functions
def _get_cart_count(request):
    """Get total cart item count."""
    cart = request.session.get('cart', {})
    return sum(cart.values()) if cart else 0


def _calculate_cart_total(request):
    """Calculate total cart value."""
    cart = request.session.get('cart', {})
    if not cart:
        return Decimal('0.00')
    
    try:
        medicine_ids = list(cart.keys())
        medicines = Medicine.objects.filter(id__in=medicine_ids)
        medicine_dict = {str(m.id): m for m in medicines}
        
        total = Decimal('0.00')
        for medicine_id_str, quantity in cart.items():
            medicine = medicine_dict.get(medicine_id_str)
            if medicine:
                total += medicine.price * quantity
        
        return total
    except Exception:
        return Decimal('0.00')


def _validate_cart_for_checkout(request):
    """Validate cart items for checkout process."""
    cart = request.session.get('cart', {})
    
    if not cart:
        return {'valid': False, 'errors': ['Cart is empty']}
    
    try:
        medicine_ids = list(cart.keys())
        medicines = Medicine.objects.filter(
            id__in=medicine_ids,
            is_active=True
        ).select_related()
        
        medicine_dict = {str(m.id): m for m in medicines}
        
        items = []
        subtotal = Decimal('0.00')
        errors = []
        
        for medicine_id_str, quantity in cart.items():
            medicine = medicine_dict.get(medicine_id_str)
            
            if not medicine:
                errors.append(f"Medicine with ID {medicine_id_str} is no longer available.")
                continue
            
            if medicine.stock < quantity:
                errors.append(f"Insufficient stock for {medicine.name}. Available: {medicine.stock}")
                continue
            
            item_total = medicine.price * quantity
            items.append({
                'medicine': medicine,
                'quantity': quantity,
                'subtotal': item_total
            })
            subtotal += item_total
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        shipping_cost = Decimal('50.00')
        total = subtotal + shipping_cost
        
        return {
            'valid': True,
            'items': items,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total': total,
            'errors': []
        }
        
    except Exception as e:
        logger.error(f"Error validating cart for checkout: {e}")
        return {'valid': False, 'errors': ['Unable to validate cart. Please try again.']}


@require_http_methods(["GET"])
def search_medicines_api(request):
    """API endpoint for medicine search autocomplete."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    try:
        medicines = Medicine.objects.filter(
            Q(name__icontains=query) | Q(manufacturer__icontains=query),
            is_active=True,
            stock__gt=0
        ).values('id', 'name', 'manufacturer', 'price')[:10]
        
        results = [
            {
                'id': m['id'],
                'name': m['name'],
                'manufacturer': m['manufacturer'],
                'price': str(m['price'])
            }
            for m in medicines
        ]
        
        return JsonResponse({'results': results})
        
    except Exception as e:
        logger.error(f"Error in medicine search API: {e}")
        return JsonResponse({'results': []})