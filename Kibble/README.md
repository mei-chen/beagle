# kibble
Clean up raw data and prepare the sentence spreadsheet for labelling

## Manual deployment

### Install additional required software
```
sudo apt-get update
sudo apt-get install nginx, supervisor
sudo apt-get install python-virtualenv
sudo apt-get install unzip libreoffice
```

### Install wkhtmltopdf
```
cd ~
sudo wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
sudo tar xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
sudo rm wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
sudo ln -s ~/wkhtmltox/bin/wkhtmltopdf /usr/bin/wkhtmltopdf
```

### Clone the repo
```
cd /var/www && git clone git@github.com:BeagleInc/kibble.git kibble
```

### Create virtualenv
```
virtualenv2 /var/www/venv
```
and activate it
```
source /var/www/venv/bin/activate
```

### Install requirements
```
pip install -u pip
pip install -r /var/www/kibble/requirements.txt
python -m spacy download en_core_web_md
```

### Create local settings with necessary parameters:
```
cd /var/www/kibble/kibble/app_settings && touch local_settings.py
```

And put your values (If you want to avoid AWS_SECRET_ACCESS_KEY managing, you may setup AIM for this server)
```
SENDGRID_API_KEY = 'your sendgrid api key'
AWS_SECRET_ACCESS_KEY = 'access key'
AWS_ACCESS_KEY_ID = 'key id'
AWS_STORAGE_BUCKET_NAME = 'bucket name'
AWS_S3_REGION_NAME = 'region'
DROPBOX_APP_KEY = 'your dropbox app key'
DROPBOX_APP_SECRET = 'your dropbox app secret'
```

### Setup enviroment settings
```
cd /var/www/kibble/ && touch .env
```

And put there following:
```
DOMAIN="your domain"
NLTK_DATA="/var/lib/nltk-data/"
SESSION_SECRET="session secret "
REDIS_URL="redis://redis url:port/0"
SOCKET_DOMAIN="1"
SYSLOG="1"
DATABASE_URL="postgres://postgres url:port/db name"
EMAIL_BACKEND="smtp"
BROKER_URL="broker url"
STATIC_ASSET_PATH="/var/www/static/"
DJANGO_DEBUG="1"
OCR_BUCKET="bucket name"
```

### Setup socket server
```
cd /var/www/kibble/realtime/node/ && npm install
```

### Make simlink to static folder
```
ln -s /var/www/kibble/static /var/www/static
```

### Setup and build frontend
```
cd /var/www/kibble/portal/static/js/src && npm install && npm run dist
cd /var/www/kibble && ./manage.py collectstatic && mv /var/www/kibble/collectstatic/admin /var/www/static && rm -r /var/www/kibble/collectstatic
```

### Run migrations and load basic relatedness models

```
cd /var/www/kibble/ && ./manage.py migrate
```
And load models
```
cd /var/www/kibble/ && ./manage.py loaddata analysis/fixtures/initial_data.json
```


### Create config files for supervisor
```
cd /etc/supervisor/conf.d
```

and create files with following content:
celery_beat.conf:
```
[program:celery_beat]
user=root ;
command=/var/www/venv/bin/celery -A kibble beat --loglevel=INFO --pidfile=/tmp/celery_beat_kibble.pid
directory=/var/www/kibble ;
stdout_logfile=/var/www/logs/celery_beat_stdout.log ;
stderr_logfile=/var/www/logs/celery_beat_stderr.log ;
stdout_logfile_maxbytes=10MB ;
stderr_logfile_maxbytes=10MB ;
```
celery.conf:
```
[program:celery]
user=www-data ;
command=/var/www/venv/bin/celery -A kibble worker -l info --time-limit=7200
directory=/var/www/kibble ;
stdout_logfile=/var/www/logs/celery_stdout.log ;
stderr_logfile=/var/www/logs/celery_stderr.log ;
stdout_logfile_maxbytes=10MB ;
stderr_logfile_maxbytes=10MB ;
```
gunicorn.conf:
```
[program:gunicorn]
user=www-data ;
command=/var/www/venv/bin/gunicorn kibble.wsgi:application --bind 127.0.0.1:8000 --log-syslog --log-syslog-facility daemon --log-syslog-to unix:///dev/log#dgram --log-level info --worker-class eventlet --timeout 60  --workers 6
directory=/var/www/kibble ;
stdout_logfile=/var/www/logs/gunicorn_stdout.log ;
stderr_logfile=/var/www/logs/gunicorn_stderr.log ;
stdout_logfile_maxbytes=10MB ;
stderr_logfile_maxbytes=10MB 
```
node_notifications.conf:
```
[program:node_notifications]
user=www-data ;
command=node server.js --syslog
directory=/var/www/kibble/realtime/node ;
stdout_logfile=/var/www/logs/node_stdout.log ;
stderr_logfile=/var/www/logs/node_stderr.log ;
stdout_logfile_maxbytes=10MB ;
stderr_logfile_maxbytes=10MB ;
```
Then run:
```
sudo supervisorctl
reload
```

