from django.core.management.base import BaseCommand
from ...utils import MarketUtils
from ...models import Experiment

import warnings
import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')


class Command(BaseCommand):
    help = 'Print available scanner parameters' 


    def handle(self, *args, **options):
        # command

        MarketUtils.get_scanner_parameters()
