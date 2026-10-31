from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Accounts_Module', '0003_userverification_passwordresettoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='userverification',
            name='attempts',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='تلاش‌های ناموفق'),
        ),
        migrations.AddField(
            model_name='passwordresettoken',
            name='attempts',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='تلاش‌های ناموفق'),
        ),
    ]
