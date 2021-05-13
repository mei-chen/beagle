"""
    conversion
    ==========

    A library to convert documents to plain text.
"""

import chardet
import contextlib
import logging
import os
import string
import subprocess
import time

import PyPDF2

from constance import config
from dogbone.exceptions import DocumentSizeOverLimitException
from pdf2docx import Converter
import ocrmypdf


def strings(filename, min=4):
    """
    Helper function to iterate through a file binary and pull out strings
    called by requires_ocr()
    """
    with open(filename, errors="ignore") as f:
        result = ""
        for c in f.read():
            if c in string.printable:
                result += c
                continue
            if len(result) >= min:
                yield result
            result = ""


def requires_ocr(filename):
    """
    Helper function to look for 'FontName' in a binary file
    indicating text presence and hence no necessity for OCR
    """
    is_ocr = True
    for s in strings(filename):
        if 'FontName' in s:
            is_ocr = False
            break
    return is_ocr


@contextlib.contextmanager
def profile(tool):
    logging.info('%s: starting', tool)
    start = time.time()
    yield
    finish = time.time()
    logging.info('%s: finished in %.3f s', tool, finish - start)


def execute(args):
    tool = args[0]

    with profile(tool):
        process = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = list(map(str.strip, process.communicate()))

    if process.returncode:
        if stderr:
            logging.error('%s: stderr:\n', tool, stderr)
        return False
    else:
        if stdout:
            logging.info('%s: stdout:\n', tool, stdout)
        return True


def pdftotext(filename):
    """
    Tries to extract embedded text from a PDF file with pdftotext.
    Preserves the original text layout.
    """

    logging.warning('pdftotext: %s', filename)

    # Replace '.pdf' with '.txt' for the final output file
    filename_out = filename[:-4] + '.txt'

    return execute(['pdftotext', '-layout', filename, filename_out])


def tesseract(filename):
    """
    Converts a PDF file to TIFF and tries to perform OCR with tesseract.
    If tesseract succeeds, it outputs another PDF file (overwriting
    the original one!), which is processed by pdftotext afterwards in order to
    preserve the original text layout (since tesseract cannot do that).
    """

    logging.warning('tesseract: %s', filename)

    try:
        # Replace '.pdf' with '.tiff' for the auxiliary input file
        filename_in = filename[:-4] + '.tiff'

        convert_args = ['convert', '-density', '300', '-depth', '8',
                        '-strip', '-background', 'white', '-alpha', 'off',
                        filename, filename_in]

        if not execute(convert_args):
            return False

        # Overwrite the contents of the original file!

        # Yet another '.pdf' will be added automatically to the output filename
        tesseract_args = ['tesseract', filename_in, filename[:-4], 'pdf']

        if not execute(tesseract_args):
            return False

        return pdftotext(filename)

    finally:
        # Cleanup
        if os.path.isfile(filename_in):
            os.remove(filename_in)


def pdf_to_txt(filename, need_ocr):
    converter = tesseract if need_ocr else pdftotext
    return converter(filename)


def pdf_to_docx(filename):
    """
    Transcodes a .pdf file to docx via the EasyPdfCloud
    :param filename: path to locate the .pdf file
    :returns: path to the docx version of the file
    """

    upload = os.path.abspath(filename)
    need_ocr = requires_ocr(upload)
    if not os.path.isfile(upload):
        raise Exception('File %s does not exist.' % upload)
    if need_ocr:
        logging.info('Document %s needs OCR' % filename)
        try:
            pdfin = open(upload, "rb")
            reader = PyPDF2.PdfFileReader(pdfin)
            num_pages = reader.getNumPages()
        except Exception as e:
            # Log the exception and move on
            logging.error(
                'process_document_conversion: Error on counting pages of pdf %s. Got exception %s: %s'
                % (filename, type(e).__name__, str(e))
            )
            num_pages = 0

        logging.info('Document %s has %s pages' % (filename, num_pages))

        if num_pages > config.MAX_PDF_OCR_UPLOAD_PAGES:
            logging.warning('Document %s is over-sized' % filename)
            raise DocumentSizeOverLimitException("Document uploaded is too large to be OCRed: %s" % num_pages)

    ext = '.docx'

    try:
        pdf_convert(upload, need_ocr)
    except Exception as e:
        logging.error('%spdf_to_docx conversion failed: %r',
                      'ocr_' if need_ocr else '', e)
        if pdf_to_txt(upload, need_ocr):
            ext = '.txt'
        else:
            raise

    # Run task to keep the record
    from portal.tasks import update_PDFUploadMonitor
    update_PDFUploadMonitor(upload, need_ocr)

    docxpath = '.'.join(os.path.abspath(filename).split('.')[:-1]) + ext
    return docxpath


def doc_to_docx(filename):
    """
    Transcodes a .pdf file to docx via the EasyPdfCloud
    :param filename: path to locate the .pdf file
    :returns: path to the docx version of the file
    """
    upload = os.path.abspath(filename)
    doc_convert(upload)

    docxpath = '.'.join(os.path.abspath(filename).split('.')[:-1]) + '.docx'
    return docxpath


def contentsdecode(text):
    found_encoding = chardet.detect(text)['encoding']
    dec_contents = text.decode(found_encoding or 'utf-8')
    return dec_contents


def filedecode(filename):
    """
    Determines encoding of a file, and outputs utf-8 encoded plaintext
    contents
    :param filename: path to locate the file
    :returns: plaintext contents of the file
    """
    with open(filename, 'rb') as f:
        file_contents = f.read()
        return contentsdecode(file_contents)


class InvalidDocumentTypeException(Exception):
    pass


def document2sentences(document, filename, extension):
    """
    Selects the appropriate method for handling an uploaded document
    Returns a list of sentences in the format:
        [('text of sentence1', {formatting_dict}, {style_dict}), ...]
    """
    from richtext.importing import conversion_handler

    converter = conversion_handler(extension)
    success, payload = converter.process(document, filename)

    if not success:
        msg = payload
        raise InvalidDocumentTypeException(msg)

    sentences = payload
    return sentences

def pdf_convert(input_filename, ocr):
	"""
	Given in file name, check if ocr is needed
	If so, used ocrmypdf to add text layer
	then convert to docx
	"""

	#if ocr:
	pdf_ocr(input_filename)
	
	output_filename = '.'.join(os.path.abspath(input_filename).split('.')[:-1]) + '.docx'

	# convert pdf to docx
	cv = Converter(input_filename)
	cv.convert(output_filename, start=0, end=None)
	cv.close()

	return output_filename


def pdf_ocr(input_filename):

    args = ['ocrmypdf', '--skip-text', '--output-type', 'pdf', input_filename, input_filename]
    pp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = pp.communicate()

    if pp.returncode:
        logging.error(err.strip())
    else:
        logging.info(out.strip())

def doc_convert(input_filename):
    output_directory = os.path.dirname(input_filename)
    subprocess.call(['soffice', '--headless', '--convert-to', 'docx', '--out-dir', output_directory, input_filename])
