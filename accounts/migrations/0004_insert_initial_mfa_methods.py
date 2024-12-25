# Generated manually for initial MFA methods

from django.db import migrations

def insert_initial_mfa_methods(apps, schema_editor):
    MFAMethod = apps.get_model('accounts', 'MFAMethod')
    
    # Crear método OTP
    MFAMethod.objects.create(
        name='otp',
        is_active=True
    )
    
    # Crear método Email
    MFAMethod.objects.create(
        name='email',
        is_active=True
    )

def remove_initial_mfa_methods(apps, schema_editor):
    MFAMethod = apps.get_model('accounts', 'MFAMethod')
    MFAMethod.objects.filter(name__in=['otp', 'email']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_mfamethod_customuser_has_mfa_mfaverification_usermfa'),
    ]

    operations = [
        migrations.RunPython(
            insert_initial_mfa_methods,
            remove_initial_mfa_methods
        )
    ]