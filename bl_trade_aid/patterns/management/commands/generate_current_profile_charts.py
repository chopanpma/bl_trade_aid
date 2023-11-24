from django.core.management.base import BaseCommand
from ...utils import MarketUtils
from ...models import Experiment

import warnings
import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')


class Command(BaseCommand):
    help = 'Call trades of the day with parameters, and call market profile for them'

    def add_arguments(self, parser):
        parser.add_argument('--profile-chart-generation-limit', '-l',  help='Limit for profile generation')
        parser.add_argument('--symbol', '-s',  help='Call profile for a single symbol')
        parser.add_argument('--experiment', '-e',  help='Name of the experiment')

    def handle(self, *args, **options):
        # command
        profile_chart_generation_limit_param = options['profile_chart_generation_limit']
        symbol = options['symbol']
        experiment_name = options['experiment']

        if experiment_name is not None:
            qs = Experiment.objects.filter(name=experiment_name)
            experiment = qs[0]
            if symbol is not None:
                MarketUtils.get_single_profile_chart(symbol, experiment)
                return

            if profile_chart_generation_limit_param is None:
                profile_chart_generation_limit_param = '50'

            profile_chart_generation_limit = int(profile_chart_generation_limit_param)

            MarketUtils.get_current_profile_charts(profile_chart_generation_limit, experiment)
        else:
            print('No eperiment')
