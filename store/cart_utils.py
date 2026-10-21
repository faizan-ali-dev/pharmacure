from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, Medicine


def get_or_create_cart(request):
    """Get or create cart for current user/session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            session_key=None
        )
        
        if hasattr(request, '_cart_merged'):
            return cart
            
        session_cart_data = request.session.get('cart', {})
        if session_cart_data and not created:
            merge_session_cart_to_user_cart(request, cart, session_cart_data)
            request.session['cart'] = {}
            request._cart_merged = True
            
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
            
        cart, created = Cart.objects.get_or_create(
            user=None,
            session_key=session_key
        )
    
    return cart


def merge_session_cart_to_user_cart(request, user_cart, session_cart_data):
    """Merge session cart data into user's persistent cart"""
    for medicine_id, quantity in session_cart_data.items():
        try:
            medicine = Medicine.objects.get(id=int(medicine_id))
            cart_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                medicine=medicine,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
                
        except (Medicine.DoesNotExist, ValueError):
            continue


def add_to_cart(request, medicine_id, quantity=1):
    """Add item to cart"""
    medicine = get_object_or_404(Medicine, id=medicine_id)
    cart = get_or_create_cart(request)
    
    if medicine.stock < quantity:
        return False, f"Only {medicine.stock} items available in stock"
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        medicine=medicine,
        defaults={'quantity': quantity}
    )
    
    if not created:
        new_quantity = cart_item.quantity + quantity
        if medicine.stock < new_quantity:
            return False, f"Cannot add {quantity} more. Only {medicine.stock - cart_item.quantity} available"
        cart_item.quantity = new_quantity
        cart_item.save()
    
    return True, f"Added {quantity} x {medicine.name} to cart"


def remove_from_cart(request, medicine_id):
    """Remove item from cart"""
    cart = get_or_create_cart(request)
    try:
        cart_item = CartItem.objects.get(cart=cart, medicine_id=medicine_id)
        medicine_name = cart_item.medicine.name
        cart_item.delete()
        return True, f"Removed {medicine_name} from cart"
    except CartItem.DoesNotExist:
        return False, "Item not found in cart"


def update_cart_quantity(request, medicine_id, quantity):
    """Update quantity of item in cart"""
    cart = get_or_create_cart(request)
    try:
        cart_item = CartItem.objects.get(cart=cart, medicine_id=medicine_id)
        medicine = cart_item.medicine
        
        if quantity <= 0:
            cart_item.delete()
            return True, f"Removed {medicine.name} from cart"
        
        if medicine.stock < quantity:
            return False, f"Only {medicine.stock} items available in stock"
        
        cart_item.quantity = quantity
        cart_item.save()
        return True, f"Updated {medicine.name} quantity to {quantity}"
        
    except CartItem.DoesNotExist:
        return False, "Item not found in cart"


def get_cart_items(request):
    """Get all cart items for current user/session"""
    cart = get_or_create_cart(request)
    return cart.items.select_related('medicine').all()


def get_cart_count(request):
    """Get total number of items in cart"""
    cart = get_or_create_cart(request)
    return cart.total_items


def get_cart_total(request):
    """Get total amount of cart"""
    cart = get_or_create_cart(request)
    return cart.total_amount


def clear_cart(request):
    """Clear all items from cart"""
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return True, "Cart cleared successfully"


def transfer_cart_to_user(request, user):
    """Transfer anonymous cart to authenticated user (called during login)"""
    if not request.session.session_key:
        return
    
    try:
        anonymous_cart = Cart.objects.get(
            user=None,
            session_key=request.session.session_key
        )
        
        user_cart, created = Cart.objects.get_or_create(
            user=user,
            session_key=None
        )
        
        for item in anonymous_cart.items.all():
            user_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                medicine=item.medicine,
                defaults={'quantity': item.quantity}
            )
            
            if not created:
                user_item.quantity += item.quantity
                user_item.save()
        
        anonymous_cart.delete()
        
    except Cart.DoesNotExist:
        pass