from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='available_colors',
            field=models.CharField(blank=True, help_text='Comma separated values, for example: Black, White', max_length=255),
        ),
        migrations.AddField(
            model_name='product',
            name='available_sizes',
            field=models.CharField(blank=True, help_text='Comma separated values, for example: S, M, L', max_length=255),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Cash'), ('qr', 'QR')], default='cash', max_length=20),
        ),
        migrations.AddField(
            model_name='order',
            name='selected_color',
            field=models.CharField(blank=True, default='None', max_length=50),
        ),
        migrations.AddField(
            model_name='order',
            name='selected_size',
            field=models.CharField(blank=True, default='None', max_length=50),
        ),
        migrations.AddField(
            model_name='order',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
    ]
