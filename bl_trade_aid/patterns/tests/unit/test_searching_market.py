from django.test import TestCase
from django.urls import reverse
from pandas import pandas as pd
from rest_framework.test import APIClient
from unittest.mock import patch
from django.conf import settings
from bl_trade_aid.users.models import User
from ...utils import MarketUtils

import logging
logger = logging.getLogger(__name__)


class ScannerSubscriptionTestCase(TestCase):

    @patch('ib_insync.IB.disconnect')
    @patch('ib_insync.IB.reqScannerData')
    @patch('ib_insync.IB.connect')
    def test_call_req_Scanner_for_no_changed_contracts(
            self,
            mock_connect,
            mock_reqscannerdata,
            mock_disconnect):

        # TODO:call service with one ticker
        # - call util scan function

        MarketUtils.get_contracts()

        # - assert the function calls the mock
        logger.info(f'callcount:  {mock_reqscannerdata.call_count}')
        self.assertEquals(1, mock_connect.call_count)
        self.assertEquals(1, mock_reqscannerdata.call_count)
        self.assertEquals(1, mock_disconnect.call_count)
