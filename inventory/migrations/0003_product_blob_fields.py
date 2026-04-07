from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_product_options_order_checkout'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image_blob_pathname',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='product',
            name='image_blob_url',
            field=models.URLField(blank=True),
        ),
    ]
