import os
import sys
import argparse
import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from typing import List, Optional
from collections import defaultdict
from dateutil.parser import parse

import numpy as np
import pandas as pd

from ibapi import wrapper
from ibapi.common import TickerId, BarData
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.utils import iswrapper

logger = logging.getLogger(__name__)

ContractList = List[Contract]
BarDataList = List[BarData]
OptionalDate = Optional[datetime]


now = datetime.now()


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


class DownloadApp(EClient, wrapper.EWrapper):
    def __init__(self, contracts: ContractList, options: argparse.Namespace):
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
            [b.date, b.open, b.high, b.low, b.close, b.volume, b.barCount, b.average]
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
            ],
        )
        if self.daily_files():
            path = "%s.csv" % make_download_path(self.options, contract)
        else:
            # since we fetched data until midnight, store data in
            # date file to which it belongs
            last = (self.current - timedelta(days=1)).strftime("%Y%m%d")
            path = os.path.sep.join(
                [make_download_path(self.options, contract), "%s.csv" % last, ]
            )
        df.to_csv(path, index=False)

    def return_data(self, contract: Contract, bars: BarDataList) -> None:
        data = [
            [b.date, b.open, b.high, b.low, b.close, b.volume, b.barCount, b.average]
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
        super().historicalDataEnd(reqId, start, end)
        self.pending_ends.remove(reqId)
        if len(self.pending_ends) == 0:
            print(f"All requests for {self.current} complete.")
            for rid, bars in self.bar_data.items():
                self.save_data(self.requests[rid], bars)
                # return self.return_data(self.requests[rid], bars)

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


# def main():

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


class Command(BaseCommand):
    help = 'Download ticker history'

    def add_arguments(self, parser):
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

        if options['debug']:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        try:
            validate_duration(options['duration'])
            validate_size(options['size'])
            options['data_type'] = options['data_type'].upper()
            validate_data_type(options['data_type'])
        except ValidationException as ve:
            print(ve)
            sys.exit(1)

        logging.debug(f"args={args}")
        contracts = []
        for s in options['symbol']:
            contract = make_contract(s, options['security_type'], options['currency'], options['exchange'])
            contracts.append(contract)
            os.makedirs(make_download_path(options, contract), exist_ok=True)
        app = DownloadApp(contracts, options)
        app.connect("192.168.0.18", options['port'], clientId=0)

        app.run()
