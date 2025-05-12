from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('admin_section', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('summary', models.CharField(help_text='A brief summary of the blog post (max 300 characters)', max_length=300)),
                ('category', models.CharField(choices=[('news', 'News'), ('announcement', 'Announcement'), ('feature', 'Feature'), ('update', 'Update')], default='news', max_length=20)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='blog_attachments/')),
                ('attachment_name', models.CharField(blank=True, help_text='Name to display for the attachment', max_length=100)),
                ('featured_image', models.ImageField(blank=True, null=True, upload_to='blog_images/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_published', models.BooleanField(default=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blogs', to='accounts.customuser')),
            ],
            options={
                'verbose_name': 'Blog Post',
                'verbose_name_plural': 'Blog Posts',
                'ordering': ['-created_at'],
            },
        ),
    ]
