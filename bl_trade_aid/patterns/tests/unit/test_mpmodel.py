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
        batch = Batch.objects.create(...)  # Add required fields here

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
        pc = ProfileChartUtils.create_profile_chart(batch)

        self.assertEquals(14, len(pc.periods()))
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
        batch = 1
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
