# Generated by Django 5.0.14 on 2025-07-20 22:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0002_post_author"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="title",
            field=models.CharField(max_length=250, unique_for_date="publish"),
        ),
    ]
