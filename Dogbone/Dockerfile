# Use the default python image
FROM python:3.6-slim

ADD prod_requirements.txt /

# 
RUN set -ex && \
	apt-get update &&\
	DEPS="\
	docx2txt \
	gfortran \
	g++ \
	ghostscript \
	icc-profiles-free \
	libreoffice \
	liblapack-dev \
	libffi-dev \
	libjpeg-dev \
	liblept5 \
	libopenblas-dev \
 	libpq-dev \
	libxml2 \
	libxml2-dev \
 	libxslt1-dev \
 	pngquant \
	postgresql-client \
	python3-cffi \
	python3-dev \
	python3-pip \
	python3-distutils \
	python3-reportlab \
	python3-pkg-resources \
	python3-psycopg2 \
	qpdf \
	tesseract-ocr \
	tk \
	ocrmypdf \
	python3-virtualenv \
	unpaper \
	zlib1g \
	" && \
	apt-get install -y --no-install-recommends $DEPS && \ 
	python3 -m venv venv && \ 
	/venv/bin/pip install --upgrade pip && \ 
	/venv/bin/pip install --no-cache-dir -r /prod_requirements.txt &&\
	/venv/bin/python -m nltk.downloader book

RUN mkdir /dogbone/
WORKDIR /dogbone/
ADD . /dogbone/

ENV VIRTUAL_ENV /venv
ENV PATH /venv/bin:$PATH
ENV PYTHONPATH /venv/bin/python
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

EXPOSE 8000

CMD ["/venv/bin/gunicorn", "--bind", ":8000", "--workers", "3", "dogbone.wsgi:application"]