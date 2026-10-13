from django.db import migrations

def activate_companies(apps, schema_editor):
    Company = apps.get_model('companies', 'Company')
    Company.objects.filter(is_deleted=False).update(is_active=True)

class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_company_attendance_qr_token'),
    ]

    operations = [
        migrations.RunPython(activate_companies, reverse_code=migrations.RunPython.noop),
    ]
