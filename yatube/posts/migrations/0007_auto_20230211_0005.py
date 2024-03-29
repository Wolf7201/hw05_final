# Generated by Django 2.2.19 on 2023-02-10 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20230205_1239'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-pub_date'], 'verbose_name': 'Пост', 'verbose_name_plural': 'Посты'},
        ),
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/', verbose_name='Картинка'),
        ),
    ]
