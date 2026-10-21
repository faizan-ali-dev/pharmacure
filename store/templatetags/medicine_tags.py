from django import template
from django.templatetags.static import static

register = template.Library()

@register.simple_tag
def medicine_image_url(medicine):
    """
    Return medicine image URL or placeholder if no image exists.
    Usage: {% medicine_image_url medicine %}
    """
    if medicine.image and hasattr(medicine.image, 'url'):
        return medicine.image.url
    return static('images/medicine-no-image.svg')

@register.simple_tag
def medicine_image_tag(medicine, css_class="", alt_text=None):
    """
    Return complete img tag with proper placeholder handling.
    Usage: {% medicine_image_tag medicine "img-fluid" "Alternative text" %}
    """
    image_url = medicine_image_url(medicine)
    alt = alt_text or f"Image for {medicine.name}"
    has_image = bool(medicine.image and hasattr(medicine.image, 'url'))
    
    extra_class = " no-image" if not has_image else ""
    
    return f'<img src="{image_url}" alt="{alt}" class="{css_class}{extra_class}" loading="lazy">'

@register.filter
def has_image(medicine):
    """
    Check if medicine has an actual image.
    Usage: {% if medicine|has_image %}...{% endif %}
    """
    return bool(medicine.image and hasattr(medicine.image, 'url'))

@register.inclusion_tag('store/components/medicine_image.html')
def render_medicine_image(medicine, size="medium", css_class=""):
    """
    Render medicine image with proper placeholder handling.
    Usage: {% render_medicine_image medicine "large" "custom-class" %}
    """
    sizes = {
        'small': {'width': '100px', 'height': '80px'},
        'medium': {'width': '200px', 'height': '160px'},
        'large': {'width': '300px', 'height': '240px'},
        'card': {'width': '100%', 'height': '220px'},
        'detail': {'width': '100%', 'height': '400px'},
    }
    
    size_config = sizes.get(size, sizes['medium'])
    
    return {
        'medicine': medicine,
        'image_url': medicine_image_url(medicine),
        'has_image': has_image(medicine),
        'size_config': size_config,
        'css_class': css_class,
    }