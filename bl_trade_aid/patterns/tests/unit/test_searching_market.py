from django.test import TestCase
from unittest.mock import patch
from unittest import mock
from django.conf import settings
from django.core.management import call_command
from ...utils import MarketUtils
from ...models import ScanData
from ...models import BarData
import pickle
import logging
logger = logging.getLogger(__name__)


class ScannerSubscriptionTestCase(TestCase):

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_call_bar_data_for_list_of_contracts(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar
            ):

        file = open(f'{settings.APPS_DIR}/patterns/tests/fixtures/bar_data_range_results.pickle', 'rb')
        data = pickle.load(file)
        file.close()
        mock_req_historical_data.return_value = data

        MarketUtils.get_bars_in_date_range('AMV', 'SMART')

        # - assert the function calls the mock

        self.assertEquals(172, len(BarData.objects.all()))

        self.assertEquals(1, mock_connect.call_count)
        self.assertEquals(1, mock_req_historical_data.call_count)
        self.assertEquals(1, mock_disconnect_bar.call_count)

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqScannerData')
    @patch('ib_insync.IB.connect')
    def test_call_req_Scanner_for_no_changed_contracts(
            self,
            mock_connect,
            mock_reqscannerdata,
            mock_disconnect_scan):
        file = open(f'{settings.APPS_DIR}/patterns/tests/fixtures/scan_results.pickle', 'rb')
        data = pickle.load(file)
        file.close()
        mock_reqscannerdata.return_value = data

        MarketUtils.get_contracts()
        self.assertEquals(50, len(ScanData.objects.all()))
        # call_command('dumpdata',  indent=4, output='scandata_fixture.json')

        print(f'call args list:  {mock_disconnect_scan.call_args_list}')
        print(f'calls:  {mock_disconnect_scan.calls}')
        self.assertEquals(1, mock_connect.call_count)
        self.assertEquals(1, mock_reqscannerdata.call_count)
        # TODO: why is it called twice
        self.assertEquals(2, mock_disconnect_scan.call_count)

    # TODO:
    # 1. create the fixture calling the command from the test DONE
    # 2. mock the call to the scan return data
    # 3. call the insert as many times as records are in scanData
    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_bars_in_date_range')
    def test_insert_loop_over_ScanData_entries(
            self,
            mock_get_bars,
            ):

        call_command('loaddata', 'scandata_fixture', verbosity=0)

        scan_data_list = ScanData.objects.all()

        MarketUtils.get_bars_from_scandata(scan_data_list)

        # - assert the function calls the mock
        self.assertEquals(50, mock_get_bars.call_count)
