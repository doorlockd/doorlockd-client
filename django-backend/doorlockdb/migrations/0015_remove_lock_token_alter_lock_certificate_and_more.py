# Generated by Django 4.0.1 on 2023-06-20 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doorlockdb', '0014_lock_certificate_delete_lockcertificate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lock',
            name='token',
        ),
        migrations.AlterField(
            model_name='lock',
            name='certificate',
            field=models.TextField(blank=True, default=None, max_length=2000, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='lock',
            name='is_enabled',
            field=models.BooleanField(default=True, help_text="Disable access for all keys on this lock. This lock is still able to synchronize with it's SSL certificate."),
        ),
    ]
