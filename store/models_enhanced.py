from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Category(models.Model):
    """Medicine categories for better organization."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Font Awesome icon class (e.g., fas fa-pills)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Medicine manufacturers."""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Medicine(models.Model):
    """Enhanced medicine model with better fields and validation."""
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Medicine name"
    )
    
    generic_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Generic/scientific name"
    )
    
    description = models.TextField(
        help_text="Detailed description of the medicine"
    )
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Medicine category"
    )
    
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Manufacturer"
    )
    
    # Pricing and Stock
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per unit",
        db_index=True
    )
    
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price (for discount calculation)"
    )
    
    stock = models.PositiveIntegerField(
        default=0,
        help_text="Available quantity in stock",
        db_index=True
    )
    
    minimum_stock = models.PositiveIntegerField(
        default=10,
        help_text="Minimum stock level for alerts"
    )
    
    # Medicine Details
    dosage = models.CharField(
        max_length=100,
        blank=True,
        help_text="Dosage information (e.g., 500mg)"
    )
    
    dosage_form = models.CharField(
        max_length=50,
        choices=[
            ('tablet', 'Tablet'),
            ('capsule', 'Capsule'),
            ('syrup', 'Syrup'),
            ('injection', 'Injection'),
            ('ointment', 'Ointment'),
            ('drops', 'Drops'),
            ('inhaler', 'Inhaler'),
            ('powder', 'Powder'),
            ('other', 'Other'),
        ],
        default='tablet',
        help_text="Form of the medicine"
    )
    
    pack_size = models.CharField(
        max_length=50,
        blank=True,
        help_text="Pack size (e.g., 10 tablets, 100ml)"
    )
    
    # Medical Information
    composition = models.TextField(
        blank=True,
        help_text="Active ingredients and composition"
    )
    
    indications = models.TextField(
        blank=True,
        help_text="Medical conditions this medicine treats"
    )
    
    contraindications = models.TextField(
        blank=True,
        help_text="Conditions where this medicine should not be used"
    )
    
    side_effects = models.TextField(
        blank=True,
        help_text="Possible side effects"
    )
    
    dosage_instructions = models.TextField(
        blank=True,
        help_text="How to take this medicine"
    )
    
    # Prescription Requirements
    prescription_required = models.BooleanField(
        default=False,
        help_text="Whether prescription is required"
    )
    
    age_restriction = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Ages'),
            ('adult', 'Adults Only (18+)'),
            ('senior', 'Seniors (65+)'),
            ('child', 'Children Only'),
            ('infant', 'Infants Only'),
        ],
        default='all',
        help_text="Age restrictions"
    )
    
    # Storage and Expiry
    storage_instructions = models.CharField(
        max_length=200,
        default="Store in a cool, dry place",
        help_text="Storage instructions"
    )
    
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expiry date of current stock"
    )
    
    # Media
    image = models.ImageField(
        upload_to='medicines/',
        null=True,
        blank=True,
        help_text="Medicine image"
    )
    
    # SEO and Display
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        help_text="URL slug (auto-generated)"
    )
    
    featured = models.BooleanField(
        default=False,
        help_text="Show on homepage"
    )
    
    # Status and Tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether medicine is available for sale"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times viewed"
    )
    
    purchase_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times purchased"
    )
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['price']),
            models.Index(fields=['stock']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['featured']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.dosage}" if self.dosage else self.name
    
    def is_in_stock(self):
        """Check if medicine is in stock."""
        return self.stock > 0
    
    def is_low_stock(self):
        """Check if medicine is low in stock."""
        return self.stock <= self.minimum_stock
    
    def get_discount_percentage(self):
        """Calculate discount percentage if original price exists."""
        if self.original_price and self.original_price > self.price:
            discount = ((self.original_price - self.price) / self.original_price) * 100
            return round(discount, 1)
        return 0
    
    def is_prescription_required(self):
        """Check if prescription is required."""
        return self.prescription_required
    
    def is_expired(self):
        """Check if medicine is expired."""
        if self.expiry_date:
            return self.expiry_date <= timezone.now().date()
        return False
    
    def save(self, *args, **kwargs):
        """Override save to generate slug."""
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(f"{self.name}-{self.dosage}")
        super().save(*args, **kwargs)


