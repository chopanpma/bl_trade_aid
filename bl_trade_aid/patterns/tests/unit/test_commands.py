import logging
from unittest.mock import Mock
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings, tag


logger = logging.getLogger(__name__)


# class CreateInterbankFileCommandTestCase(TransactionTestCase):
#     def setUp(self):
#         self.file = '{}/mpconnector/tests/fixtures/ActivePayments_201807251055.csv'.format(settings.APPS_DIR)
# 
#     @patch('pandas.read_csv')
#     @patch('patterns.')
#     def test_create_profile_charts(self, generate_interbank_file_mock, read_csv_mock):
#         pass
#         # mock the calls to methods
#         # get_contracts
#         # get_bars_from_scandata 
#         # create_profile_charts
#         # save profiles in a day/version folder.
#         # assert the count
#         # done
# 
#         call_command('generate_profile_charts')
#         self.assertEqual(1, generate_interbank_file_mock.call_count)
#         self.assertTrue(os.path.exists(file_path))
