from django.core.management.base import BaseCommand
from ...utils import MarketUtils
import warnings

import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')


class Command(BaseCommand):
    help = 'Start market profile server'

    def handle(self, *args, **options):
        # command
        MarketUtils.get_contracts()
