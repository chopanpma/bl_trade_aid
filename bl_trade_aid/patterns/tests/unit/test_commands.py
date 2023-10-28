import logging
from unittest.mock import Mock
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings, tag


logger = logging.getLogger(__name__)


class GenerateCurrentProfileChartsCommandTestCase(TransactionTestCase):

    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_current_profile_charts')
    def test_generate_current_profile_charts(self, mock_get_current_profile_charts):
        # TODO: save profiles in a day/version folder.
        # assert the count
        # done

        call_command('generate_current_profile_charts')
        self.assertEqual(1, mock_get_current_profile_charts.call_count)
