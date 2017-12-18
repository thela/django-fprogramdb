# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-18 13:21
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import re


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Call',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fp', models.CharField(choices=[('FP1', 'FP1'), ('FP2', 'FP2'), ('FP3', 'FP3'), ('FP4', 'FP4'), ('FP5', 'FP5'), ('FP6', 'FP6'), ('FP7', 'FP7'), ('H2020', 'H2020')], default='H2020', max_length=2)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('fundingScheme', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EuodpData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('euodp_url', models.URLField()),
                ('file_url', models.URLField()),
                ('update_date', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FpData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fp', models.CharField(choices=[('FP1', 'FP1'), ('FP2', 'FP2'), ('FP3', 'FP3'), ('FP4', 'FP4'), ('FP5', 'FP5'), ('FP6', 'FP6'), ('FP7', 'FP7'), ('H2020', 'H2020')], default='H2020', max_length=5)),
                ('organizations', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='organizations', to='fprogramdb.EuodpData')),
                ('programmes', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='programmes', to='fprogramdb.EuodpData')),
                ('projects', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='fprogramdb.EuodpData')),
                ('topics', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='fprogramdb.EuodpData')),
            ],
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pic', models.CharField(default='', max_length=20)),
                ('organizationActivityType', models.CharField(choices=[('PRC', 'Private for-profit entities (excluding Higher or Secondary Education Establishments)'), ('HES', 'Higher or Secondary Education Establishments'), ('REC', 'Research Organisations'), ('OTH', 'Other'), ('PUB', 'Public bodies (excluding Research Organisations and Secondary or Higher Education Establishments)')], max_length=3)),
                ('legalName', models.CharField(blank=True, max_length=1024, null=True)),
                ('shortName', models.CharField(blank=True, max_length=200, null=True)),
                ('street', models.CharField(blank=True, max_length=200, null=True)),
                ('city', models.CharField(blank=True, max_length=200, null=True)),
                ('country', models.CharField(blank=True, max_length=8, null=True)),
                ('postalCode', models.CharField(blank=True, max_length=8, null=True)),
                ('merged', models.BooleanField(default=False)),
                ('merged_ids', models.CharField(blank=True, max_length=200, null=True, validators=[django.core.validators.RegexValidator(re.compile('^\\d+(?:\\,\\d+)*\\Z'), code='invalid', message='Enter only digits separated by commas.')])),
                ('merged_with_id', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PartnerProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coordinator', models.BooleanField()),
                ('ecContribution', models.DecimalField(decimal_places=2, max_digits=13)),
                ('original_partner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='original_partner', to='fprogramdb.Partner')),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fprogramdb.Partner')),
            ],
        ),
        migrations.CreateModel(
            name='Programme',
            fields=[
                ('fp', models.CharField(choices=[('FP1', 'FP1'), ('FP2', 'FP2'), ('FP3', 'FP3'), ('FP4', 'FP4'), ('FP5', 'FP5'), ('FP6', 'FP6'), ('FP7', 'FP7'), ('H2020', 'H2020')], default='H2020', max_length=2)),
                ('rcn', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=20)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('shortTitle', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('fp', models.CharField(choices=[('FP1', 'FP1'), ('FP2', 'FP2'), ('FP3', 'FP3'), ('FP4', 'FP4'), ('FP5', 'FP5'), ('FP6', 'FP6'), ('FP7', 'FP7'), ('H2020', 'H2020')], default='H2020', max_length=5)),
                ('rcn', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('GA', models.CharField(max_length=20)),
                ('acronym', models.CharField(max_length=20)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('objective', models.CharField(blank=True, max_length=2048, null=True)),
                ('startDate', models.DateField(null=True, verbose_name='start date')),
                ('endDate', models.DateField(null=True, verbose_name='end_date')),
                ('totalCost', models.DecimalField(decimal_places=2, max_digits=13)),
                ('ecMaxContribution', models.DecimalField(decimal_places=2, max_digits=13)),
                ('duration', models.IntegerField(blank=True, null=True)),
                ('call', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fprogramdb.Call')),
                ('programme', models.ManyToManyField(to='fprogramdb.Programme')),
            ],
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fp', models.CharField(choices=[('FP1', 'FP1'), ('FP2', 'FP2'), ('FP3', 'FP3'), ('FP4', 'FP4'), ('FP5', 'FP5'), ('FP6', 'FP6'), ('FP7', 'FP7'), ('H2020', 'H2020')], default='H2020', max_length=5)),
                ('rcn', models.CharField(max_length=20)),
                ('code', models.CharField(max_length=20)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('legalBasisRcn', models.CharField(max_length=20)),
                ('legalBasisCode', models.CharField(max_length=20)),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='fprogramdb.Topic'),
        ),
        migrations.AddField(
            model_name='partnerproject',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fprogramdb.Project'),
        ),
    ]
