# -*- coding: utf-8 -*-
from __future__ import print_function

import sys


from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from fprogramdb.models import FpData, sourceurls

try:
    from importlib import reload
except ImportError:
    pass
reload(sys)
try:
    sys.setdefaultencoding('utf-8')
except AttributeError:
    pass


class Command(BaseCommand):
    def read_fp(self, fp='H2020', cached=True, update_only=False):
        """
            read all info related to a fp and stores it into the db
            :param update_only:
            :param fp: framework string
            :param cached: use files already downloaded
        """

        fp_data_ob, fp_created = FpData.objects.get_or_create(fp=fp)
        if fp_created:
            fp_data_ob.generate_euodpdata()

        for attribute_label in ['programmes', 'topics', 'projects', 'organizations']:
            euodp_data = getattr(fp_data_ob, attribute_label)
            if euodp_data:
                with transaction.atomic():
                    euodp_data.update(attribute_label, fp)

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            "-fp", "--frameworkprogrammes", dest="fp", choices=[fp for fp in sourceurls],
            nargs='*', help="FPS to be processed", default=['H2020'])
        parser.add_argument(
            "--checkupdates", dest="update_only",
            help="only check updates on the db", default="False")
        parser.add_argument(
            "--cached", dest="cached",
            help="FPS to be processed", default="True")

    def handle(self, *args, **options):
        if 'fp' in options:
            if 'H2020' in options['fp']:
                self.read_fp('H2020', cached=options['cached'] != 'False', update_only=options['update_only'] == 'True')
                options['fp'].remove('H2020')
            else:
                print('You should load H2020 before other FP')

            for fp in options['fp']:
                self.read_fp(fp, cached=options['cached'] != 'False', update_only=options['update_only'] == 'True')
