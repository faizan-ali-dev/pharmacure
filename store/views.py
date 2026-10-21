from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Medicine, Order, OrderItem, Payment, Doctor, Specialization
from .forms import CheckoutForm
from .cart_utils import (
    get_or_create_cart, add_to_cart as add_item_to_cart, 
    remove_from_cart as remove_item_from_cart,
    update_cart_quantity as update_item_quantity,
    get_cart_items, get_cart_count, get_cart_total, clear_cart
)


def _get_cart(request):
    """Legacy function - kept for backward compatibility"""
    return request.session.get('cart', {})


def _save_cart(request, cart):
    """Legacy function - kept for backward compatibility"""
    request.session['cart'] = cart
    request.session.modified = True


def home(request):
    q = request.GET.get('q', '').strip()
    medicines = Medicine.objects.filter(stock__gt=0)
    if q:
        medicines = medicines.filter(Q(name__icontains=q) | Q(description__icontains=q)).distinct()
    
    featured_doctors = Doctor.objects.prefetch_related('specializations')[:3]
    
    return render(request, 'store/home.html', {
        'medicines': medicines, 
        'query': q,
        'featured_doctors': featured_doctors
    })


def medicine_detail(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    return render(request, 'store/medicine_detail.html', {'medicine': medicine})


def add_to_cart(request, medicine_id):
    """Add medicine to cart (works for both authenticated and anonymous users)"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to add items to cart')
        return redirect('users:login')
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            messages.error(request, 'Invalid quantity')
            return redirect('store:medicine_detail', pk=medicine_id)
        
        success, message = add_item_to_cart(request, medicine_id, quantity)
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': success,
                'message': message,
                'cart_count': get_cart_count(request)
            })
        
        return redirect('store:view_cart')
    
    return redirect('store:medicine_detail', pk=medicine_id)


def view_cart(request):
    """View cart items (works for both authenticated and anonymous users)"""
    cart_items = get_cart_items(request)
    
    items = []
    for cart_item in cart_items:
        items.append({
            'medicine': cart_item.medicine,
            'quantity': cart_item.quantity,
            'subtotal': cart_item.total_price
        })
    
    subtotal = get_cart_total(request)
    total_items = get_cart_count(request)
    
    return render(request, 'store/cart.html', {
        'items': items, 
        'subtotal': subtotal,
        'total': subtotal,
        'total_items': total_items
    })


def update_cart(request, medicine_id):
    """Update cart item quantity"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        success, message = update_item_quantity(request, medicine_id, quantity)
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect('store:view_cart')
    
    return redirect('store:view_cart')


def remove_from_cart(request, medicine_id):
    """Remove item from cart"""
    success, message = remove_item_from_cart(request, medicine_id)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('store:view_cart')


@login_required
def checkout(request):
    """Checkout process using database-based cart"""
    from .cart_utils import get_cart_items, get_cart_total, clear_cart
    
    cart_items_queryset = get_cart_items(request)
    
    if not cart_items_queryset.exists():
        messages.info(request, 'Your cart is empty')
        return redirect('store:home')

    items = []
    subtotal = Decimal('0.00')
    
    for cart_item in cart_items_queryset:
        items.append({
            'medicine': cart_item.medicine,
            'quantity': cart_item.quantity,
            'subtotal': cart_item.total_price
        })
        subtotal += cart_item.total_price

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data['address']
            is_emergency = form.cleaned_data.get('is_emergency_delivery', False)
            total = subtotal
            if is_emergency:
                total += Decimal(str(settings.EMERGENCY_DELIVERY_CHARGE))

            order = Order.objects.create(
                user=request.user,
                address=address,
                total_amount=total,
                is_emergency_delivery=is_emergency,
                status='Pending'
            )
            payment = Payment.objects.create(
                order=order,
                amount=total,
                payment_method='COD',
                status='Completed'
            )
            for it in items:
                OrderItem.objects.create(
                    order=order,
                    medicine=it['medicine'],
                    quantity=it['quantity'],
                    price=it['medicine'].price
                )
                med = it['medicine']
                med.stock = max(0, med.stock - it['quantity'])
                med.save()

            clear_cart(request)
            messages.success(request, 'Order placed successfully')
            return render(request, 'store/order_confirmation.html', {'order': order})
    else:
        initial_address = request.user.get_full_address() or ''
        form = CheckoutForm(initial={'address': initial_address})

    return render(request, 'store/checkout.html', {
        'form': form, 
        'items': items, 
        'subtotal': subtotal,
        'emergency_delivery_charge': settings.EMERGENCY_DELIVERY_CHARGE
    })


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})


@login_required
def mark_order_received(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if order.status == 'Delivered':
        order.status = 'Received by User'
        order.save()
        messages.success(request, 'Order marked as received')
    return redirect('store:my_orders')


def doctors_list(request):
    """Display list of doctors with basic filtering (experience/fee/online removed)."""
    doctors = Doctor.objects.prefetch_related('specializations')
    specializations = Specialization.objects.filter(is_active=True)

    specialization_id = request.GET.get('specialization')
    search = request.GET.get('search', '').strip()

    if specialization_id:
        doctors = doctors.filter(specializations__id=specialization_id)

    if search:
        doctors = doctors.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(specializations__name__icontains=search) |
            Q(about__icontains=search)
        ).distinct()

    doctors = doctors.order_by('last_name', 'first_name')

    paginator = Paginator(doctors, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'doctors': page_obj,
        'specializations': specializations,
        'current_filters': {
            'specialization': specialization_id,
            'search': search,
            'sort_by': 'name',
        }
    }

    return render(request, 'store/doctors_list.html', context)


def doctor_detail(request, slug):
    """Display detailed information about a specific doctor"""
    doctor = get_object_or_404(Doctor, slug=slug)
    context = {'doctor': doctor}

    return render(request, 'store/doctor_detail.html', context)


def featured_doctors(request):
    """Display featured doctors on homepage"""
    doctors = Doctor.objects.prefetch_related('specializations')[:6]
    
    return render(request, 'store/featured_doctors.html', {'doctors': doctors})