To ensure that services up and running use this command inside supervisorctl:
```
status
```

### Setup nginx
You may adjust this config for your nginx server

```
upstream app_servers {
    server 127.0.0.1:8000;
}

upstream socket_nodes {
    ip_hash;
    server 127.0.0.1:4000;
}

upstream flower_server {
    server 127.0.0.1:5555;
}

server {
    listen 80;
    listen [::]:80;

    listen 443 ssl http2;

    server_name YOUR_SERVER_NAME;
    charset     utf-8;

    ###########################################################################
    ##
    ##  SSL Settings
    ##
    ###########################################################################

    ssl_certificate_key /PATH/TO/SSL/KEY;
    ssl_certificate /PATH/TO/SSL/CRT;
    ssl_trusted_certificate /PATH/TO/SSL/CRT;
    ssl_dhparam /PATH/TO/SSL/DHPARAM;

    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:AES256+EECDH:AES256+EDH'; # 'AES256+EECDH:AES256+EDH:!aNULL';
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_session_cache shared:SSL:10m;
    ssl_prefer_server_ciphers on;
    ssl_session_timeout 5m;

    if ($ssl_protocol = "") {
        rewrite ^ https://$server_name$request_uri? permanent;
    }

    add_header Strict-Transport-Security "max-age=63072000; includeSUBDOMAINs; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    client_max_body_size 75M;   # adjust to taste

    ###########################################################################
    ##
    ##  Location Settings
    ##
    ###########################################################################

    location / {
        proxy_pass         http://app_servers;
        proxy_redirect     off;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host $server_name;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 180s;
}

    location /static/ {
        autoindex off;
        alias /var/www/static/;
    }

    location /media/ {
        autoindex off;
        alias /var/www/kibble/uploads/;
    }

    location /socket.io/ {
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_pass http://socket_nodes;
    }

    location /flower/ {
        rewrite ^/flower/(.*)$ /$1 break;

        auth_basic "Restricted Access";
        auth_basic_user_file   /etc/nginx/htpasswd.users;
        proxy_set_header Authorization "";
        proxy_hide_header Authorization;

        proxy_pass http://flower_server;

        proxy_set_header        Host $host;
        proxy_set_header        X-Real-IP $remote_addr;
        proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header        X-Forwarded-Proto $scheme;
        proxy_set_header        X-Forwarded-Host $http_host;
    }

    location /flower/static {
        alias  /var/www/venv/lib/python2.7/site-packages/flower/static;
    }
}

```

And restart nginx

## Running in Dev

### Configure Dev envirnoment
- Create the file `local_settings.py` in the `app_settings/` directory, where the file contents include:
    - `DEBUG = True`
    - `HOT_LOAD = True`
- Create the file `secret.yml` in the ` ansible/vars/` directory, where the file contents include:

```
AWS_SECRET_ACCESS_KEY: ... (if you omit this and 3 below files will be saved locally)
AWS_ACCESS_KEY_ID: ...
AWS_STORAGE_BUCKET_NAME: ...
AWS_S3_REGION_NAME: ...
DROPBOX_APP_KEY: ...
DROPBOX_APP_SECRET: ...
GOOGLE_DRIVE_CLIENT_ID: ...
GOOGLE_DRIVE_CLIENT_SECRET: ...
SENDGRID_API_KEY: [required]
db_password: ...
public_key: ~/.ssh/<your_rsa>.pub
superuser_username: [required]
superuser_password: [required]
```

