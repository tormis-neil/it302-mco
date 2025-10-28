# Generated manually on 2025-10-28
# Remove security fields: failed_login_attempts, locked_until, last_failed_login_at

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_encrypt_existing_emails"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="failed_login_attempts",
        ),
        migrations.RemoveField(
            model_name="user",
            name="locked_until",
        ),
        migrations.RemoveField(
            model_name="user",
            name="last_failed_login_at",
        ),
    ]
