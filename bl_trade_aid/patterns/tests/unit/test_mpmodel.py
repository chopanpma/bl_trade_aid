from django.test import TestCase
from django.conf import settings
from unittest.mock import patch
from unittest import mock
from django.core.management import call_command
from ...utils import ProfileChartUtils
from ...utils import HourLetterMapper
from django.core.files.uploadedfile import SimpleUploadedFile
from ...models import ProfileChart, Batch

import logging

logger = logging.getLogger(__name__)


class ProfileChartModelTest(TestCase):

    def test_chart_file_upload(self):
        # Creating a dummy batch for the ForeignKey
        batch = Batch.objects.create(experiment=1)  # Add required fields here

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

        batch = Batch.objects.all()[0]
        pc = ProfileChartUtils.create_profile_chart(batch)

        self.assertEquals(14, len(pc.periods('MSFT')))
        # test the profile chart one day column is created
        day_tpo = pc.get_day_tpos('2023-03-13')
        self.assertEquals(day_tpo[76], 'JMOPQ')

    def test_get_period_letters(
            self,
            ):
        mapper = HourLetterMapper()

        self.assertEquals('A', mapper.get_letter('08:00'))
        self.assertEquals('I', mapper.get_letter('12:00'))
        self.assertEquals('o', mapper.get_letter('15:30'))
        self.assertEquals('U', mapper.get_letter('19:30'))
        self.assertEquals('$', mapper.get_letter('07:30'))

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
        batch = Batch.objects.all()[0]
        pc = ProfileChartUtils.create_profile_chart(batch)
        # create mocks
        # load profile chart  with pickle
        # call the service that will create the column for the prices and one for day

        # icompare with the text that is supposed to have the mpc
        logger.debug(pc.get_profile_chart_data_frame_string())
        filename = f'{settings.APPS_DIR}/patterns/tests/fixtures/profile_chart_output.txt'
        with open(filename, 'r') as f:
            content = f.read()

        self.assertEquals(content, pc.get_profile_chart_data_frame_string())
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
        pc = ProfileChartUtils.create_profile_chart(batch)
        # create mocks
        # load profile chart  with pickle
        # call the service that will create the column for the prices and one for day

        # icompare with the text that is supposed to have the mpc
        logger.debug(pc.get_profile_chart_data_frame_string())
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
