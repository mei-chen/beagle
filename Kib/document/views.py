import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse, Http404, HttpResponseBadRequest
)
from django.shortcuts import get_object_or_404
from utils.http import set_download_filename

from utils.conversion import pdf_to_docx

from portal.models import Batch
from document.models import Document
from document.tasks import zip_sentences


def test_easypdf_view(request):
    """Test EasyPDF"""

    pdfpath = os.path.join(
        settings.BASE_DIR,
        'utils', 'EasyPDFCloudAPI', '_test', 'DOC002.PDF')
    docxpath = pdf_to_docx(pdfpath, ocr=False)
    docx = open(docxpath)

    response = HttpResponse(
        docx,
        content_type='application/vnd.openxmlformats-officedocument.'
                     'wordprocessingml.document')
    response['Content-Disposition'] = 'attachment; filename="test.docx"'

    return response


@login_required
def download_batch_documents(request, get_files_method):
    try:
        batch = get_object_or_404(Batch, pk=request.GET.get('batch'))
    except ValueError:
        raise Http404("Bad batch id")
    plaintext = bool(request.GET.get('plaintext'))

    zip = getattr(batch, get_files_method)(plaintext)

    response = HttpResponse(zip.getvalue(), content_type='application/zip')
    set_download_filename(response, '%s.zip' % batch.name)
    return response


@login_required
def download_document_sentences(request):
    document_id = request.GET.get('document')
    batch_id = request.GET.get('batch')
    if document_id:
        try:
            doc = get_object_or_404(Document, pk=document_id)
        except ValueError:
            raise Http404('Bad document id')

        if request.GET.get('json'):
            ext = 'json'
            response = HttpResponse(
                doc.get_json(), content_type='application/json'
            )
        else:
            response = HttpResponse(
                doc.get_csv(), content_type='text/csv'
            )
            ext = 'csv'
        set_download_filename(response, '%s.%s' % (doc.name, ext))
        return response

    elif batch_id:
        batch = get_object_or_404(Batch, pk=batch_id)
        ziptype = 'json' if request.GET.get('json') else 'csv'
        zip_sentences(batch, request.session.session_key, ziptype)
        return HttpResponse(status=201)
    return HttpResponseBadRequest()
