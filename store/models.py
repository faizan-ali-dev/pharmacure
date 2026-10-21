from django.db import models
from django.conf import settings
from django.templatetags.static import static
from django.core.validators import RegexValidator


class Specialization(models.Model):
    """Medical specializations for doctors"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Font Awesome icon class (e.g., fas fa-heart)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Specializations"
    
    def __str__(self):
        return self.name


class Doctor(models.Model):
    """Doctors affiliated with the pharmacy"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    EXPERIENCE_CHOICES = [
        ('0-2', '0-2 years'),
        ('3-5', '3-5 years'),
        ('6-10', '6-10 years'),
        ('11-15', '11-15 years'),
        ('16-20', '16-20 years'),
        ('20+', '20+ years'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    
    title = models.CharField(
        max_length=20,
        default='Dr.',
        help_text="Professional title (Dr., Prof., etc.)"
    )
    
    license_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Medical license number"
    )
    
    specializations = models.ManyToManyField(
        Specialization,
        related_name='doctors',
        help_text="Medical specializations"
    )
    
    years_experience = models.CharField(
        max_length=10,
        choices=EXPERIENCE_CHOICES,
        default='3-5',
        help_text="Years of professional experience"
    )
    
    education = models.TextField(
        help_text="Educational background and qualifications"
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        help_text="Contact phone number"
    )
    
    email = models.EmailField(
        help_text="Professional email address"
    )
    
    clinic_address = models.TextField(
        help_text="Clinic or hospital address"
    )
    
    languages_spoken = models.CharField(
        max_length=200,
        default="Urdu, English",
        help_text="Languages spoken by doctor"
    )
    
    about = models.TextField(
        help_text="Brief description about the doctor"
    )
    
    achievements = models.TextField(
        blank=True,
        help_text="Awards, certifications, and achievements"
    )
    
    website = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        help_text="URL slug (auto-generated)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['license_number']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    @property
    def name_without_title(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_specializations_list(self):
        """Return comma-separated list of specializations."""
        return ", ".join([spec.name for spec in self.specializations.all()])
    
    
    def save(self, *args, **kwargs):
        """Override save to generate slug."""
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify("{}-{}".format(self.first_name, self.last_name))
            slug = base_slug
            counter = 1
            while Doctor.objects.filter(slug=slug).exists():
                slug = "{}-{}".format(base_slug, counter)
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Medicine(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='medicines/', blank=True, null=True)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
    def get_image_url(self):
        """Return medicine image URL or placeholder if no image exists."""
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return static('images/medicine-placeholder.svg')
    
    def has_image(self):
        """Check if medicine has an actual image."""
        return bool(self.image and hasattr(self.image, 'url'))


class Cart(models.Model):
    """Persistent cart model to store cart items for users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['user', 'session_key']]
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Cart for session {self.session_key}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    """Individual items in a cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['cart', 'medicine']]
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.medicine.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Received by User', 'Received by User'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_emergency_delivery = models.BooleanField(default=False)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.medicine} x {self.quantity}"


class Payment(models.Model):
    PAYMENT_METHODS = (
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='COD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment #{self.id} - {self.amount} - {self.status}"


class SalesReport(models.Model):
    REPORT_CHOICES = (
        ('today', 'Today'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('total', 'Total Sales'),
    )

    key = models.CharField(max_length=30, choices=REPORT_CHOICES, unique=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sales Report'
        verbose_name_plural = 'Sales Reports'

    def __str__(self):
        return f"{self.get_key_display()}: {self.amount} (generated {self.generated_at})"
