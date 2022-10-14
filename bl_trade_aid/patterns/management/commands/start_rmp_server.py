from django.core.management.base import BaseCommand
from ...MP import MpFunctions
from ibapi import wrapper
from ibapi.common import TickerId, BarData
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.utils import iswrapper
from dash.dependencies import Input, Output
from typing import List, Optional
from dateutil.parser import parse
from collections import defaultdict
from datetime import timedelta
from datetime import datetime
from ...models import RawData

import os
import sys
import requests
import dash
import dash_core_components as dcc
import dash_html_components as html
import time

import argparse
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import warnings
import logging
import json

logger = logging.getLogger(__name__)
ContractList = List[Contract]
BarDataList = List[BarData]
OptionalDate = Optional[datetime]
now = datetime.now()

warnings.filterwarnings('ignore')


def make_download_path(options: argparse.Namespace, contract: Contract) -> str:
    """Make path for saving csv files.
    Files to be stored in base_directory/<security_type>/<size>/<symbol>/
    """
    path = os.path.sep.join(
        [
            options['base_directory'],
            options['security_type'],
            options['size'].replace(" ", "_"),
            contract.symbol,
        ]
    )
    return path


def make_contract(symbol: str, sec_type: str, currency: str, exchange: str) -> Contract:
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract


class ValidationException(Exception):
    pass


def _validate_in(value: str, name: str, valid: List[str]) -> None:
    if value not in valid:
        raise ValidationException(f"{value} not a valid {name} unit: {','.join(valid)}")


def _validate(value: str, name: str, valid: List[str]) -> None:
    tokens = value.split()
    if len(tokens) != 2:
        raise ValidationException("{name} should be in the form <digit> <{name}>")
    _validate_in(tokens[1], name, valid)
    try:
        int(tokens[0])
    except ValueError as ve:
        raise ValidationException(f"{name} dimenion not a valid number: {ve}")


SIZES = ["secs", "min", "mins", "hour", "hours", "day", "week", "month"]
DURATIONS = ["S", "D", "W", "M", "Y"]


def validate_duration(duration: str) -> None:
    _validate(duration, "duration", DURATIONS)


def validate_size(size: str) -> None:
    _validate(size, "size", SIZES)


def validate_data_type(data_type: str) -> None:
    _validate_in(
        data_type,
        "data_type",
        [
            "TRADES",
            "MIDPOINT",
            "BID",
            "ASK",
            "BID_ASK",
            "ADJUSTED_LAST",
            "HISTORICAL_VOLATILITY",
            "OPTION_IMPLIED_VOLATILITY",
            "REBATE_RATE",
            "FEE_RATE",
            "YIELD_BID",
            "YIELD_ASK",
            "YIELD_BID_ASK",
            "YIELD_LAST",
        ],
    )


