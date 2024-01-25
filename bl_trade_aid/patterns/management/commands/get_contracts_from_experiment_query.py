from django.core.management.base import BaseCommand
from ...utils import MarketUtils
from ...models import Experiment

import warnings
import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')


class Command(BaseCommand):
    help = 'Get contracts using experiment query but not getting bardata'

    def add_arguments(self, parser):
        parser.add_argument('--experiment', '-e',  help='Name of the experiment')

    def handle(self, *args, **options):
        # command
        experiment_name = options['experiment']
        if experiment_name is not None:
            qs = Experiment.objects.filter(name=experiment_name)
            experiment = qs[0]

            MarketUtils.get_contracts(experiment)
        else:
            print('No experiment')
