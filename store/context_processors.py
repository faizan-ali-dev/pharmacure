from .cart_utils import get_cart_count

def cart_count(request):
    """Return total quantity of items in cart for display in navbar."""
    try:
        total = get_cart_count(request)
    except Exception:
        total = 0
    return {'cart_count': total}
