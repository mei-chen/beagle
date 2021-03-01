import os.path

from django.conf import settings
from .EasyPDFCloudAPI import EasyPDFCloudAPI
from .EasyPDFCloudExceptions import EasyPDFCloudArgumentException


def pdf_convert(in_file_name, ocr):
    credentials = settings.OCR_PDF_CREDENTIALS if ocr else settings.PDF_CREDENTIALS
    _convert(credentials, in_file_name)


def doc_convert(in_file_name):
    credentials = settings.DOC_CREDENTIALS
    _convert(credentials, in_file_name)


def _convert(credentials, in_file_name):  # noqa
    """
    Sample code to upload a file to the server, have it converted,
    and download the converted file to the computer.

    For internal usage only. Use `pdf_convert` or `doc_convert` to perform an
    actual conversion.
    """
    client_id, client_secret = credentials['ClientID'], credentials['ClientSecret']
    workflow_id, workflow_name = credentials['WorkflowID'], credentials['WorkflowName']

    api = EasyPDFCloudAPI(client_id, client_secret)

    # Look at the list of all workflows and make sure that our workflow info is correct.
    workflows = api.get_workflows()["workflows"]
    found = False
    for workflow in workflows:
        if workflow["workflowID"] == workflow_id and workflow["workflowName"] == workflow_name:
            found = True
            break
    if not found:
        raise EasyPDFCloudArgumentException("Invalid workflow credentials.")

    # Creates a new job and uploads a file to convert.
    json_job = api.start_job(workflow_id, in_file_name)
    job_id = json_job["jobID"]
    print("The file is being uploaded from '%s'..." % in_file_name)

    try:
        # Wait for the job as it is being processed.
        while api.wait_for_job(job_id) is False:
            print("The job is currently running...")
        print("The job was already processed.")

        # Gives the (metadata) output file name on the server.
        json_metadata = api.download_job_output(job_id, "metadata").json()
        file_name = json_metadata["contents"][0]["name"]

        # Downloads the job (file) output.
        print("The file was converted and is being downloaded...")
        response_file = api.download_job_output(job_id, "file")

        # The output directory is the same as the input directory.
        out_dir_name = os.path.dirname(in_file_name)
        out_file_name = os.path.join(out_dir_name, file_name)

        # Saves the converted file to the hard drive.
        print("The file is being saved...")
        try:
            with open(out_file_name, 'wb') as fout:
                for chunk in response_file.iter_content(1024):
                    fout.write(chunk)
        except IOError:
            print("No such file or directory: '%s'." % out_file_name)
        else:
            print("The file was stored in '%s'." % out_file_name)

    finally:
        # Make sure to delete the job from the server if it has been started.
        api.delete_job(job_id)
