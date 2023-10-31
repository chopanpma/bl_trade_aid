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
        parser.add_argument('--profile-chart-generation-limit', '-limit',  help='Limit for profile generation')

    def handle(self, *args, **options):
        # command
        profile_chart_generation_limit_param = options['profile_chart_generation_limit']
        if profile_chart_generation_limit_param is None:
            profile_chart_generation_limit_param = '50'

        profile_chart_generation_limit = int(profile_chart_generation_limit_param)

        MarketUtils.get_current_profile_charts(profile_chart_generation_limit)
