from django.test import TestCase
from unittest.mock import patch
from unittest import mock
from django.core.management import call_command
from ...utils import ProfileChartUtils
from ...utils import HourLetterMapper
import logging
logger = logging.getLogger(__name__)


class MarketProfileOOModelTestCase(TestCase):

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_call_bar_data_for_list_of_contracts(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar
            ):

        call_command('loaddata', 'bardata_fixture', verbosity=0)

        batch = 1
        pf = ProfileChartUtils.create_profile_chart(batch)

        self.assertEquals(14, len(pf.periods()))

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_get_period_letters(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar
            ):
        mapper = HourLetterMapper()

        self.assertEquals('A', mapper.get_letter('08:00'))
        self.assertEquals('I', mapper.get_letter('12:00'))
        self.assertEquals('P', mapper.get_letter('15:30'))
        self.assertEquals('X', mapper.get_letter('19:30'))
        self.assertEquals('X', mapper.get_letter('07:30'))
