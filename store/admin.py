from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.db.models import Sum, Count
from django.contrib.auth.models import User
from .models import Medicine, Order, OrderItem, Payment, SalesReport, Cart, CartItem, Doctor, Specialization


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_display', 'stock_display', 'stock_status')
    list_filter = ('stock',)
    search_fields = ('name', 'description')
    list_per_page = 20
    ordering = ('name',)
    
    def price_display(self, obj):
        return format_html('<span style="color: #10b981; font-weight: bold;">Rs.{}</span>', obj.price)
    price_display.short_description = 'Price'
    
    def stock_display(self, obj):
        color = '#ef4444' if obj.stock <= 5 else '#f59e0b' if obj.stock <= 10 else '#10b981'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.stock)
    stock_display.short_description = 'Stock'
    
    def stock_status(self, obj):
        if obj.stock <= 5:
            return format_html('<span style="color: #ef4444;">⚠️ Critical</span>')
        elif obj.stock <= 10:
            return format_html('<span style="color: #f59e0b;">⚡ Low</span>')
        else:
            return format_html('<span style="color: #10b981;">✅ Good</span>')
    stock_status.short_description = 'Status'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('medicine', 'quantity', 'price')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id_display', 'user_display', 'status_display', 'total_amount_display', 'created_at_display')
    list_filter = ('status', 'is_emergency_delivery', 'created_at')
    search_fields = ('user__username', 'user__email', 'address')
    inlines = [OrderItemInline]
    actions = ['mark_as_shipped', 'mark_as_delivered']
    list_per_page = 25
    
    def order_id_display(self, obj):
        return format_html('<strong>#{}</strong>', obj.id)
    order_id_display.short_description = 'Order ID'
    
    def user_display(self, obj):
        return format_html('<span title="{}">{}</span>', obj.user.email, obj.user.username)
    user_display.short_description = 'Customer'
    
    def status_display(self, obj):
        colors = {
            'Pending': '#f59e0b',
            'Shipped': '#3b82f6',
            'Delivered': '#10b981',
            'Received by User': '#059669'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.status)
    status_display.short_description = 'Status'
    
    def total_amount_display(self, obj):
        return format_html('<span style="color: #10b981; font-weight: bold;">Rs.{}</span>', obj.total_amount)
    total_amount_display.short_description = 'Total'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%b %d, %Y at %I:%M %p')
    created_at_display.short_description = 'Order Date'

    def mark_as_shipped(self, request, queryset):
        updated = queryset.filter(status='Pending').update(status='Shipped')
        self.message_user(request, f"{updated} orders marked as Shipped.")
    mark_as_shipped.short_description = '🚚 Mark selected orders as Shipped'

    def mark_as_delivered(self, request, queryset):
        updated = queryset.filter(status='Shipped').update(status='Delivered')
        self.message_user(request, f"{updated} orders marked as Delivered.")
    mark_as_delivered.short_description = '✅ Mark selected orders as Delivered'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id_display', 'order_link', 'amount_display', 'status_display', 'created_at_display')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('transaction_id', 'order__user__username')
    list_per_page = 25
    
    def payment_id_display(self, obj):
        return format_html('<strong>#{}</strong>', obj.id)
    payment_id_display.short_description = 'Payment ID'
    
    def order_link(self, obj):
        url = reverse('admin:store_order_change', args=[obj.order.id])
        return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)
    order_link.short_description = 'Order'
    
    def amount_display(self, obj):
        return format_html('<span style="color: #10b981; font-weight: bold;">Rs.{}</span>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def status_display(self, obj):
        colors = {
            'Pending': '#f59e0b',
            'Completed': '#10b981',
            'Failed': '#ef4444'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.status)
    status_display.short_description = 'Status'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%b %d, %Y at %I:%M %p')
    created_at_display.short_description = 'Payment Date'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'medicine', 'quantity', 'price_display')
    list_filter = ('order__status',)
    search_fields = ('order__user__username', 'medicine__name')
    
    def price_display(self, obj):
        return format_html('<span style="color: #10b981; font-weight: bold;">Rs.{}</span>', obj.price)
    price_display.short_description = 'Price'


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ('key', 'amount_display', 'generated_at_display')
    readonly_fields = ('key', 'amount', 'generated_at')
    
    def amount_display(self, obj):
        return format_html('<span style="color: #10b981; font-weight: bold;">Rs.{}</span>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def generated_at_display(self, obj):
        return obj.generated_at.strftime('%b %d, %Y at %I:%M %p')
    generated_at_display.short_description = 'Generated At'


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('total_price_display',)
    fields = ('medicine', 'quantity', 'total_price_display')
    
    def total_price_display(self, obj):
        if obj.id:
            return format_html('<span style="color: #10b981; font-weight: bold;">Rs.{}</span>', obj.total_price)
        return '-'
    total_price_display.short_description = 'Total Price'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_owner', 'total_items_display', 'total_amount_display', 'created_at_display', 'updated_at_display')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'session_key')
    readonly_fields = ('created_at', 'updated_at', 'total_items', 'total_amount')
    inlines = [CartItemInline]
    list_per_page = 20
    
    def cart_owner(self, obj):
        if obj.user:
            return format_html('<span style="color: #2563eb;">👤 {}</span>', obj.user.username)
        return format_html('<span style="color: #6b7280;">🔒 Anonymous ({})</span>', obj.session_key[:10] + '...' if obj.session_key else 'Unknown')
    cart_owner.short_description = 'Owner'
    
    def total_items_display(self, obj):
        return format_html('<span style="color: #f59e0b; font-weight: bold;">{} items</span>', obj.total_items)
    total_items_display.short_description = 'Items'
    
    def total_amount_display(self, obj):
        return format_html('<span style="color: #10b981; font-weight: bold;">Rs.{}</span>', obj.total_amount)
    total_amount_display.short_description = 'Total'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_display.short_description = 'Created'
    
    def updated_at_display(self, obj):
        return obj.updated_at.strftime('%b %d, %Y')
    updated_at_display.short_description = 'Updated'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('medicine_name', 'cart_owner', 'quantity_display', 'total_price_display', 'updated_at_display')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('medicine__name', 'cart__user__username')
    readonly_fields = ('created_at', 'updated_at', 'total_price')
    list_per_page = 20
    
    def medicine_name(self, obj):
        return format_html('<span style="color: #2563eb;">💊 {}</span>', obj.medicine.name)
    medicine_name.short_description = 'Medicine'
    
    def cart_owner(self, obj):
        if obj.cart.user:
            return format_html('<span style="color: #2563eb;">👤 {}</span>', obj.cart.user.username)
        return format_html('<span style="color: #6b7280;">🔒 Anonymous</span>')
    cart_owner.short_description = 'Cart Owner'
    
    def quantity_display(self, obj):
        return format_html('<span style="color: #f59e0b; font-weight: bold;">x{}</span>', obj.quantity)
    quantity_display.short_description = 'Qty'
    
    def total_price_display(self, obj):
        return format_html('<span style="color: #10b981; font-weight: bold;">Rs.{}</span>', obj.total_price)
    total_price_display.short_description = 'Total Price'
    
    def updated_at_display(self, obj):
        return obj.updated_at.strftime('%b %d, %Y at %I:%M %p')
    updated_at_display.short_description = 'Last Updated'


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name_display', 'description_display', 'doctors_count')
    search_fields = ('name', 'description')
    list_per_page = 20
    ordering = ('name',)
    
    def name_display(self, obj):
        icon = obj.icon if obj.icon else '🏥'
        return format_html('<span style="font-size: 16px;">{} {}</span>', icon, obj.name)
    name_display.short_description = 'Specialization'
    
    def description_display(self, obj):
        if len(obj.description) > 60:
            return format_html('<span title="{}">{}</span>', obj.description, obj.description[:60] + '...')
        return obj.description
    description_display.short_description = 'Description'
    
    def doctors_count(self, obj):
        count = obj.doctors.count()
        return format_html('<span style="color: #3b82f6; font-weight: bold;">{} doctors</span>', count)
    doctors_count.short_description = 'Total Doctors'


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('doctor_name_display', 'specializations_display', 'email', 'license_number')
    list_filter = ('specializations', 'gender')
    search_fields = ('first_name', 'last_name', 'license_number', 'email', 'clinic_name')
    filter_horizontal = ('specializations',)
    list_per_page = 20
    ordering = ('first_name', 'last_name')

    fieldsets = (
        ('Personal Information', {
            'fields': ('title', 'first_name', 'last_name', 'gender', 'date_of_birth')
        }),
        ('Professional Information', {
            'fields': ('license_number', 'specializations', 'years_experience', 'education')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'clinic_address')
        }),
        ('Consultation Details', {
            'fields': ('languages_spoken',)
        }),
        ('Additional Information', {
            'fields': ('about', 'achievements'),
            'classes': ('collapse',)
        }),
        ('Social Media & SEO', {
            'fields': ('slug', 'website', 'facebook', 'twitter', 'linkedin'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('slug',)
    
    def doctor_name_display(self, obj):
        photo_icon = '👨‍⚕️' if obj.gender == 'M' else '👩‍⚕️'
        return format_html('<span style="font-size: 16px;">{} {} {} {}</span>', 
                          photo_icon, obj.title, obj.first_name, obj.last_name)
    doctor_name_display.short_description = 'Doctor Name'
    
    def specializations_display(self, obj):
        specs = obj.specializations.all()[:2]  # Show only first 2
        spec_names = [spec.name for spec in specs]
        total_count = obj.specializations.count()
        
        if total_count > 2:
            display = ', '.join(spec_names) + ' (+{} more)'.format(total_count-2)
        else:
            display = ', '.join(spec_names)
            
        return format_html('<span style="color: #2563eb;">{}</span>', display)
    specializations_display.short_description = 'Specializations'