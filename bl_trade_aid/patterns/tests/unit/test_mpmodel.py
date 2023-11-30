from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from unittest import mock
from ...utils import ProfileChartUtils
from ...utils import HourLetterMapper
from ...models import ProfileChart
from ...models import Batch
from ...models import BarData
from ...models import Experiment
from ...models import Rule
from ...models import ProcessedContract
from ...models import Alert

import logging
import pandas as pd
import decimal

logger = logging.getLogger(__name__)


class ProfileChartModelTest(TestCase):

    def test_chart_file_upload(self):
        # Creating a dummy batch for the ForeignKey
        experiment = Experiment.objects.create(name="experiment")
        batch = Batch.objects.create(experiment=experiment)  # Add required fields here

        # Creating a dummy uploaded file
        content = b"dummy_file_content"
        chart_file = SimpleUploadedFile("test_chart.txt", content)

        # Creating the ProfileChart instance
        profile_chart = ProfileChart.objects.create(
            batch=batch,
            symbol="TEST",
            chart_file=chart_file
            )

        # Check that the file has been saved correctly
        self.assertTrue(profile_chart.chart_file)

        # You can also test the file's content if necessary
        saved_file = profile_chart.chart_file.read()
        self.assertEqual(saved_file, content)

        # Cleanup (Deleting the test file after the test)
        profile_chart.chart_file.delete()


class MarketProfileOOModelTestCase(TestCase):
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

        call_command('loaddata', 'bardata_fixture', verbosity=0)

        experiment_rule = Rule.objects.create(days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment.rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()
        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)

        self.assertEquals(14, len(pc.periods('MSFT')))
        # test the profile chart one day column is created
        day_tpo = pc.get_day_tpos('2023-03-13', 'MSFT')
        self.assertEquals(day_tpo[76], 'yzABCDEHIJK')

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_get_control_value_for_contracts(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar
            ):

        call_command('loaddata', 'bardata_fixture', verbosity=0)

        experiment_rule = Rule.objects.create(days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment.rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()

        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)

        # test the profile chart one day column is created
        prices_dict = {
            70: 'y', 71: 'y', 72: 'y', 73: 'y', 74: 'yzABCEFG', 75: 'yzABCDEFGHJK', 76: 'yzABCDEHIJK',
            77: 'yIJK', 78: 'yK', 79: 'yK', 80: '', 81: '', 82: '', 83: '', 84: '', 85: '', 86: '',
            87: '', 88: '', 89: '', 90: '', 91: '', 92: '', 93: '', 94: '', 95: '', 96: '', 97: '',
            98: '', 99: '', 100: '', 101: '', 102: '', 103: '', 104: '', 105: '', 106: '', 107: '',
            108: '', 109: '', 110: '', 111: ''}
        charts = {}
        charts['ProfileChart'] = prices_dict
        date = pd.Timestamp('2023-03-13 00:00:00')
        point_of_control = pc.get_control_point(date, charts)
        self.assertEquals(75, point_of_control)

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_call_bar_data_and_insert_symbol(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar
            ):

        call_command('loaddata', 'bardata_fixture', verbosity=0)

        experiment_rule = Rule.objects.create(days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment.rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()

        ProfileChartUtils.create_profile_chart_wrapper(batch)
        symbols = BarData.objects.filter(batch=batch).distinct('symbol')

        self.assertEquals(2, len(symbols))
        self.assertEquals('AAPL', symbols[0].symbol)
        self.assertEquals('MSFT', symbols[1].symbol)

    def test_get_period_letters(
            self,
            ):
        mapper = HourLetterMapper()

        self.assertEquals('x', mapper.get_letter('08:00'))
        self.assertEquals('F', mapper.get_letter('12:00'))
        self.assertEquals('M', mapper.get_letter('15:30'))
        self.assertEquals('R', mapper.get_letter('19:30'))
        self.assertEquals('w', mapper.get_letter('07:30'))

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_mp_one_day(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar
            ):

        call_command('loaddata', 'bardata_fixture', verbosity=0)

        experiment_rule = Rule.objects.create(days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment.rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()

        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)
        pc.generate_profile_charts()
        # create mocks
        # load profile chart  with pickle
        # call the service that will create the column for the prices and one for day

        # icompare with the text that is supposed to have the mpc
        filename = f'{settings.APPS_DIR}/patterns/tests/fixtures/profile_chart_output1.txt'
        with open(filename, 'r') as f:
            content = f.read()

        qs = ProfileChart.objects.all()
        profile_chart = qs[0]
        saved_file = profile_chart.chart_file.read()
        self.assertEquals(bytes(content, 'utf-8'), saved_file)

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.connect')
    def test_mp_more_than_one_symbol(
            self,
            mock_connect,
            mock_disconnect_bar
            ):

        call_command('loaddata', 'bardata_fixture_2', verbosity=0)
        batch = Batch.objects.all()[0]
        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)
        pc.generate_profile_charts()
        # create mocks
        # load profile chart  with pickle
        # call the service that will create the column for the prices and one for day

        # icompare with the text that is supposed to have the mpc
        filename1 = f'{settings.APPS_DIR}/patterns/tests/fixtures/profile_chart_output1.txt'
        with open(filename1, 'r') as f:
            content1 = f.read()

        filename2 = f'{settings.APPS_DIR}/patterns/tests/fixtures/profile_chart_output2.txt'
        with open(filename2, 'r') as f:
            content2 = f.read()

        qs = ProfileChart.objects.all()
        profile_chart1 = qs[0]
        profile_chart2 = qs[1]
        saved_file1 = profile_chart1.chart_file.read()
        saved_file2 = profile_chart2.chart_file.read()

        self.assertEquals(bytes(content1, 'utf-8'), saved_file1)
        self.assertEquals(bytes(content2, 'utf-8'), saved_file2)


class AlertModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.experiment = Experiment.objects.create(name="experiment")
        cls.batch = Batch.objects.create(experiment=cls.experiment)  # Add required fields here
        cls.processed_contract = ProcessedContract.objects.create(
                symbol='MSFT',
                batch=cls.batch,
                positive_outcome=True,
                )  # Add required fields here

    def test_str_representation(self):
        alert = Alert(
                processed_contract=self.processed_contract,
                alert_price=decimal.Decimal('1234.5678'),
                operator='GT')
        alert.save()

        # You might need to adjust the expected string based on the exact requirements
        expected_string = (f'Alert: {alert.operator}:{alert.alert_price} '
                           f'[{timezone.localtime(alert.created).strftime("%Y-%m-%d %H:%M:%S")}]')

        self.assertEqual(str(alert), expected_string)

    # Optional: Test field definitions
    def test_field_definitions(self):
        alert = Alert(
                processed_contract=self.processed_contract,
                alert_price=decimal.Decimal('1234.5678'),
                operator='GT')
        alert.save()
        self.assertIsInstance(alert.alert_price, decimal.Decimal)
        self.assertIsInstance(alert.operator, str)
