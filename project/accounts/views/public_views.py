"""
Implements views that any visitor of the website can interact with.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from ..services import DateManager
from rest_framework.status import HTTP_200_OK

class CountDownView(APIView):
    """
    API endpoint for displaying a countdown to next Sunday.
    """
    def get(self, request) -> Response:
        countdown = DateManager.Countdown.to_next_sunday()
        return Response(data=countdown.to_dict(), status=HTTP_200_OK)