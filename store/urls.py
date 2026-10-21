from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('medicine/<int:pk>/', views.medicine_detail, name='medicine_detail'),
    path('cart/add/<int:medicine_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/update/<int:medicine_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:medicine_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-orders/receive/<int:order_id>/', views.mark_order_received, name='mark_order_received'),
    
    path('doctors/', views.doctors_list, name='doctors_list'),
    path('doctors/<slug:slug>/', views.doctor_detail, name='doctor_detail'),
    path('featured-doctors/', views.featured_doctors, name='featured_doctors'),
]