class Order(models.Model):
    """Enhanced order model with better tracking."""
    
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    # Order Identification
    order_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Unique order number"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Order Details
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('50.00')
    )
    
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Addresses
    shipping_address = models.TextField(
        help_text="Delivery address"
    )
    
    billing_address = models.TextField(
        blank=True,
        help_text="Billing address (if different)"
    )
    
    # Contact Information
    phone_number = models.CharField(
        max_length=17,
        help_text="Contact number for delivery"
    )
    
    email = models.EmailField(
        help_text="Email for order updates"
    )
    
    # Special Instructions
    notes = models.TextField(
        blank=True,
        help_text="Special delivery instructions"
    )
    
    # Prescription
    prescription_image = models.ImageField(
        upload_to='prescriptions/',
        null=True,
        blank=True,
        help_text="Prescription image (if required)"
    )
    
    prescription_verified = models.BooleanField(
        default=False,
        help_text="Whether prescription has been verified"
    )
    
    # Tracking
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Shipping tracking number"
    )
    
    estimated_delivery = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Estimated delivery date and time"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['order_number']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        """Generate order number if not exists."""
        if not self.order_number:
            import random
            import string
            self.order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)
    
    def get_total_items(self):
        """Get total number of items in order."""
        return self.orderitem_set.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.status in ['pending', 'confirmed']


class OrderItem(models.Model):
    """Enhanced order item model."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT
    )
    
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price at time of order"
    )
    
    discount_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Discount applied to this item"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['order', 'medicine']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['medicine']),
        ]
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"
    
    def get_subtotal(self):
        """Calculate subtotal for this item."""
        return (self.price * self.quantity) - self.discount_applied


class Payment(models.Model):
    """Enhanced payment model with better tracking."""
    
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('digital_wallet', 'Digital Wallet'),
        ('upi', 'UPI'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Payment Identification
    payment_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="External transaction ID"
    )
    
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    
    # Payment Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cod'
    )
    
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Gateway Information
    gateway_response = models.JSONField(
        null=True,
        blank=True,
        help_text="Payment gateway response data"
    )
    
    gateway_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Payment gateway processing fee"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['payment_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.order.order_number}"


class SalesReport(models.Model):
    """Enhanced sales reporting model."""
    
    REPORT_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    report_date = models.DateField(db_index=True)
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        default='daily'
    )
    
    # Sales Metrics
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_items_sold = models.PositiveIntegerField(default=0)
    
    # Customer Metrics
    new_customers = models.PositiveIntegerField(default=0)
    returning_customers = models.PositiveIntegerField(default=0)
    
    # Product Metrics
    top_selling_medicine = models.ForeignKey(
        Medicine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Financial Metrics
    average_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    shipping_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    discount_given = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['report_date', 'report_type']
        ordering = ['-report_date']
        indexes = [
            models.Index(fields=['report_date']),
            models.Index(fields=['report_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.report_type.title()} Report - {self.report_date}"


class Wishlist(models.Model):
    """User wishlist for medicines."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'medicine']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.medicine.name}"


class Review(models.Model):
    """Product reviews and ratings."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Review title"
    )
    
    comment = models.TextField(
        help_text="Detailed review"
    )
    
    is_verified_purchase = models.BooleanField(
        default=False,
        help_text="Whether user actually purchased this medicine"
    )
    
    is_approved = models.BooleanField(
        default=True,
        help_text="Whether review is approved for display"
    )
    
    helpful_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of users who found this review helpful"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'medicine']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medicine']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.medicine.name} - {self.rating}★ by {self.user.username}"