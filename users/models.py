from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)

    def get_full_address(self):
        parts = [self.street, self.city]
        return ', '.join([p for p in parts if p])

    def __str__(self):
        return self.username
