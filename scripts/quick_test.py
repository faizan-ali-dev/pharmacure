import os
import sys
import pathlib
import django

# Ensure project root is on PYTHONPATH so 'pharmacure_project' package can be imported
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharmacure_project.settings')
django.setup()

from users.models import CustomUser
from store.models import Medicine, Order, OrderItem

# Create superuser if not exists
if not CustomUser.objects.filter(username='admin').exists():
    CustomUser.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
    print('Superuser "admin" created with password "adminpass"')
else:
    print('Superuser "admin" already exists')

# Create sample medicine
med, created = Medicine.objects.get_or_create(name='Paracetamol', defaults={'description':'Sample painkiller','price':'50.00','stock':100})
if created:
    print('Sample medicine created:', med.name)
else:
    print('Sample medicine already exists:', med.name)

# Create a sample order for admin user
user = CustomUser.objects.get(username='admin')
order = Order.objects.create(user=user, address='123 Test St, Test City', total_amount=med.price, is_emergency_delivery=False)
OrderItem.objects.create(order=order, medicine=med, quantity=1, price=med.price)
print('Created sample order id:', order.id)
