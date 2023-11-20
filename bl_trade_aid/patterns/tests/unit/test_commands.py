import logging
from unittest.mock import Mock
from unittest.mock import patch
from ...models import Batch
from ...models import Experiment
from ...models import Rule
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings, tag


logger = logging.getLogger(__name__)


class GenerateCurrentProfileChartsCommandTestCase(TransactionTestCase):
    fixtures = ['batch.json']

    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_current_profile_charts')
    def test_generate_current_profile_charts(self, mock_get_current_profile_charts):
        # TODO: save profiles in a day/version folder.
        # assert the count
        # done

        call_command('generate_current_profile_charts')
        self.assertEqual(1, mock_get_current_profile_charts.call_count)

    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_contracts')
    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_bars_in_date_range')
    @patch('bl_trade_aid.patterns.utils.ProfileChartWrapper.generate_profile_charts')
    @patch('bl_trade_aid.patterns.utils.ProfileChartWrapper.set_participant_symbols')
    def test_generate_current_profile_chart_with_limits(
            self,
            mock_set_participant_symbols,
            mock_generate_profile_charts,
            mock_get_bars_in_date_range,
            mock_get_contracts,
            ):
        # TODO: save profiles in a day/version folder.
        # assert the count
        # done
        # Load Data
        call_command('loaddata', 'scandata_fixture', verbosity=0)
        mock_get_contracts.return_value = Batch.objects.all()[0]
        # Call command
        call_command('generate_current_profile_charts', profile_chart_generation_limit=20)
        self.assertEqual(20, mock_get_bars_in_date_range.call_count)
        self.assertEqual(1, mock_set_participant_symbols.call_count)

    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_contracts')
    @patch('bl_trade_aid.patterns.utils.MarketUtils.get_bars_in_date_range')
    @patch('bl_trade_aid.patterns.utils.ProfileChartWrapper.generate_profile_charts')
    def test_generate_current_profile_chart_one_symbol(
            self,
            mock_generate_profile_charts,
            mock_get_bars_in_date_range,
            mock_get_contracts,
            ):
        # TODO: save profiles in a day/version folder.
        # assert the count
        # done
        # Load Data
        call_command('loaddata', 'scandata_fixture', verbosity=0)

        experiment_rule = Rule.objects.create(days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment.rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()

        mock_get_contracts.return_value = batch
        # Call command
        call_command('generate_current_profile_charts', symbol='MSFT', experiment='Test_Experiment')
        self.assertEqual(1, mock_get_bars_in_date_range.call_count)
