from collections import defaultdict
from django.core.management.base import BaseCommand
from ...utils import MarketUtils
import warnings

from ib_insync import IB
from ib_insync import Stock
from ib_insync import util

import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')


class Command(BaseCommand):
    help = 'Call trades of the day with parameters, and call market profile for them'

    def add_arguments(self, parser):
        parser.add_argument('--profile-chart-generation-limit', '-l',  help='Limit for profile generation')
        parser.add_argument('--symbol', '-s',  help='Call profile for a single symbol')

    def handle(self, *args, **options):
        # command
        profile_chart_generation_limit_param = options['profile_chart_generation_limit']
        symbol = options['symbol']

        if symbol is not None:

            MarketUtils.get_single_profile_chart(symbol)
            return

        if profile_chart_generation_limit_param is None:
            profile_chart_generation_limit_param = '50'

        profile_chart_generation_limit = int(profile_chart_generation_limit_param)

        MarketUtils.get_current_profile_charts(profile_chart_generation_limit)
