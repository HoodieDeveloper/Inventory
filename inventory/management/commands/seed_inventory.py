from django.core.management.base import BaseCommand

from inventory.models import Category, Product, User


class Command(BaseCommand):
    help = 'Create demo admin, customer, categories, and products.'

    def handle(self, *args, **options):
        admin_user, _ = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'full_name': 'Inventory Admin',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        admin_user.full_name = 'Inventory Admin'
        admin_user.role = 'admin'
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password('Admin@123')
        admin_user.save()

        customer_user, _ = User.objects.get_or_create(
            email='customer@example.com',
            defaults={
                'full_name': 'Demo Customer',
                'role': 'customer',
            },
        )
        customer_user.full_name = 'Demo Customer'
        customer_user.role = 'customer'
        customer_user.set_password('Customer@123')
        customer_user.save()

        electronics, _ = Category.objects.get_or_create(name='Electronics')
        fashion, _ = Category.objects.get_or_create(name='Fashion')
        groceries, _ = Category.objects.get_or_create(name='Groceries')
        office, _ = Category.objects.get_or_create(name='Office Supplies')

        sample_products = [
            {
                'name': 'Wireless Headphones',
                'category': electronics,
                'stock': 24,
                'price': 79.99,
                'description': 'Comfortable over-ear headphones with crisp sound and long battery life.',
                'available_colors': 'Black, White, Blue',
                'available_sizes': '',
            },
            {
                'name': 'Gaming Mouse',
                'category': electronics,
                'stock': 18,
                'price': 39.99,
                'description': 'High precision mouse with ergonomic design and RGB lighting.',
                'available_colors': 'Black, Red',
                'available_sizes': '',
            },
            {
                'name': 'Cotton T-Shirt',
                'category': fashion,
                'stock': 50,
                'price': 14.99,
                'description': 'Soft cotton t-shirt available in multiple sizes.',
                'available_colors': 'White, Gray, Navy',
                'available_sizes': 'S, M, L, XL',
            },
            {
                'name': 'Notebook Pack',
                'category': office,
                'stock': 60,
                'price': 11.50,
                'description': 'Pack of premium notebooks for office and school use.',
                'available_colors': 'Brown, Blue',
                'available_sizes': '',
            },
            {
                'name': 'Organic Coffee',
                'category': groceries,
                'stock': 30,
                'price': 9.75,
                'description': 'Fresh roasted organic coffee with rich aroma.',
                'available_colors': '',
                'available_sizes': '250g, 500g',
            },
        ]

        for item in sample_products:
            Product.objects.get_or_create(
                name=item['name'],
                defaults={
                    'category': item['category'],
                    'stock': item['stock'],
                    'price': item['price'],
                    'description': item['description'],
                    'available_colors': item.get('available_colors', ''),
                    'available_sizes': item.get('available_sizes', ''),
                },
            )

        self.stdout.write(self.style.SUCCESS('Demo inventory data created successfully.'))
