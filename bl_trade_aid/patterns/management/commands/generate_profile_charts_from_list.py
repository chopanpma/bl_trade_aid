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
        parser.add_argument('--symbol', '-s',  nargs='+',  help='Call profile for a single symbol')
        parser.add_argument('--experiment', '-e',  nargs='+', help='Name of the experiment')

    def handle(self, *args, **options):
        # command
        symbols = options.get('symbol', [])
        experiment_names = options.get('experiment', [])
        for experiment_name in experiment_names:
            if experiment_name is not None:
                qs = Experiment.objects.filter(name=experiment_name)
                experiment = qs[0]
                MarketUtils.get_current_profile_charts_from_symbol_list(symbols, experiment)
                return
            else:
                print('No experiment')
