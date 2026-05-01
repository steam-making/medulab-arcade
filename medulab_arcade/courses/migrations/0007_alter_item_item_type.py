from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0006_homeworkattachment_homeworksubmission"),
    ]

    operations = [
        migrations.AlterField(
            model_name="item",
            name="item_type",
            field=models.CharField(
                choices=[
                    ("example", "예제"),
                    ("objective", "객관식"),
                    ("problem", "실습문제"),
                    ("project", "프로젝트"),
                    ("homework", "과제"),
                ],
                default="example",
                max_length=50,
                verbose_name="유형",
            ),
        ),
    ]
