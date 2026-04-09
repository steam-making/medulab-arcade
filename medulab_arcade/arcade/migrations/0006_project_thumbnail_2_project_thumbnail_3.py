from django.db import migrations, models
import arcade.models


class Migration(migrations.Migration):

    dependencies = [
        ('arcade', '0005_remove_project_category_project_categories_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='thumbnail_2',
            field=models.ImageField(blank=True, null=True, upload_to=arcade.models.project_thumbnail_path, verbose_name='썸네일 2'),
        ),
        migrations.AddField(
            model_name='project',
            name='thumbnail_3',
            field=models.ImageField(blank=True, null=True, upload_to=arcade.models.project_thumbnail_path, verbose_name='썸네일 3'),
        ),
    ]
