import json

from beagle_simpleapi.endpoint import ComputeView
from statistics.tasks import log_statistic_event


class StatisticsComputeView(ComputeView):
    """
    Endpoint for POSTing (i.e. logging to our db)
    new user-related statistic events.
    """

    url_pattern = r'statistics$'
    endpoint_name = 'statistics_compute_view'

    def compute(self, request, *args, **kwargs):
        """
        Expects POST request with following JSON body:
        {
            event: ... (required event name, used for identifying its type),
            attributes: {
                ... (optional event-specific metadata),
            },
            ... (other fields are ignored)
        }

        Does not return any useful payload (only status codes and
        success/error messages).
        """

        try:
            payload = json.loads(request.body)
            log_statistic_event.delay(event_name=payload['event'],
                                      event_user=self.user,
                                      event_data=payload.get('attributes'))
            return {"message": "OK", "http_status": 200}
        except Exception as e:
            return self.build_error_response_from_exception(e)
