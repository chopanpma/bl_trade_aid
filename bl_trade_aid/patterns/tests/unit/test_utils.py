from django.test import TestCase
from ...utils import ProfileChartUtils
import decimal

import logging

logger = logging.getLogger(__name__)


class PeriodPlottingTest(TestCase):

    def test_plot_tpo(self):
        # create the expected
        original_dict = {}
        expected_dict = {
                51: '', 52: '', 53: '', 54: '', 55: '', 56: '', 57: '', 58: '', 59: '', 60: '',
                61: '', 62: '', 63: '', 64: '', 65: '', 66: '', 67: '', 68: '', 69: '', 70: '',
                71: '', 72: '', 73: '', 74: '', 75: '', 76: '', 77: '', 78: '', 79: '', 80: '',
                81: '', 82: '', 83: '', 84: '', 85: '', 86: '', 87: '', 88: '', 89: '', 90: '',
                91: 'A', 92: 'A', 93: 'A', 94: 'A', 95: 'A', 96: 'A', 97: 'A', 98: 'A', 99: 'A',
                100: 'A', 101: 'A', 102: 'A', 103: 'A', 104: 'A', 105: '', 106: '', 107: '', 108: '',
                109: '', 110: '', 111: '', 112: '', 113: '', 114: '', 115: '', 116: '', 117: '', 118:
                '', 119: ''}

        total_min_price = int(decimal.Decimal('51.00'))
        total_max_price = int(decimal.Decimal('120.00'))

        for price in range(total_min_price, total_max_price):
            original_dict[price] = ('')

        min_price = int(decimal.Decimal('91.00'))
        max_price = int(decimal.Decimal('104.00'))

        # call the service
        result_dict = ProfileChartUtils.plot_tpo(original_dict, min_price, max_price, 'A')

        # assert
        self.assertEqual(expected_dict, result_dict)

    def test_plot_tpo_two_periods(self):
        # create the expected
        original_dict = {}
        expected_dict = {
                51: '', 52: '', 53: '', 54: '', 55: '', 56: '', 57: '', 58: '', 59: '', 60: '',
                61: '', 62: '', 63: '', 64: '', 65: '', 66: '', 67: '', 68: '', 69: '', 70: '',
                71: '', 72: '', 73: '', 74: '', 75: '', 76: '', 77: '', 78: '', 79: '', 80: '',
                81: '', 82: '', 83: '', 84: '', 85: '', 86: '', 87: '', 88: '', 89: '', 90: '',
                91: 'AB', 92: 'AB', 93: 'AB', 94: 'AB', 95: 'AB', 96: 'AB', 97: 'AB', 98: 'AB', 99: 'AB',
                100: 'AB', 101: 'A', 102: 'A', 103: 'A', 104: 'A', 105: '', 106: '', 107: '', 108: '',
                109: '', 110: '', 111: '', 112: '', 113: '', 114: '', 115: '', 116: '', 117: '', 118:
                '', 119: ''}

        total_min_price = int(decimal.Decimal('51.00'))
        total_max_price = int(decimal.Decimal('120.00'))

        for price in range(total_min_price, total_max_price):
            original_dict[price] = ('')

        min_price = int(decimal.Decimal('91.00'))
        max_price = int(decimal.Decimal('104.00'))

        # call the service
        result_dict = ProfileChartUtils.plot_tpo(original_dict, min_price, max_price, 'A')

        # second scenario
        min_price = int(decimal.Decimal('91.00'))
        max_price = int(decimal.Decimal('100.00'))

        result_dict = ProfileChartUtils.plot_tpo(result_dict, min_price, max_price, 'B')

        # assert
        self.assertEqual(expected_dict, result_dict)
