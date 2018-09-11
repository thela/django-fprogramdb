# Generated by Django 2.0.4 on 2018-09-05 14:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fprogramdb', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='call',
            name='source',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.PROTECT, to='fprogramdb.EuodpData'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='fpdata',
            name='organizations',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organizations', to='fprogramdb.EuodpData'),
        ),
        migrations.AlterField(
            model_name='fpdata',
            name='programmes',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='programmes', to='fprogramdb.EuodpData'),
        ),
        migrations.AlterField(
            model_name='fpdata',
            name='projects',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projects', to='fprogramdb.EuodpData'),
        ),
        migrations.AlterField(
            model_name='fpdata',
            name='topics',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='topics', to='fprogramdb.EuodpData'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='source',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.PROTECT, to='fprogramdb.EuodpData'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='partnerproject',
            name='original_partner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='original_partner', to='fprogramdb.Partner'),
        ),
        migrations.AlterField(
            model_name='partnerproject',
            name='partner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='fprogramdb.Partner'),
        ),
        migrations.AlterField(
            model_name='partnerproject',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='fprogramdb.Project'),
        ),
        migrations.AlterField(
            model_name='programme',
            name='source',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.PROTECT, to='fprogramdb.EuodpData'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='project',
            name='call',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='fprogramdb.Call'),
        ),
        migrations.AlterField(
            model_name='project',
            name='source',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.PROTECT, to='fprogramdb.EuodpData'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='project',
            name='topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='fprogramdb.Topic'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='legalBasisCode',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='topic',
            name='legalBasisRcn',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='topic',
            name='source',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.PROTECT, to='fprogramdb.EuodpData'),
            preserve_default=False,
        ),
    ]
