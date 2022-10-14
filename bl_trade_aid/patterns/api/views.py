from rest_framework.response import Response
from rest_framework.views import APIView
from ..utils import APIUtils

# Create your views here.

import logging
logger = logging.getLogger(__name__)


class ListBarDataView(APIView):

    def post(self,
             request,
             format=None,
             ):

        # TODO; 0. get parameters from url * toy en este paso
        # parameters already in url, take them from there and call function
        symbol = request.data.get('symbol')
        height_precision = request.data.get('height_precision')
        exchange = request.data.get('exchange')
        security_type = request.data.get('security_type')
        use_extended_hours = request.data.get('use_extended_hours')
        logger.info(f'symbol:{symbol}')

        response_dict = APIUtils.get_dataframe_from_broker(
                   symbol,
                   height_precision,
                   exchange,
                   security_type,
                   use_extended_hours,
                   )
        # TODO: 1. get items from IBR

        # TODO: 2. prepare dictionary

        # TODO: 3. return dictionary empty now, later change to real dict step 2

        return Response(response_dict)
