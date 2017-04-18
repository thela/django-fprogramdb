# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-04-18 08:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Call',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fp', models.CharField(choices=[('FP6', 'FP6'), ('FP7', 'FP7'), ('H2020', 'H2020')], default='H2020', max_length=2)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('fundingScheme', models.CharField(blank=True, max_length=200, null=True)),
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
            ],
        ),
        migrations.CreateModel(
            name='PartnerProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coordinator', models.BooleanField()),
                ('ecContribution', models.DecimalField(decimal_places=2, max_digits=13)),
                ('partner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fprogramdb.Partner')),
            ],
        ),
        migrations.CreateModel(
            name='Programme',
            fields=[
                ('fp', models.CharField(choices=[('FP6', 'FP6'), ('FP7', 'FP7'), ('H2020', 'H2020')], default='H2020', max_length=2)),
                ('rcn', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=20)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('shortTitle', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('fp', models.CharField(choices=[('FP6', 'FP6'), ('FP7', 'FP7'), ('H2020', 'H2020')], default='H2020', max_length=5)),
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
                ('fp', models.CharField(choices=[('FP6', 'FP6'), ('FP7', 'FP7'), ('H2020', 'H2020')], default='H2020', max_length=5)),
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
