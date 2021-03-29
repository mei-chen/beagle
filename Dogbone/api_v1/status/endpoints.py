from beagle_simpleapi.endpoint import StatusView
from constance import config as beagle_app


class ApplicationStatusView(StatusView):
    url_pattern = r'status'
    endpoint_name = 'app_status_view'

    def authenticate_user(self):
        """
        We don't need the user to be authenticated
        :return:
        """
        return None

    def status(self, request, *args, **kwargs):
        result = {}

        result['extension'] = {'enabled': beagle_app.BROWSER_EXTENSION_ENABLED}
        if not beagle_app.BROWSER_EXTENSION_ENABLED:
            result['extension']['message'] = beagle_app.BROWSER_EXTENSION_DISABLED_MESSAGE

        return result
