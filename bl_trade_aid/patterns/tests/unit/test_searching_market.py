from django.test import TestCase
from unittest.mock import patch
from unittest import mock
from django.conf import settings
from django.core.management import call_command
from ...utils import MarketUtils
from ...models import ScanData
from ...models import BarData
from ...models import Batch
from ...models import ProcessedContract
from ...models import ExcludedContract
from ...models import Experiment
from ...models import RuleExperiment
from ...models import QueryParameter
from ...models import Rule
from ib_insync import ScannerSubscription
from ib_insync import TagValue
import pickle
import logging
logger = logging.getLogger(__name__)


class ScannerSubscriptionTestCase(TestCase):
    fixtures = ['batch.json']

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

        rule = Rule.objects.create(days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment_rule = RuleExperiment.objects.create(experiment=experiment, rule=rule)
        experiment.experiment_rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()

        MarketUtils.get_bars_in_date_range('AMV', 'SMART', batch)

        # - assert the function calls the mock

        # call_command('dumpdata',  indent=4, output='bardata_fixture.json')
        batch = BarData.objects.all()[0].batch

        self.assertEquals(172, len(BarData.objects.all()))
        self.assertEquals(172, len(BarData.objects.filter(batch=batch)))

        print(f'call args list:  {mock_disconnect_bar.call_args_list}')
        self.assertEquals(1, mock_connect.call_count)
        self.assertEquals(1, mock_req_historical_data.call_count)
        # self.assertEquals(1, mock_disconnect_bar.call_count)
        # TODO: fix the test problem calling the disconnect mock

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

        rule = Rule.objects.create(days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment_rule = RuleExperiment.objects.create(experiment=experiment, rule=rule)
        experiment.experiment_rules.add(experiment_rule)

        batch = MarketUtils.get_contracts(experiment)

        self.assertEquals(50, len(ScanData.objects.filter(batch=batch)))
        # call_command('dumpdata',  indent=4, output='scandata_fixture.json')

        print(f'call args list:  {mock_disconnect_scan.call_args_list}')
        print(f'calls:  {mock_disconnect_scan.calls}')
        self.assertEquals(1, mock_connect.call_count)
        self.assertEquals(1, mock_reqscannerdata.call_count)
        # TODO: why is it called twice
        # self.assertEquals(1, mock_disconnect_scan.call_count)

        how_many_of_them_are_in_the_batch = ScanData.objects.filter(batch=batch)
        self.assertEquals(50, how_many_of_them_are_in_the_batch.count())

    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_bars_in_date_range')
    def test_insert_loop_over_ScanData_entries(
            self,
            mock_get_bars,
            ):

        call_command('loaddata', 'scandata_fixture', verbosity=0)

        # For this query we are not filterig by batch since it is not what is tested
        # and the mocked data does not contain batch
        scan_data_list = ScanData.objects.all()

        batch = Batch.objects.all()[0]
        MarketUtils.get_bars_from_scandata(scan_data_list, batch)

        # - assert the function calls the mock
        self.assertEquals(50, mock_get_bars.call_count)

    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_contracts')
    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_bars_from_scandata')
    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_bars_in_date_range')
    @patch('bl_trade_aid.patterns.utils.ProfileChartWrapper.generate_profile_charts')
    def test_scan_and_create_profiles(
            self,
            mock_generate_profile_charts,
            mock_get_bars_in_date_range,
            mock_get_bars_from_scandata,
            mock_get_contracts,
            ):
        mock_get_contracts.return_value = Batch.objects.all()[0]

        call_command('loaddata', 'scandata_fixture', verbosity=0)

        experiment = Experiment.objects.all()[0]
        MarketUtils.get_current_profile_charts(profile_chart_generation_limit=30, experiment=experiment)

        self.assertEquals(1, mock_get_contracts.call_count)
        self.assertEquals(1, mock_get_bars_from_scandata.call_count)
        self.assertEquals(1, mock_generate_profile_charts.call_count)
        # assert that the file has been created

    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_contracts')
    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_bars_in_date_range')
    def test_insert_loop_over_ScanData_entries_only_if_they_have_not_being_evaluated(
            self,
            mock_get_bars_in_date_range,
            mock_get_contracts,
            ):
        mock_get_contracts.return_value = Batch.objects.all()[0]
        experiment = Experiment.objects.all()[0]

        call_command('loaddata', 'contract_fixture2', verbosity=0)
        call_command('loaddata', 'contract_details_fixture', verbosity=0)
        call_command('loaddata', 'scandata_fixture_2', verbosity=0)
        call_command('loaddata', 'bardata_fixture_2', verbosity=0)

        MarketUtils.get_current_profile_charts(profile_chart_generation_limit=50, experiment=experiment)

        self.assertEquals(2, mock_get_bars_in_date_range.call_count)

        mock_get_bars_in_date_range.reset_mock()
        MarketUtils.get_current_profile_charts(profile_chart_generation_limit=50, experiment=experiment)

        self.assertEquals(0, mock_get_bars_in_date_range.call_count)

    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_contracts')
    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_bars_in_date_range')
    def test_exclusion_list(
            self,
            mock_get_bars_in_date_range,
            mock_get_contracts,
            ):
        rule = Rule.objects.create(days_offset=2)
        experiment = Experiment.objects.all()[0]
        experiment_rule = RuleExperiment.objects.create(experiment=experiment, rule=rule)
        experiment.experiment_rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()
        mock_get_contracts.return_value = batch

        call_command('loaddata', 'contract_fixture2', verbosity=0)
        call_command('loaddata', 'contract_details_fixture', verbosity=0)
        call_command('loaddata', 'scandata_fixture_2', verbosity=0)
        call_command('loaddata', 'bardata_fixture_2', verbosity=0)

        ExcludedContract.objects.create(symbol='MSFT', exclude_active=True)
        MarketUtils.get_current_profile_charts(profile_chart_generation_limit=50, experiment=experiment)

        self.assertEquals(1, mock_get_bars_in_date_range.call_count)
        self.assertEquals(1, ProcessedContract.objects.filter(batch=batch).count())

        # assert that the file has been created

    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_contracts')
    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_bars_in_date_range')
    def test_exclusion_list_if_element_is_not_in_list(
            self,
            mock_get_bars_in_date_range,
            mock_get_contracts,
            ):
        batch = Batch.objects.all()[0]
        mock_get_contracts.return_value = batch

        call_command('loaddata', 'contract_fixture2', verbosity=0)
        call_command('loaddata', 'contract_details_fixture', verbosity=0)
        call_command('loaddata', 'scandata_fixture_2', verbosity=0)
        call_command('loaddata', 'bardata_fixture_2', verbosity=0)

        ExcludedContract.objects.create(symbol='AMZN', exclude_active=True)

        MarketUtils.get_current_profile_charts(profile_chart_generation_limit=50, experiment=batch.experiment)

        self.assertEquals(2, mock_get_bars_in_date_range.call_count)
        self.assertEquals(2, ProcessedContract.objects.filter(batch=batch).count())

        # assert that the file has been created

    @patch('bl_trade_aid.patterns.utils.MarketUtils.create_parameters')
    @patch('bl_trade_aid.patterns.utils.MarketUtils.create_scanner')
    @patch('ib_insync.IB.reqScannerData')
    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.connect')
    def test_get_contract_calls_create_scanner_and_create_parameters(
            self,
            mock_connect,
            mock_disconnect_scan,
            mock_reqscannerdata,
            mock_create_scanner,
            mock_create_parameters):

        file = open(f'{settings.APPS_DIR}/patterns/tests/fixtures/scan_results.pickle', 'rb')
        data = pickle.load(file)
        file.close()
        mock_reqscannerdata.return_value = data

        rule = Rule.objects.create(days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment_rule = RuleExperiment.objects.create(experiment=experiment, rule=rule)
        experiment.experiment_rules.add(experiment_rule)

        # add scancodes
        experiment.instrument = 'STK'
        experiment.location_code = 'STK.US.MAJOR'
        experiment.scan_code = 'HOT_BY_VOLUME'

        # call_command('dumpdata',  indent=4, output='scandata_fixture.json')

        # add scancodes
        QueryParameter.objects.create(
                parameter_name='averageOptVolumeAbove',
                parameter_value='100',
                experiment=experiment)
        QueryParameter.objects.create(
                parameter_name='marketCapAbove',
                parameter_value='100000000',
                experiment=experiment)
        QueryParameter.objects.create(
                parameter_name='marketCapAbove',
                parameter_value='100000000',
                experiment=experiment)

        MarketUtils.get_contracts(experiment)

        self.assertEquals(1, mock_create_parameters.call_count)
        mock_create_parameters.assert_called_with(
            experiment,
            )

        self.assertEquals(1, mock_create_scanner.call_count)
        mock_create_scanner.assert_called_with(
            experiment,
            )

    def test_create_scanner_method(
            self,
            ):

        rule = Rule.objects.create(days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment_rule = RuleExperiment.objects.create(experiment=experiment, rule=rule)
        experiment.experiment_rules.add(experiment_rule)

        # add scancodes
        experiment.instrument = 'STK'
        experiment.location_code = 'STK.US.MAJOR'
        experiment.scan_code = 'HOT_BY_VOLUME'
        experiment.above_price = '0.10'
        experiment.below_price = '20'
        experiment.above_volume = '10000'
        experiment.market_cap_above = '10000000'
        experiment.market_cap_below = '200000000'
        actual = MarketUtils.create_scanner(experiment)
        expected = ScannerSubscription(
            numberOfRows=-1,
            instrument='STK',
            locationCode='STK.US.MAJOR',
            scanCode='HOT_BY_VOLUME',
            abovePrice='0.10',
            belowPrice='20',
            aboveVolume='10000',
            marketCapAbove='10000000',
            marketCapBelow='200000000',
            moodyRatingAbove='',
            moodyRatingBelow='',
            spRatingAbove='',
            spRatingBelow='',
            maturityDateAbove='',
            maturityDateBelow='',
            couponRateAbove=None,
            couponRateBelow=None,
            excludeConvertible=False,
            averageOptionVolumeAbove=None,
            scannerSettingPairs='',
            stockTypeFilter='')

        self.assertEquals(expected, actual)

    def test_create_parameters_method(
            self,
            ):
        experiment = Experiment.objects.all()[0]

        QueryParameter.objects.create(
                parameter_name='averageOptVolumeAbove',
                parameter_value='100',
                experiment=experiment)
        QueryParameter.objects.create(
                parameter_name='marketCapAbove',
                parameter_value='100000000',
                experiment=experiment)
        QueryParameter.objects.create(
                parameter_name='scannerSettingPairs',
                parameter_value='StockType=STOCK',
                experiment=experiment)

        expected = [TagValue('averageOptVolumeAbove', '100'),
                    TagValue('marketCapAbove', '100000000'),
                    TagValue('scannerSettingPairs', 'StockType=STOCK')]
        actual = MarketUtils.create_parameters(experiment)
        are_equal = sorted(actual) == sorted(expected)
        self.assertTrue(are_equal)
