from collections import defaultdict
from django.core.management.base import BaseCommand
import pandas as pd
import numpy as np
import warnings

from ib_insync import IB
from ib_insync import Stock
from ib_insync import util

import logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')


def Print_Market_Profile(market_df, height_precision=1, frequency='D'):

    fin_prod_data = market_df.copy()
    fin_prod_data[('High')] = fin_prod_data[('High')] * height_precision
    fin_prod_data[('Low')] = fin_prod_data[('Low')] * height_precision
    fin_prod_data = fin_prod_data.round({'Low': 0, 'High': 0})

    time_groups = fin_prod_data.set_index('Date')
    time_groups = time_groups.groupby(pd.Grouper(freq=frequency))['Close'].mean()

    current_time_group_index = 0
    mp = defaultdict(str)
    char_mark = 64

    # build dictionary with all needed prices
    tot_min_price = min(np.array(fin_prod_data['Low']))
    tot_max_price = max(np.array(fin_prod_data['High']))
    for price in range(int(tot_min_price), int(tot_max_price)):
        mp[price] += ('\t')

    # add max price as it will be ignored in for range loop above
    mp[tot_max_price] = '\t' + str(
            time_groups.index[current_time_group_index]
            )[5:7] + '/' + str(
                    time_groups.index[current_time_group_index]
                    )[8:11]

    for x in range(0, len(fin_prod_data)):
        if fin_prod_data.iloc[x]['Date'] > time_groups.index[current_time_group_index]:
            # new time period
            char_mark = 64
            # buffer and tab all entries
            buffer_max = max([len(v) for k, v in mp.items()])
            current_time_group_index += 1
            for k, v in mp.items():
                mp[k] += (chr(32) * (buffer_max - len(mp[k]))) + '\t'
            mp[tot_max_price] += str(
                    time_groups.index[current_time_group_index])[5:7] + '/' + str(
                            time_groups.index[current_time_group_index])[8:11]

        char_mark += 1

        min_price = fin_prod_data.iloc[x]['Low']
        max_price = fin_prod_data.iloc[x]['High']
        for price in range(int(min_price), int(max_price)):
            mp[price] += (chr(char_mark))

    sorted_keys = sorted(mp.keys(), reverse=True)
    for x in sorted_keys:
        # buffer each list
        print(str("{0:.3f}".format((x * 1.0) / height_precision)) + ': \t' + ''.join(mp[x]))


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

    def normalize_df(self, df):
        df = df.rename(columns={'date': 'DateTime'})
        df = df.rename(columns={'open': 'Open'})
        df = df.rename(columns={'high': 'High'})
        df = df.rename(columns={'low': 'Low'})
        df = df.rename(columns={'close': 'Close'})
        df = df.rename(columns={'volume': 'Volume'})

        df = df.drop(df.columns.difference(
            [
                'DateTime',
                'Open',
                'High',
                'Low',
                'Close',
                'Volume',
                ]), 1, inplace=False)

        df['Date'] = pd.to_datetime(pd.to_datetime(df['DateTime']).dt.date)
        df = df.set_index(pd.DatetimeIndex(df['Date']))

        return df

    def handle(self, *args, **options):
        # command
        util.startLoop()
        ib = IB()
        ib.connect('192.168.0.15', 7497, clientId=1)

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

        print(f'type bars:{type(bars)}')

        print(f'bars:{bars}')

        df = self.normalize_df(util.df(bars))

        logger.info(df)

        Print_Market_Profile(df, height_precision=options['height_precision'])
