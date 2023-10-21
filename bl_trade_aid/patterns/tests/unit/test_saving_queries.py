from django.test import TestCase
from django.urls import reverse
from pandas import pandas as pd
from rest_framework.test import APIClient
from unittest.mock import patch
from django.conf import settings
from bl_trade_aid.users.models import User

import logging
logger = logging.getLogger(__name__)

#          png_filename = f'{settings.APPS_DIR}/api/tests/fixtures/kenobi.png'
#          with open(png_filename, 'rb') as jpeg:


class ReturningResultTestCase(TestCase):
    def setUp(self):

        self.client = APIClient()
        self.token = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJBZGVsYW50b3MiLCJpc3MiOiIwMDMwI'\
                     'iwiaWF0IjoxNjIzMjE0ODYwfQ.ozp4GIIzC2MpYdIqQ499O79tjLnCj-5NJMCbnFsp1kaFfGtOcTLLV'\
                     '1gbpsJCX9t61T4UnI-JxavNxO6wi4IL7w'
        # cls.user = UserFactory.create(password='password')

    def test_return_bars(self):
        # TODO: implement
        # - mock library call for the scan
        # - write the file
        # - create mock file
        # assert retur
        pass

    def test_store_scan(self):
        # TODO: implement
        # - mock library call for the scan
        # - add info to the table
        # - assert table values
        pass

    def test_query_is_under_a_experiment(self):
        pass

    def test_experiment_is_mapped_to_a_param_config(self):
        pass

    def test_param_config(self):
        pass

    def test_create_a_tpo_from_data(self):
        pass

    def test_create_a_market_profile_from_data(self):
        pass
