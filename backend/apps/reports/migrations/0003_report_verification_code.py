import secrets

from django.db import migrations, models

import apps.reports.models


def backfill_codes(apps, schema_editor):
    Report = apps.get_model('reports', 'Report')
    for report in Report.objects.filter(verification_code__isnull=True):
        report.verification_code = secrets.token_hex(8)
        report.save(update_fields=['verification_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='verification_code',
            field=models.CharField(max_length=32, null=True, editable=False),
        ),
        migrations.RunPython(backfill_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='report',
            name='verification_code',
            field=models.CharField(
                default=apps.reports.models._make_verification_code,
                editable=False, max_length=32, unique=True,
            ),
        ),
    ]
