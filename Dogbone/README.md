dogbone
=======

[![Circle CI](https://circleci.com/gh/BeagleInc/dogbone.svg?style=svg&circle-token=2d0654865581f878dd599ad39fc51bfae7353f2e)](https://circleci.com/gh/BeagleInc/dogbone)


Utils:
------

- Link to admin interface: [http://localhost:8000/adm/office](http://localhost:8000/adm/office)
- Run all the servers (the 4 terminals I always keep open):

    ```
    ~/dogbone $ ./manage.py runserver
    ```

    ```
    ~/dogbone $ celery -A dogbone worker --loglevel=INFO --discard
    ```

    ```
    ~/dogbone/node_server $ node server.js
    ```

    ```
    ~/dogbone/portal/static/react $ npm start
    ```

- How to migrate after a pull:

    ```
    $ python manage.py syncdb  # often not needed
    $ python manage.py migrate
    ```

- How to generate a migration after a model has been changed:

    ```
    $ python manage.py schemamigration --auto APPNAME
    # Now don't forget to add the new migration file to the commit
    ```

Install (on local machine):
---------------------------

This guide targets a Linux environment with a Ubuntu-family system (Ubuntu, Mint, ...):

1. Clone Github repo:

    ```
    $ git clone git@github.com:BeagleInc/dogbone.git
    ```

2. Postgresql:

    - Install:

        ```
        $ sudo apt-get install postgresql-9.3 postgresql-client-9.3 postgresql-contrib-9.3 postgresql-server-dev-9.3
        ```

    - Add user for yourself

        ```
        $ sudo -u postgres createuser -d "$(id -un)"
        ```
    - Add the database (if it doesn't already exist)

        ```
        $ createdb beagle
        ```

3. VirtualEnv:

    ```
    # Init virtual-environment
    $ virtualenv venv
    # Activate venv
    $ . venv/bin/activate
    # Leave a venv
    $ deactivate
    ```

4. Install requirements:

    ```
    $ sudo pip install -r requirements.txt
    ```
    - If you are using venv do not use 'sudo' or all libs will be installed globally.

5. NLTK:

    ```
    $ python -m nltk.downloader book
    ```

6. Redis:

    - Install:

        ```
        $ sudo apt-get install redis-server
        ```

7. Setup environment
    - Create .env

        ```
        $ vim .env
        ```

        - Add

          ```
          DATABASE_URL=postgres://%2Fvar%2Frun%2Fpostgresql/beagle
          REDIS_URL=redis://localhost:6379/1
          BROKER_URL=redis://localhost:6379/0

          HOT_LOAD=1

          AWS_ACCESS_KEY_ID=AKIAJJYNXM63VQWA7R5Q
          AWS_SECRET_ACCESS_KEY=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
          ```

8. Spawn celery worker

   ```
   $ celery -A dogbone worker --loglevel=INFO
   ```

    - To clear the task queue beforehand, use `--discard`

9. Run SocketIO:

    ```
    cd node_server
    npm install
    nodejs server.js
    ```

10. Run Django:

    ```
    python manage.py runserver
    ```

11. Run React:

    ```
    cd portal/static/react
    npm install
    npm start
    ```

12. Initialize database:

    - Run `python manage.py syncdb --noinput`
    - Run `python manage.py migrate`
        - Might fail because migrations are out of order, if so, comment out app `longerusernameandemail` from `dogbone\dogbone\app_settings\common_settings.py`
        - Run migration again which should work.
        - Uncomment `longerusernameandemail` and rerun migrations.

13. Potential problems:

    13.1. After installing the node modules on `portal/static/react` through `npm install` and attempting to start npm server through `npm start` (needed to serve JS files), following error might show up:
    ```
    sh: 1: node: not found
    npm ERR! weird error 127
    npm WARN This failure might be due to the use of legacy binary "node"
    ```
    - Run `sudo apt-get install nodejs-legacy` and run `npm start` again.

    13.2. If you got any errors about missing libs while attempting to start npm server through `npm start`, try to run `npm install` one more time.

14. Initialize the project for dev environment:

    ```
    python manage.py initdb
    python manage.py install_initsamples_to_existing_users
    python manage.py init_pretrained
    python manage.py install_pretrained
    ```

    - Also, you can create your own superuser by running:

    ```
    python manage.py createsuperuser
    ```

## Setup cloud watcher
To make cloud watcher work you need to complete following steps:

### Google Drive
1. Go to [Google API Console](https://console.developers.google.com/apis/) and
make your own project.
2. Search for "_Google Drive API_", select the entry, and click "_Enable_".
3. Select "_Credentials_" from the left menu, click "_Create Credentials_",
select "_OAuth client ID_".
4. Now, the product name and consent screen need to be set, so click
"_Configure consent screen_" and follow the instructions.
5. Select "_Application type_" to be "_Web application_"
(use the "_OAuth consent screen_" page if you want to further customize the app).
6. Don't forget to add `http://localhost:8000` to "_Authorized JavaScript origins_" and
`http://localhost:8000/account/google_drive_auth_callback` to
"_Authorized redirect URIs_" respectively (change the domain properly
if you use a non-local environment).
7. Find `GOOGLE_DRIVE_CLIENT_ID` and `GOOGLE_DRIVE_CLIENT_SECRET` options inside your environment's
admin panel (`http[s]://<DOMAIN>/adm/office/constance/config/`) and
set their values to "_Client ID_" and "_Client secret_" respectively
(copy and paste them from the app's "_Credentials_" page).

### Dropbox
1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps) and
make your own app (you may customize it a bit from the "_Branding_" page).
2. Don't forget to add `http://localhost:8000/account/dropbox_auth_callback`
(you may change it according to your environment domain) to "_OAuth 2_" -> "_Redirect URIs_".
3. Find `DROPBOX_APP_KEY` and `DROPBOX_APP_SECRET` options inside your environment's
admin panel (`http[s]://<DOMAIN>/adm/office/constance/config/`) and
set their values to "_App key_" and "_App secret_" (hidden by default) respectively
(copy and paste them from the app's "_Settings_" page).


--------------------------------------------------------------

Docker (for dev) [mostly outdated -- use the previous section]
--------------------------------------------------------------

1. Starting from the root of the Dogbone code, build the Docker image by
   running
   ```
   docker build -t="glifchits/dogbone:latest" .
   ```

2. if you run the command `docker images` then you should see
   "glifchits/dogbone" there

3. run the image with the command `./dev.sh`. This should mount your local
   `dogbone` app code directory into the Docker container. The Docker container
   will have your local code located in `/dogbone`.

4. in the Docker container, `cd /dogbone` and run `./docker_start.sh`. The app
   is now running inside the Docker container.

5. the Docker image is built to expose port 8000 inside the container by
   default. Find out which port the Docker runtime has mapped this container to
   (by running `docker ps`), then visit `localhost:{{docker-port}}` to see the
   app

6. Potential Problems
    - On running the `docker build -t="glifchits/dogbone:latest" .` command, the following error might show up:
    ```django.db.utils.OperationalError: FATAL:  the database system is starting up```.
        - If so, initialize a container instance through `docker run -it -v $(pwd):/docker -p 8000:8000 -p 4000:4000 -p 3000:3000 [IMAGE ID]` and attach to the container instance.
        - Run `/etc/init.d/postgresql start` and `service redis-server start`, give them a few seconds to start.
            - (Whenever a container is restarted, the postgresql server and redis-server should be restarted).
        - Run `python manage.py syncdb --noinput`
        - Run `python manage.py migrate`
            - Might fail because migrations are out of order, if so, comment out app `longerusernameandemail` from `dogbone\dogbone\commons.py`
            - Run migration again which should work.
            - Uncomment `longerusernameandemail` and rerun migrations.
    - After installing the node modules on `../portal/static/react` through `npm install` and attempting to start npm server through `npm start` (needed to serve JS files), following error might show up:
    ```
    sh: 1: node: not found
    npm ERR! weird error 127
    npm WARN This failure might be due to the use of legacy binary "node"
    ```

    - Run `sudo apt-get install nodejs-legacy` and run `npm start` again.

7. To initialize the project for the dev environment, run the following management commands.
    - Run a celery instance (`celery -A dogbone worker --loglevel=INFO`), and if run into the following error:
    ```
    Running a worker with superuser privileges when the
    worker accepts messages serialized with pickle is a very bad idea!

    If you really want to continue then you have to set the C_FORCE_ROOT
    ```
    - Run `export C_FORCE_ROOT="true"` and restart celery.
    - Connect to a new terminal through `docker exec -it [CONTAINER_ID] bash` and run following management commands:
        - `python manage.py initdb`
        - `python manage.py install_initsamples_to_existing_users`
        - `python manage.py init_pretrained`
        - `python manage.py install_pretrained`
    - Run `python manage.py runserver 0.0.0.0:8000` to start the webserver and can be viewed on `http://localhost:8000/`



Default credentials on this image: `cian@sniffthefineprint.com` : `topdog`


(I run Docker on Mac, so step 5 may be missing some information. Mac users
don't get `localhost` since the Docker runtime is tunnelled through a Linux
virtual machine and we have to go through the VM's IP address). (This has been fixed in the most recent docker instance, `localhost` now works.)


Running Tests
-------------

Run all tests:

	# From the root of the project
    python manage.py test


Example of specific test run:

    python manage.py test nlplib.tests.test_extref
