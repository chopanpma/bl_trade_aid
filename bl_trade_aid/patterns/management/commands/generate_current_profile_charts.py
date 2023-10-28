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
    help = 'Call trades of the day with parameters, and call profile for them'

    def handle(self, *args, **options):
        # command
        MarketUtils.get_current_profile_charts()