### Provisioning
- Install [Ansible](http://docs.ansible.com/ansible/intro_installation.html)
- `$ vagrant up`
- `$ vagrant provision`

### Install wkhtmltopdf
Will be moved to automatic ansible task later
```
vagrant up
vagrant ssh
cd ~
sudo wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
sudo tar xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
sudo rm wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
sudo ln -s ~/wkhtmltox/bin/wkhtmltopdf /usr/bin/wkhtmltopdf
```

### Relatedness models
If needed initial relatedness models, run:
- `$ vagrant up`
- `$ vagrant ssh`
- `$ cd /srv/kibble`
- `$ source ../venv/bin/activate`
- `$ python manage.py loaddata analysis/fixtures/initial_data.json`

_Convenience one-liner:_ `cd /srv/kibble && source ../venv/bin/activate && python manage.py loaddata analysis/fixtures/initial_data.json`

### Install spacy model
- `$ vagrant up`
- `$ vagrant ssh`
- `$ cd /srv/kibble`
- `$ source ../venv/bin/activate`
- `$ python -m spacy download en_core_web_md`

_Convenience one-liner:_ `cd /srv/kibble && source ../venv/bin/activate && python -m spacy download en_core_web_md`

### Django server
- `$ vagrant up`
- `$ vagrant ssh`
- `$ cd /srv/kibble`
- `$ source ../venv/bin/activate`
- `$ python manage.py createsuperuser`
- `$ python manage.py runserver 0.0.0.0:8001`
- Login to admin as socket requires a session_key, which is generated by a logged in user.

_Convenience one-liner:_ `cd /srv/kibble && source ../venv/bin/activate && python manage.py runserver 0.0.0.0:8001`

### Socket server
In new terminal run:
- `$ vagrant ssh`
- `$ cd /srv/kibble/realtime/node`
- `$ npm install`
- `$ node server.js`

_Convenience one-liner:_ `cd /srv/kibble/realtime/node && node server.js`

### Celery beat
In new terminal run:
- `$ vagrant ssh`
- `$ cd /srv/kibble`
- `$ source ../venv/bin/activate`
- `$ celery -A kibble beat -l info`

_Convenience one-liner:_ `cd /srv/kibble && source ../venv/bin/activate && celery -A kibble beat -l info`

Note: required for enabling the online cloud folder watcher (otherwise optional)

### Celery worker
In new terminal run:
- `$ vagrant ssh`
- `$ cd /srv/kibble`
- `$ source ../venv/bin/activate`
- `$ celery -A kibble worker -l info --discard`

_Convenience one-liner:_ `cd /srv/kibble && source ../venv/bin/activate && celery -A kibble worker -l info --discard`

### Compile front end.
Outside vagrant environment
- `$ cd portal/static/js`
- `$ npm install`
- `$ npm run dist` for js file.
    - Or for hot reload:
    - `$ npm start`

## Deploy on AWS
- Check that a proper AMI exists in the region (if not, create an Ubuntu one)
    - For `us-west-2` (Oregon) use the following: `ami-66880e06`
    - For `ca-central-1` (Canada) use the following: `ami-ff902d9b`
- Edit `ansible/vars/base.yml` and set the proper `ami_id` and the `region`
- `$ sudo pip install boto`
- `$ sudo pip install awscli`
- `$ aws config` and fill in AWS credentials (found in IAM)
- Identify the ssh key registered in github, or generate and add a new one:
    - https://help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/
    - Replace `<your_rsa>` below with the name of this key
- Fill the AWS credentials and ssh key in `ansible/vars/secret.yml`

```
AWS_STORAGE_BUCKET_NAME: ...
AWS_S3_REGION_NAME: ...
DROPBOX_APP_KEY: ...
DROPBOX_APP_SECRET: ...
GOOGLE_DRIVE_CLIENT_ID: ...
GOOGLE_DRIVE_CLIENT_SECRET: ...
SENDGRID_API_KEY: ...
db_password: ...
public_key: ~/.ssh/<your_rsa>.pub
superuser_username: ...
superuser_password: ...
env: ...
ami_id: ...
region: ...
```

- `$ ssh-add ~/.ssh/<your_rsa>`
- `$ cd ansible && ansible-playbook deploy.yml -e "env=deploy"` (for the instance called __"kibble-deploy"__)


## Feature Structure

### Local upload

Uploading files from local storage to create new batch based on uploaded files or add to existed batch

#### Front-end:
- portal/static/js/src/LocalFolder
- portal/static/js/src/base/rexux/modules/files.js
#### Back-end:
- Models: portal/models.py:Batch, portal/models.py:File
- aditional logic: portal/models.py:make_upload_path
#### API
- portal/api/viewsets.py:FileAPI
- routers: portal/api/router.py


### Batch Management

Displays total list of existing batches

#### Front-end
- portal/static/js/src/BatchManagement
- base/rexux/modules/batches.js
#### Back-end
- Models: portal/models.py:Batch,
#### API
- portal/api/viewsets.py:BatchAPI
- routers: portal/api/router.py


### Project Management

All current (and archived) projects and controls to manage batches for projects, editing, archiving

#### Front-end:
- portal/static/js/src/ProjectManagement
- portal/static/js/src/base/rexux/modules/batches.js
- portal/static/js/src/base/rexux/modules/projects.js
#### Back-end:
- Models: portal/models.py:Project, portal/models.py:ProjectArchive, portal/models.py:Batch
- tasks: portal/tasks.py:compress_project
#### API:
- portal/api/viewsets.py:ProjectAPI, portal/api/viewsets.py:BatchAPI
- routers: portal/api/router.py

### OCR

Process files that requires OCR. Integrades 3rd party services to make OCR.

#### Front-End:
- portal/static/js/src/OCR
- portal/static/js/src/base/rexux/modules/batches.js
- portal/static/js/src/base/rexux/modules/files.js
- portal/static/js/src/base/rexux/modules/documents.js
#### Back-end:
- models: portal/models.py:File, document/models.py:Document
- tasks: document/tasks.py:do_ocr
#### API:
- document/api/viewsets.py:OCRAPIReplace, document/api/viewsets.py:OCRAPICreate
- routers: document/api/router.py
- downloading docs: document/views.py:download_batch_documents, document/urls.py
- easyPDF integration: utils/EasyPDFCloudAPI
- justOCR integration: utils/justocr

### Format Converting

Convert files from batch to processable format.

#### Front-end
- portal/static/js/src/FormatConverting
- portal/static/js/src/base/rexux/modules/batches.js
- portal/static/js/src/base/rexux/modules/projects.js
- portal/static/js/src/base/rexux/modules/conversion.js
- portal/static/js/src/base/rexux/modules/documents.js
#### Back-end:
- models: portal/models.py:File, document/models.py:Document
- tasks: document/tasks.py:convert_file
- utils: utils/conversion.py
#### API:
- document/api/viewsets.py:ConvertAPI
- routers: document/api/router.py
- downloading docs: document/views.py:download_batch_documents, document/urls.py


### Cleanup Document

Apply diffrent cleanup tools to processed by Format converting document.

#### Front-end
- portal/static/js/src/CleanupDocument
- portal/static/js/src/base/rexux/modules/cleanup.js
- portal/static/js/src/base/rexux/modules/tools.js
- portal/static/js/src/base/rexux/modules/documents.js
#### Back-end:
- models: document/models.py:Document, document/models.py:DocumentTag
- signal processors: document/models.py:file_cleanup
- tasks: document/tasks.py:cleanup_document
- cleanup tools: document/models.py:Document, utils/cleanup.py
#### API:
- document/api/viewsets.py:CleanupDocumentAPI, document/api/viewsets.py:CleanupDocumentToolsAPI
- routers: document/api/router.py
- downloading docs: document/views.py:download_batch_documents, document/urls.py


### Sentence Splitting

Splitt cleaned documents into sentences (Beagle's splitting sentence API integration)/
Only documents with created DocumentTag (i.e. processed by at least one cleanup tool) is available for spitting.

#### Front-end
- portal/static/js/src/SentenceSplitting
- portal/static/js/src/base/rexux/modules/documents.js
#### Back-end:
- models: document/models.py:Document, document/models.py:Sentence
- tasks: document/tasks.py:sentence_splitting
#### API:
- document/api/viewsets.py:SentenceAPI
- routers: document/api/router.py
- downloading sentences: document/tasks.py:zip_csvs, document/urls.py
- API integration: utils/sentence_splitting/api.py


### RegEx

Managing regular expressions to analyse existing sentences.
Also applying regex to choosen batch and downloading csv report is available.

#### Front-end
- portal/static/js/src/RegEx
- portal/static/js/src/base/rexux/modules/batches.js
- portal/static/js/src/base/rexux/modules/regexes.js
- portal/static/js/src/base/rexux/modules/reports.js
#### Back-end:
- models: analysis/models.py:RegEx, analysis/models.py:Report
- tasks: analysis/tasks.py:regex_apply
#### API:
- analysis/api/viewsets.py:RegExAPI, analysis/api/viewsets.py:RegExApplyAPI, analysis/api/viewsets.py:ReportAPI
- routers: analysis/api/router.py
- downloading reports: document/urls.py
