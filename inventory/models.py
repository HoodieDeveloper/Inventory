from decimal import Decimal

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, full_name='', role='customer', **extra_fields):
        if not email:
            raise ValueError('Email address is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, full_name='System Admin', **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email=email, password=password, full_name=full_name, role='admin', **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )

    username = None
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} - {self.get_role_display()}"

    @property
    def is_admin_role(self):
        return self.role == 'admin'


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_blob_url = models.URLField(blank=True)
    image_blob_pathname = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    available_sizes = models.CharField(max_length=255, blank=True, help_text='Comma separated values, for example: S, M, L')
    available_colors = models.CharField(max_length=255, blank=True, help_text='Comma separated values, for example: Black, White')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def option_list(self, raw_value):
        return [item.strip() for item in raw_value.split(',') if item.strip()]

    @property
    def sizes_list(self):
        return self.option_list(self.available_sizes)

    @property
    def colors_list(self):
        return self.option_list(self.available_colors)

    @property
    def display_image_url(self):
        if self.image_blob_url:
            return self.image_blob_url
        if self.image:
            try:
                return self.image.url
            except Exception:
                return ''
        return ''


class Order(models.Model):
    PAYMENT_CHOICES = (
        ('cash', 'Cash'),
        ('qr', 'QR'),
    )

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    selected_color = models.CharField(max_length=50, blank=True, default='None')
    selected_size = models.CharField(max_length=50, blank=True, default='None')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    order_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-order_date']

    def clean(self):
        if not self.customer_id or not self.customer.is_active:
            raise ValidationError('A valid active user is required to place orders.')
        if self.customer.role != 'customer':
            raise ValidationError('Only customer accounts can place orders.')
        if self.quantity > self.product.stock:
            raise ValidationError('Order quantity cannot exceed product stock.')

    def save(self, *args, **kwargs):
        if self.product_id and self.quantity:
            self.total_price = Decimal(self.quantity) * self.product.price
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.pk} - {self.customer.full_name}"
