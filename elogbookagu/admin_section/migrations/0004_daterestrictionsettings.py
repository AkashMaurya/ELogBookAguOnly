# Generated by Django 5.1.4 on 2025-04-23 06:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_section', '0003_adminnotification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DateRestrictionSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('past_days_limit', models.PositiveIntegerField(default=7, help_text='Maximum number of days in the past a student can select')),
                ('allow_future_dates', models.BooleanField(default=False, help_text='Whether students can select future dates')),
                ('future_days_limit', models.PositiveIntegerField(default=0, help_text='Maximum number of days in the future a student can select (if future dates are allowed)')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='date_restriction_updates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Date Restriction Setting',
                'verbose_name_plural': 'Date Restriction Settings',
            },
        ),
    ]
