from django.test import TestCase
from django.core.management import call_command
from unittest.mock import patch
from unittest import mock
from ...utils import ProfileChartUtils
from ...models import Batch
from ...models import Experiment
from ...models import RuleExperiment
from ...models import Rule

import logging
import pandas as pd

logger = logging.getLogger(__name__)


class RulesTestCase(TestCase):
    fixtures = ['batch.json']

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_get_accepted_band_for_all_except_last_two_days_max_band(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar
            ):

        call_command('loaddata', 'bardata_IBD', verbosity=0)

        batch = Batch.objects.all()[0]
        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)
        pc.set_participant_symbols()

        ps = batch.processed_contracts.filter(positive_outcome=True)
        self.assertEquals(8, len(ps))

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_wide_accepted_band(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar
            ):
        call_command('loaddata', 'bardata_IBD', verbosity=0)

        rule = Rule.objects.create(control_point_band_ticks=30)
        experiment = Experiment.objects.all()[0]
        experiment_rule = RuleExperiment.objects.create(experiment=experiment, rule=rule)
        experiment.experiment_rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()

        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)
        pc.set_participant_symbols()

        ps = batch.processed_contracts.filter(positive_outcome=True)
        self.assertEquals(2, len(ps))

#     @patch('bl_trade_aid.patterns.utils.ProfileChartWrapper.days_offset',
#            new_callable=mock.PropertyMock)
#     @patch('bl_trade_aid.patterns.utils.ProfileChartWrapper.ticks_offset',
#            new_callable=mock.PropertyMock)
    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_ticks_offset(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar,
            ):
        call_command('loaddata', 'bardata_IBD', verbosity=0)

        rule = Rule.objects.create(
                ticks_offset=20,
                days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment_rule = RuleExperiment.objects.create(experiment=experiment, rule=rule)
        experiment.experiment_rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()

        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)
#         mock_days_offset.return_value = 1
#         mock_ticks_offset.return_value = 30

        control_points = {
                pd.Timestamp('2023-02-23 00:00:00'): 110,
                pd.Timestamp('2023-02-24 00:00:00'): 115,
                pd.Timestamp('2023-02-26 00:00:00'): 150,
                pd.Timestamp('2023-02-27 00:00:00'): 130,
                pd.Timestamp('2023-02-28 00:00:00'): 120,
                pd.Timestamp('2023-03-01 00:00:00'): 110,
                pd.Timestamp('2023-03-02 00:00:00'): 180,
                }

        max_point_of_control = 150
        min_point_of_control = 110
        result = pc.check_symbol_positive_experiment(
                control_points,
                max_point_of_control,
                min_point_of_control,
                )

        self.assertTrue(result)

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_days_returned_happy_path(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar,
            ):
        call_command('loaddata', 'bardata_IBD', verbosity=0)

        rule = Rule.objects.create(
                days_returned=7,
                days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment_rule = RuleExperiment.objects.create(experiment=experiment, rule=rule)
        experiment.experiment_rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()

        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)

        control_points = {
                pd.Timestamp('2023-02-23 00:00:00'): 110,
                pd.Timestamp('2023-02-24 00:00:00'): 115,
                pd.Timestamp('2023-02-26 00:00:00'): 150,
                pd.Timestamp('2023-02-27 00:00:00'): 130,
                pd.Timestamp('2023-02-28 00:00:00'): 120,
                pd.Timestamp('2023-03-01 00:00:00'): 110,
                pd.Timestamp('2023-03-02 00:00:00'): 180,
                }

        max_point_of_control = 150
        min_point_of_control = 110
        result = pc.check_symbol_positive_experiment(
                control_points,
                max_point_of_control,
                min_point_of_control,
                )

        self.assertTrue(result)

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_days_returned_short(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar,
            ):
        call_command('loaddata', 'bardata_IBD', verbosity=0)

        rule = Rule.objects.create(
                days_returned=7,
                days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment_rule = RuleExperiment.objects.create(experiment=experiment, rule=rule)
        experiment.experiment_rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()

        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)

        control_points = {
                pd.Timestamp('2023-02-23 00:00:00'): 110,
                pd.Timestamp('2023-02-24 00:00:00'): 115,
                pd.Timestamp('2023-02-26 00:00:00'): 150,
                pd.Timestamp('2023-02-27 00:00:00'): 130,
                pd.Timestamp('2023-03-01 00:00:00'): 110,
                pd.Timestamp('2023-03-02 00:00:00'): 180,
                }

        max_point_of_control = 150
        min_point_of_control = 110
        result = pc.check_symbol_positive_experiment(
                control_points,
                max_point_of_control,
                min_point_of_control,
                )

        self.assertFalse(result)

    @patch('ib_insync.IB.disconnect',  new_callable=mock.Mock)
    @patch('ib_insync.IB.reqHistoricalData')
    @patch('ib_insync.IB.connect')
    def test_days_offset(
            self,
            mock_connect,
            mock_req_historical_data,
            mock_disconnect_bar
            ):
        # TODO: types of rules
        # 1. filter symbols from being plotted
        # 2. filter scan rules
        # 3. criteria to find a positive chart.

        call_command('loaddata', 'bardata_IBD', verbosity=0)

        rule = Rule.objects.create(days_offset=1)
        experiment = Experiment.objects.all()[0]
        experiment_rule = RuleExperiment.objects.create(experiment=experiment, rule=rule)
        experiment.experiment_rules.add(experiment_rule)

        batch = Batch.objects.all()[0]
        batch.experiment = experiment
        batch.save()
        pc = ProfileChartUtils.create_profile_chart_wrapper(batch)
        pc.set_participant_symbols()

        ps = batch.processed_contracts.filter(positive_outcome=True)
        self.assertEquals(12, len(ps))
