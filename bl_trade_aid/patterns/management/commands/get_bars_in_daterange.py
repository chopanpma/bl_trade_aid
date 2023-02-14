from django.core.management.base import BaseCommand
import warnings

from ib_insync import IB
from ib_insync import Stock
from ib_insync import util

import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')


class Command(BaseCommand):
    help = 'Start market profile server'

    def add_arguments(self, parser):
        parser.add_argument("symbol")
        parser.add_argument(
            "-hp", "--height-precision", type=int, default=100, help="how many decimals considered"
        )
        parser.add_argument(
            "-p", "--port", type=int, default=7496, help="local port for TWS connection"
        )
        parser.add_argument("--days", type=str, default="4", help="days for the mp")
        parser.add_argument(
            "--exchange", type=str, default="SMART", help="exchange for symbols"
        )
        parser.add_argument(
            "--security-type", type=str, default="STK", help="security type for symbols"
        )
        parser.add_argument(
            "-eh", "--extended-hours", action="store_false", help="Extended Trading Hours"
        )
        parser.add_argument(
            "-d", "--debug", action="store_true", help="turn on debug logging"
        )

    def handle(self, *args, **options):
        # command
        util.startLoop()
        ib = IB()
        ib.connect('192.168.0.20', 7497, clientId=1)

        contract = Stock(
                options['symbol'],
                options['exchange'],
                'USD'
                )

        dt = ''
        bars = ib.reqHistoricalData(
                contract,
                endDateTime=dt,
                durationStr=f'{options["days"]} D',
                barSizeSetting='30 mins',
                whatToShow='TRADES',
                useRTH=options['extended_hours'],
                formatDate=1)

        # Display the filtered contracts
        with open('bars.txt', 'w') as file:
            file.write(f'bars: {bars}')