class DateAction(argparse.Action):
    """Parses date strings."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        value: str,
        option_string: str = None,
    ):
        """Parse the date."""
        setattr(namespace, self.dest, parse(value))


class DownloadApp(EClient, wrapper.EWrapper):
    def __init__(
            self,
            contracts: ContractList,
            options: argparse.Namespace):
        EClient.__init__(self, wrapper=self)
        wrapper.EWrapper.__init__(self)
        self.request_id = 0
        self.started = False
        self.next_valid_order_id = None
        self.contracts = contracts
        self.requests = {}
        self.bar_data = defaultdict(list)
        self.pending_ends = set()
        self.options = options
        self.current = self.options['end_date']
        self.duration = self.options['duration']
        self.useRTH = 0

    def next_request_id(self, contract: Contract) -> int:
        self.request_id += 1
        self.requests[self.request_id] = contract
        return self.request_id

    def historicalDataRequest(self, contract: Contract) -> None:
        cid = self.next_request_id(contract)
        self.pending_ends.add(cid)

        self.reqHistoricalData(
            cid,  # tickerId, used to identify incoming data
            contract,
            self.current.strftime("%Y%m%d 00:00:00"),  # always go to midnight
            self.duration,  # amount of time to go back
            self.options['size'],  # bar size
            self.options['data_type'],  # historical data type
            self.useRTH,  # useRTH (regular trading hours)
            1,  # format the date in yyyyMMdd HH:mm:ss
            False,  # keep up to date after snapshot
            [],  # chart options
        )

    def save_data(self, contract: Contract, bars: BarDataList) -> None:
        data = [
            [
                b.date,
                b.open,
                b.high,
                b.low,
                b.close,
                b.volume,
                b.barCount,
                b.average,
                contract.symbol,
                ]
            for b in bars
        ]
        df = pd.DataFrame(
            data,
            columns=[
                "datetime",
                "Open",
                "High",
                "Low",
                "Close",
                "volume",
                "barCount",
                "average",
                "symbol",
            ],
        )

        RawData.objects.all().delete()
        json_list = json.loads(json.dumps(list(df.T.to_dict().values())))
        for dic in json_list:
            RawData.objects.get_or_create(**dic)

    def return_data(self, contract: Contract, bars: BarDataList) -> None:
        data = [
            [
                b.date,
                b.open,
                b.high,
                b.low,
                b.close,
                b.volume,
                b.barCount,
                b.average,
                b.symbol]
            for b in bars
        ]
        df = pd.DataFrame(
            data,
            columns=[
                "datetime",
                "Open",
                "High",
                "Low",
                "Close",
                "volume",
                "barCount",
                "average",
                "symbol",
            ],
        )
        return df

    def daily_files(self):
        return SIZES.index(self.options['size'].split()[1]) >= 5

    @iswrapper
    def headTimestamp(self, reqId: int, headTimestamp: str) -> None:
        contract = self.requests.get(reqId)
        ts = datetime.strptime(headTimestamp, "%Y%m%d  %H:%M:%S")
        logging.info("Head Timestamp for %s is %s", contract, ts)
        if ts > self.options['start_date'] or self.options['max_days']:
            logging.warning("Overriding start date, setting to %s", ts)
            self.options['start_date'] = ts  # TODO make this per contract
        if ts > self.options['end_date']:
            logging.warning("Data for %s is not available before %s", contract, ts)
            self.done = True
            return
        # if we are getting daily data or longer, we'll grab the entire amount at once
        if self.daily_files():
            days = (self.options['end_date'] - self.options['start_date']).days
            if days < 365:
                self.duration = "%d D" % days
            else:
                self.duration = "%d Y" % np.ceil(days / 365)
            # when getting daily data, look at regular trading hours only
            # to get accurate daily closing prices
            self.useRTH = 1
            # round up current time to midnight for even days
            self.current = self.current.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        self.historicalDataRequest(contract)

    @iswrapper
    def historicalData(self, reqId: int, bar) -> None:
        self.bar_data[reqId].append(bar)

    @iswrapper
    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        print("historidalDataEnd:")
        super().historicalDataEnd(reqId, start, end)
        self.pending_ends.remove(reqId)
        if len(self.pending_ends) == 0:
            print(f"All requests for {self.current} complete.")
            for rid, bars in self.bar_data.items():
                self.save_data(self.requests[rid], bars)
                # df = self.return_data(self.requests[rid], bars)
                # print(f"df result: {df}")
                # self.update_data_instance.update_graph_for_real(df, self.value)

            self.current = datetime.strptime(start, "%Y%m%d  %H:%M:%S")
            if self.current <= self.options['start_date']:
                self.done = True
            else:
                for contract in self.contracts:
                    self.historicalDataRequest(contract)

    @iswrapper
    def connectAck(self):
        logging.info("Connected")

    @iswrapper
    def nextValidId(self, order_id: int):
        super().nextValidId(order_id)

        self.next_valid_order_id = order_id
        logging.info(f"nextValidId: {order_id}")
        # we can start now
        self.start()

    def start(self):
        if self.started:
            return

        self.started = True
        for contract in self.contracts:
            self.reqHeadTimeStamp(
                self.next_request_id(contract), contract, self.options['data_type'], 0, 1
            )

    @iswrapper
    def error(self, req_id: TickerId, error_code: int, error: str):
        super().error(req_id, error_code, error)
        print("Error. Id:", req_id, "Code:", error_code, "Msg:", error)


class MainGraph:
    def __init__(self, options):
        self.options = options
        time.sleep(10)

        self.app = dash.Dash(__name__)

        # url_30m = "https://www.binance.com/api/v1/klines?symbol=BTCBUSD&interval=30m"  # 10 days history 30 min ohlcv
        # self.df = self.get_data(url_30m)

        # self.df.to_csv('btcusd30m.csv', index=False)

        # params

        rawdf = RawData.as_dataframe()
        self.df = self.normalize_df(rawdf)

        print('columnas tws:')
        for col in self.df.columns:
            print(col)

        context_days = len([group[1] for group in self.df.groupby(self.df.index.date)])
        print('after context days')
        # Number of days used for context
        self.freq = 2  # for 1 min bar use 30 min frequency for each TPO, here we fetch default 30 min bars server
        self.avglen = context_days - 2  # num days to calculate average values
        self.mode = 'tpo'  # for volume --> 'vol'
        self.trading_hr = 24  # Default for BTC USD or Forex
        day_back = 0  # -1 While testing sometimes maybe you don't want current days data then use -1
        print('after setting parameters  day_back')
        # ticksz = 28 # If you want to use manual tick size then uncomment this.
        # Really small number means convoluted alphabets (TPO)
        self.ticksz = (self.get_ticksize(self.df.copy(), freq=self.freq))*2
        # Algorithm will calculate the optimal tick size based on volatility
        self.textsize = 10

        if day_back != 0:
            self.symbol = 'Historical Mode'
        else:
            self.symbol = 'BTC-USD Live'

        print('after df.copy')
        dfnflist = [group[1] for group in self.df.groupby(self.df.index.date)]  #

        print('after group by')
        self.dates = []
        for d in range(0, len(dfnflist)):
            self.dates.append(dfnflist[d].index[0])

        print('after appending dates')
        date_time_close = datetime.today().strftime('%Y-%m-%d') + ' ' + '23:59:59'
        append_dt = pd.Timestamp(date_time_close)
        self.dates.append(append_dt)
        date_mark = {str(h): {'label': str(h), 'style': {'color': 'blue', 'fontsize': '4',
                                                         'text-orientation': 'upright'}} for h in range(
                                                             0,
                                                             len(self.dates))}

        print('after date_mark')

        self.mp = MpFunctions(
            data=self.df.copy(), freq=self.freq,
            style=self.mode, avglen=self.avglen,
            ticksize=self.ticksz, session_hr=self.trading_hr)
        print(f'freq: {self.freq}, style: {self.mode}, avlen: {self.avglen},'
              f'ticksize: {self.ticksz}, session_hr: {self.trading_hr}')
        self.mplist = self.mp.get_context()

        print(f'after GetContext mplist: {self.mplist}')
        self.app.layout = html.Div(
            html.Div([
                dcc.Location(id='url', refresh=False),
                dcc.Link('Twitter', href='https://twitter.com/beinghorizontal'),
                html.Br(),
                dcc.Link('python source code', href='http://www.github.com/beinghorizontal'),
                html.H4('@beinghorizontal'),
                dcc.Graph(id='beinghorizontal'),
                dcc.Interval(
                    id='interval-component',
                    interval=20 * 1000,  # Reduce the time if you want frequent updates 5000 = 5 sec
                    n_intervals=0
                ),
                html.P([
                    html.Label("Time Period"),
                    dcc.RangeSlider(id='slider',
                                    pushable=1,
                                    marks=date_mark,
                                    min=0,
                                    max=len(self.dates),
                                    step=None,
                                    value=[len(self.dates) - 2, len(self.dates) - 1])
                ], style={'width': '80%',
                          'fontSize': '14px',
                          'padding-left': '100px',
                          'display': 'inline-block'})
            ])
        )

        print('about to set callback')
        self.app.callback(
            Output(
                component_id='beinghorizontal',
                component_property='figure'),
            [
                Input('interval-component', 'n_intervals'),
                Input('slider', 'value')
            ])(self.update_graph)

    def normalize_df(self, df):
        newdf = df.drop(df.columns.difference(
            [
                'datetime',
                'Open',
                'High',
                'Low',
                'Close',
                'volume',
                ]), 1, inplace=False)
        format = '%Y%m%d  %H:%M:%S'
        newdf['datetime'] = pd.to_datetime(newdf['datetime'], format=format)
        newdf = newdf.set_index(pd.DatetimeIndex(newdf['datetime']))
        print(f'index in df: {newdf.index}')

        return newdf

    def run_server(self, port, host, debug):
        self.app.run_server(
            port=port, host=host,
            debug=debug)  # debug=False if executing from ipython(vscode/Pycharm/Spyder)

    def get_ticksize(self, data, freq=30):
        # data = dflive30
        print('inside get_ticksize')
        numlen = int(len(data) / 2)
        # sample size for calculating ticksize = 50% of most recent data
        print('after numlen')
        tztail = data.tail(numlen).copy()
        print('after tail.copy')
        tztail['tz'] = tztail.Close.rolling(freq).std()  # std. dev of 30 period rolling
        print('after tztail')
        tztail = tztail.dropna()
        ticksize = np.ceil(tztail['tz'].mean() * 0.25)  # 1/4 th of mean std. dev is our ticksize
        print('after ceil')

        if ticksize < 0.2:
            ticksize = 0.2  # minimum ticksize limit

        print('exiting get_ticksize')
        return int(ticksize)

    def get_data(self, url):
        """
        :param url: binance url
        :return: ohlcv dataframe
        """
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data)
        df = df.apply(pd.to_numeric)
        df[0] = pd.to_datetime(df[0], unit='ms')
        df = df[[0, 1, 2, 3, 4, 5]]
        df.columns = ['datetime', 'Open', 'High', 'Low', 'Close', 'volume']
        df = df.set_index('datetime', inplace=False, drop=False)
        return df

    def update_graph(self, n, value):
        print("update_graph:")
        listmp_hist = self.mplist[0]
        print(f"mplist 0:{self.mplist[0]}")
        distribution_hist = self.mplist[1]
        print(f"mplist 1:{self.mplist[1]}")
        # url_1m = "https://www.binance.com/api/v1/klines?symbol=BTCBUSD&interval=1m"
        # df_live1 = self.get_data(url_1m)  # this line fetches new data for current day
        df_live1 = RawData.as_dataframe()
        print(f"df after as_dataframe:{df_live1}")
        df_live1 = df_live1.dropna()

        print(f"df after dropna:{df_live1}")
        dflive30 = df_live1.resample('30min').agg({'datetime': 'last', 'Open': 'first', 'High': 'max', 'Low': 'min',
                                                   'Close': 'last', 'volume': 'sum'})
        print(f"df after resample:{dflive30}")
        # df2 = pd.concat([self.df, dflive30])
        df2 = dflive30  # TODO: understand previous commented line
        df2 = df2.drop_duplicates('datetime')
        print(f"df after drop_duplicates:{df_live1}")

        ticksz_live = (self.get_ticksize(dflive30.copy(), freq=2))
        print(f"tick size:{ticksz_live}")
        mplive = MpFunctions(
            data=dflive30.copy(),
            freq=self.freq,
            style=self.mode,
            avglen=self.avglen,
            ticksize=ticksz_live,
            session_hr=self.trading_hr)

        print(f"mplive:{mplive}")
        mplist_live = mplive.get_context()
        print(f"mplist_live:{mplist_live}")
        listmp_live = mplist_live[0]  # it will be in list format so take [0] slice for current day MP data frame
        print(f"mplist_live 0:{mplist_live[0]}")
        df_distribution_live = mplist_live[1]
        print(f"df_distribution_live:{mplist_live[1]}")
        df_distribution_concat = pd.concat([distribution_hist, df_distribution_live], axis=0)
        print(f"df_distribution_concat:{df_distribution_concat}")
        df_distribution_concat = df_distribution_concat.reset_index(inplace=False, drop=True)
        print(f"df_distribution_concat reseted index :{df_distribution_concat}")

        df_updated_rank = self.mp.get_dayrank()
        ranking = df_updated_rank[0]
        power1 = ranking.power1  # Non-normalised IB strength
        power = ranking.power  # Normalised IB strength for dynamic shape size for markers at bottom
        breakdown = df_updated_rank[1]
        dh_list = ranking.highd
        dl_list = ranking.lowd

        listmp = listmp_hist + listmp_live

        df3 = df2[(df2.index >= self.dates[value[0]]) & (df2.index <= self.dates[value[1]])]
        DFList = [group[1] for group in df2.groupby(df2.index.date)]

        fig = go.Figure(data=[go.Candlestick(x=df3.index,

                                             open=df3['Open'],
                                             high=df3['High'],
                                             low=df3['Low'],
                                             close=df3['Close'],
                                             showlegend=True,
                                             name=self.symbol,
                                             opacity=0.3)])  # To make candlesticks more prominent increase the opacity

        for inc in range(value[1] - value[0]):
            i = value[0]
            # inc = 0 # for debug
            # i = value[0]

            i += inc
            df1 = DFList[i].copy()
            df_mp = listmp[i]
            irank = ranking.iloc[i]  # select single row from ranking df
            df_mp['i_date'] = df1['datetime'][0]
            # # @todo: background color for text
            df_mp['color'] = np.where(np.logical_and(
                df_mp['close'] > irank.vallist, df_mp['close'] < irank.vahlist), 'green', 'white')

            df_mp = df_mp.set_index('i_date', inplace=False)

            # print(df_mp.index)
            fig.add_trace(
                go.Scattergl(x=df_mp.index, y=df_mp.close, mode="text", text=df_mp.alphabets,
                             showlegend=False, textposition="top right",
                             textfont=dict(family="verdana", size=self.textsize, color=df_mp.color)))

            if power1[i] < 0:
                my_rgb = 'rgba({power}, 3, 252, 0.5)'.format(power=abs(165))
            else:
                my_rgb = 'rgba(23, {power}, 3, 0.5)'.format(power=abs(252))

            brk_f_list_maj = []
            f = 0
            for f in range(len(breakdown.columns)):
                brk_f_list_min = []
                for index, rows in breakdown.iterrows():
                    if rows[f] != 0:
                        brk_f_list_min.append(index + str(': ') + str(rows[f]) + '<br />')
                brk_f_list_maj.append(brk_f_list_min)

            breakdown_values = ''  # for bubble callouts
            for st in brk_f_list_maj[i]:
                breakdown_values += st
            commentary_text = (
                '<br />Insights:<br />High: {}<br />Low: {}<br />Day_Range: '
                '{}<br />VAH:  {}<br /> POC:  {}<br /> VAL:  {}<br /> Balance Target:  '
                '{}<br /> Day Type:  {}<br />strength: {}%<br /><br />strength BreakDown:  {}<br />{}<br />{}'.format(
                    dh_list[i], dl_list[i], round(dh_list[i] - dl_list[i], 2),
                    irank.vahlist,
                    irank.poclist, irank.vallist, irank.btlist, irank.daytype, irank.power, '',
                    '-------------------', breakdown_values))

            fig.add_trace(go.Scattergl(
                x=[irank.date],
                y=[df3['High'].max() - (self.ticksz)],
                mode="markers",
                marker=dict(color=my_rgb, size=0.90 * power[i],
                            line=dict(color='rgb(17, 17, 17)', width=2)),
                # marker_symbol='square',
                hovertext=commentary_text, showlegend=False))

            lvns = irank.lvnlist

            for lvn in lvns:
                if lvn > irank.vallist and lvn < irank.vahlist:
                    fig.add_shape(
                        # Line Horizontal
                        type="line",
                        x0=df_mp.index[0],
                        y0=lvn,
                        x1=df_mp.index[0] + timedelta(hours=1),
                        y1=lvn,
                        line=dict(
                            color="darksalmon",
                            width=2,
                            dash="dashdot", ), )

            fig.add_shape(
                type="line",
                x0=df_mp.index[0],
                y0=dl_list[i],
                x1=df_mp.index[0],
                y1=dh_list[i],
                line=dict(
                    color="gray",
                    width=1,
                    dash="dashdot", ), )

        fig.layout.xaxis.type = 'category'  # This line will omit annoying weekends on the plotly graph

        ltp = df1.iloc[-1]['Close']
        if ltp >= irank.poclist:
            ltp_color = 'green'
        else:
            ltp_color = 'red'

        fig.add_trace(
            go.Bar(
                x=df3.index,
                y=df3['volume'],
                marker=dict(color='magenta'),
                yaxis='y3',
                name=str(commentary_text)))

        fig.add_trace(go.Scattergl(
            x=[df3.iloc[-1]['datetime']],
            y=[df3.iloc[-1]['Close']],
            mode="text",
            name="last traded price",
            text=[str(df3.iloc[-1]['Close'])],
            textposition="bottom center",
            textfont=dict(size=18, color=ltp_color),
            showlegend=False
        ))
        # to make x-axis less crowded
        if value[1] - value[0] > 4:
            dticksv = 30
        else:
            dticksv = len(self.dates)
        y3min = df3['volume'].min()
        y3max = df3['volume'].max() * 10
        ymin = df3['Low'].min()
        ymax = df3['High'].max() + (4 * self.ticksz)

        # Adjust height & width according to your monitor size & orientation.
        fig.update_layout(paper_bgcolor='black', plot_bgcolor='black', height=900, width=1990,
                          xaxis=dict(showline=True, color='white', type='category', title_text='Time', tickangle=45,
                                     dtick=dticksv, title_font=dict(size=18, color='white')),
                          yaxis=dict(showline=True, color='white', range=[ymin, ymax], showgrid=False,
                                     title_text='BTC/USD'),
                          yaxis2=dict(showgrid=False),
                          yaxis3=dict(range=[y3min, y3max], overlaying="y",
                                      side="right",
                                      color='black',
                                      showgrid=False),
                          legend=dict(font=dict(color='White', size=14)))

        fig.update_layout(yaxis_tickformat='d')
        fig["layout"]["xaxis"]["rangeslider"]["visible"] = False
        fig["layout"]["xaxis"]["tickformat"] = "%H:%M:%S"

        # plot(fig, auto_open=True) # For debugging
        return (fig)


# if __name__ == '__main__':
    # app.run_server(port=8000, host='127.0.0.1',
    # debug=True)  # debug=False if executing from ipython(vscode/Pycharm/Spyder)


class Command(BaseCommand):
    help = 'Start market profile server'

    def add_arguments(self, parser):

        parser.add_argument(
            "-gp", "--graph-port", type=int, default=8999, help="local port for TWS connection"
        )

        parser.add_argument("symbol", nargs="+")
        parser.add_argument(
            "-d", "--debug", action="store_true", help="turn on debug logging"
        )
        parser.add_argument(
            "-p", "--port", type=int, default=7496, help="local port for TWS connection"
        )
        parser.add_argument("--size", type=str, default="1 min", help="bar size")
        parser.add_argument("--duration", type=str, default="1 D", help="bar duration")
        parser.add_argument(
            "-t", "--data-type", type=str, default="TRADES", help="bar data type"
        )
        parser.add_argument(
            "--base-directory",
            type=str,
            default="data",
            help="base directory to write bar files",
        )
        parser.add_argument(
            "--currency", type=str, default="USD", help="currency for symbols"
        )
        parser.add_argument(
            "--exchange", type=str, default="SMART", help="exchange for symbols"
        )
        parser.add_argument(
            "--security-type", type=str, default="STK", help="security type for symbols"
        )
        parser.add_argument(
            "--start-date",
            help="First day for bars",
            default=now - timedelta(days=2),
            action=DateAction,
        )
        parser.add_argument(
            "--end-date", help="Last day for bars", default=now, action=DateAction,
        )
        parser.add_argument(
            "--max-days", help="Set start date to earliest date", action="store_true",
        )

    def handle(self, *args, **options):
        # command

        try:
            graph = MainGraph(options)

            print('about to init GetDataFromIB')
            get_data_class = GetDataFromIB(options)
            print('about call get_data_from_ib')
            get_data_class.get_data_from_ib()

            graph.run_server(
                port=options['graph_port'], host='0.0.0.0',
                debug=True)  # debug=False if executing from ipython(vscode/Pycharm/Spyder)

        except Exception as e:
            print(e)
            sys.exit(1)

        logging.debug(f"args={args}")


class GetDataFromIB():
    def __init__(self, options):
        self.options = options

    def get_data_from_ib(self):
        print("options:{}".format(self.options))
        print("get_data_from_ib:")
        options = self.options

        if options['debug']:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        try:
            print("try from get_data_from_ib ")
            print(f"validate duration: {options['duration']}")
            validate_duration(options['duration'])
            print(f"validate size: {options['size']}")
            validate_size(options['size'])
            options['data_type'] = options['data_type'].upper()
            print(f"validate data_type: {options['data_type']}")
            validate_data_type(options['data_type'])
            print("after validations")
        except ValidationException as ve:
            print(ve)
            sys.exit(1)

        contracts = []
        for s in options['symbol']:
            print("calling ib library")
            contract = make_contract(s, options['security_type'], options['currency'], options['exchange'])
            contracts.append(contract)
            # os.makedirs(make_download_path(options, contract), exist_ok=True)

        print(f"contracts:{contracts}")

        app = DownloadApp(contracts, options)
        # app.connect("192.168.0.3", options['port'], clientId=0)
        app.connect("192.168.0.10", options['port'], clientId=0)

        app.run()
