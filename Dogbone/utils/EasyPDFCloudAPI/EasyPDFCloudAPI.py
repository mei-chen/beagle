import logging
import requests

from EasyPDFCloudExceptions import EasyPDFCloudArgumentException, EasyPDFCloudHTTPException


# URL Endpoints.
JOB_ENDPOINT = 'https://api.easypdfcloud.com/v1/jobs/'
TOKEN_ENDPOINT = 'https://www.easypdfcloud.com/oauth2/token'
WORKFLOW_ENDPOINT = 'https://api.easypdfcloud.com/v1/workflows/'
AUTHORIZE_ENDPOINT = 'https://www.easypdfcloud.com/oauth2/authorize'

logger = logging.getLogger(__name__)


class EasyPDFCloudAPI(object):

    def __init__(self, client_id, client_secret):
        """ Creates an instance of the API and loads it with a new token. """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.update_token()

    def update_token(self):
        """ Sends a POST request to the server and updates the current token with a new one. """
        data = {"grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "epc.api"}
        response = requests.post(TOKEN_ENDPOINT, data=data)
        if self.check_response(response, False):
            try:
                json = response.json()
                self.access_token = json["access_token"]
            except (ValueError, KeyError):
                exc = EasyPDFCloudArgumentException("Invalid client credentials.")
                logger.error(exc)
                raise exc

    def check_response(self, http_response, auto_refresh):
        """ Checks the status codes in the HTTPResponse object and decides the appropriate action to take. """
        # Indicates successful request/response.
        if 200 <= http_response.status_code < 300:
            return True

        # Request was bad or unauthorized.
        if http_response.status_code in (400, 401):
            header = http_response.headers.get("WWW-Authenticate")
            error = description = None
            if header is not None:
                # Get error information from the header.
                fields = header.split(",")
                for field in fields:
                    name, value = field.split("=")
                    name = name.lower()
                    value = value.replace("%20", " ")
                    if name in ("error", "bearer error"):
                        error = value
                    elif name in ("error_description", "bearer error_description"):
                        description = value
                # If using an invalid access token, refresh it.
                if error.lower() == "\"invalid_token\"" and auto_refresh:
                    self.update_token()
                    return False
            exc = EasyPDFCloudHTTPException(http_response.status_code, http_response.reason, error, description)
            logger.error(exc)
            raise exc

        # If a different error occurs, gathers info from the server as a JSON response and raises an exception.
        e = EasyPDFCloudHTTPException(http_response.status_code, http_response.reason)
        try:
            json_error = http_response.json()
            # Updates the exception object, if necessary.
            message = json_error.get("message")
            if message is not None:
                e.reason = message
            error = json_error.get("error")
            if error is not None:
                e.error = error
            source = json_error.get("source")
            if source is not None:
                e.description_or_source = source
        finally:
            logger.error(e)
            raise e

    def get_workflows(self):
        """ Returns a JSON object containing all the user's workflows. """
        token = self.access_token
        url = WORKFLOW_ENDPOINT
        response = requests.get(url,
                                headers={"Authorization": "Bearer " + token},
                                verify=False)
        if self.check_response(response, True):
            return response.json()
        elif not self.check_response(response, True):
            return self.get_workflows()

    def get_workflow(self, workflow_id):
        """ Returns a JSON object with information about one specific workflow. """
        token = self.access_token
        url = WORKFLOW_ENDPOINT + workflow_id
        response = requests.get(url,
                                headers={"Authorization": "Bearer " + token},
                                verify=False)
        if self.check_response(response, True):
            return response.json()
        elif not self.check_response(response, True):
            return self.get_workflow(workflow_id)

    def start_job(self, workflow_id, file_path):
        """ Uploads a file and starts a workflow job. """
        token = self.access_token
        url = WORKFLOW_ENDPOINT + workflow_id + "/jobs"
        file_obj = {'file': open(file_path, 'rb')}
        response = requests.post(url,
                                 files=file_obj,
                                 headers={"Authorization": "Bearer " + token},
                                 verify=False)
        if self.check_response(response, True):
            return response.json()
        elif not self.check_response(response, True):
            return self.start_job(workflow_id, file_obj)

    def get_job_info(self, job_id):
        """ Gets information about a specific job. """
        token = self.access_token
        url = JOB_ENDPOINT + job_id
        response = requests.get(url,
                                headers={"Authorization": "Bearer " + token},
                                verify=False)
        if self.check_response(response, True):
            return response.json()
        elif not self.check_response(response, True):
            return self.get_job_info(job_id)

    def wait_for_job(self, job_id):
        """ Waits for the specified job until the server indicates that it has been completed. """
        token = self.access_token
        url = JOB_ENDPOINT + job_id
        try:
            response = requests.post(url,
                                     headers={"Authorization": "Bearer " + token},
                                     verify=False)
            message = response.json()["message"]
            if message == "The job is already processed" or self.check_response(response, True):
                return True
            elif not self.check_response(response, True):
                return self.wait_for_job(job_id)
        except EasyPDFCloudHTTPException as e:
            if e.status_code == 409:
                return False
            else:
                logger.error(e)
                raise

    def download_job_output(self, job_id, output_type, file_name=None):
        """ Receives information on and downloads the output from a specific job. """
        if output_type.lower() in ("file", "metadata"):
            token = self.access_token
            if file_name is None:
                url = JOB_ENDPOINT + job_id + "/output/"
            else:
                url = JOB_ENDPOINT + job_id + "/output/" + file_name
            response = requests.get(url,
                                    params={"type": output_type},
                                    headers={"Authorization": "Bearer " + token},
                                    stream=True, verify=False)
            if self.check_response(response, True):
                return response
            elif not self.check_response(response, True):
                return self.download_job_output(job_id, output_type, file_name)
        else:
            exc = EasyPDFCloudArgumentException("Invalid output type. Must be 'file' or 'metadata'.")
            logger.error(exc)
            raise exc

    def delete_job(self, job_id):
        """ Deletes a job from the server. """
        token = self.access_token
        url = JOB_ENDPOINT + job_id
        response = requests.delete(url,
                                   headers={"Authorization": "Bearer " + token},
                                   verify=False)
        if self.check_response(response, True):
            return response
        elif not self.check_response(response, True):
            return self.delete_job(job_id)
