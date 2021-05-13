# What to do:

The “push\_files” script in this directory takes the public dns of the instance (as provided on the AWS site) as an argument, and uses scp to put the setup script, settings files, and ssh files for the github on the instance.  Then you should ssh in and run the setup\_script file (not sudo).

    push_files <publicdns>
    ssh -i “~/.ssh/<key>.pem” ubuntu@<publicdns>
    ./setup_script

The instance needs 4GB of memory and 16GB of storage.
# Understanding the script:

**Step 1**
Apt is the package manager for the OS.  The first few lines are adding things to its repository for later (postgres and npm), then we do apt update to get it all up-to-date.

**Step 2**
Install a bunch of dependencies, including:

- pip, the python package manager (pip), which we upgrade to the latest version on the next line
- venv <span style="color:blue">(It would be nice to use venv, as packaged with python3, but for now this is useless because we are still on virtualenv)</span>
- libpq-dev, which is needed for psycopg2 (which is in the kibble requirements.txt)
- postgresql, the database
- ngingx, a reverse proxy which sits in front of gunicorn. It handles what it can and passes the rest of the requests along.
- redis-server, a database
- nodejs, contains both npm and node
- supervisor, which will be used to launch the gunicorn and celery processes, and which will keep logs of their activity.
- unzip
- tesseract-ocr
- libreoffice
- xfonts stuff, needed for the latest version of wkhtmltopdf
- gunicorn, WSGI server for the frontend (installed with pip)
- virtualenv, the python virtual environment we are using for now (installed with pip)

The “-y” flag for the apt commands is “yes” for when it asks if you want to install.

**Step 3**
Install a tool called “wkhtmltopdf”.  Download the installer, depackage it, and remove it.

**Step 4**
Move some files around and manage their ownership:

- Change ownership and group of the /var/www directory so that linux lets us do stuff there.  We want our code there because it’s the directory that our server services expect to look in.
- Copy over the supervisor config files
- Copy over the nginx config file
- Make a directory for the supervisor log files to live in

**Step 5**
Clone the codebase and switch into the develop branch (which has the latest code).
Cloning the codebase is done with ssh to allow for key authentication which doesn't require the user to enter a password at the prompt.  The ssh key and corresponding config file are uploaded into ~/.ssh by the push_files script.

**Step 6**
Create our virtual environment and activate it.  Install the project requirements.

**Step 7**
<span style="color:red">Set the variables for the project.</span>

**Step 8**
Setup socket server

**Step 9**
Setup and build frontend files.  The static files are collected into /var/www/beagle/Kibble/static, with a symlink at /var/www/static.

**Step 10**
Set up the database. Check that the database settings match what is in /var/www/beagle/Kibble/kibble/app_settings/production_settings.py:

    DATABASES =  {
    'default':  {
    'ENGINE':  'django.db.backends.postgresql_psycopg2',
    'NAME':  'kibble',
    'USER':  'kibble',
    'PASSWORD':  'password',
    'HOST':  'localhost',
    'PORT':  '5432',
    }
    }

**Step 11**
Migrate and load relatedness models. !!!!!! NOTE THE JSON NEEDS TO BE UPDATED !!!!! for the delorean "lightweight glove" dropdown menu.

**Step 12**
Launch redis-server and supervisor processes.  Restart nginx.

**Step 13**
Set up superuser.

**Other Stuff**

Delorean should be launched on the same machine to provide the relatedness model for kibble.  Kibble looks for it on port 3000.  Create a delorean venv, put the "glove.50d.txt" file in the delorean directory, and install the delorean requirements and "python3 -m spacy download en\_core\_web_sm".  Launch "app.py" in a screen.

# Other Information
[This is an useful read](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-18-04)

**Issues Encountered Making the Script:**

_App and Environment Variables:_

- This isn't set up yet!

_Node:_

- Installing nodejs with apt provides both npm and node, and we can get whatever version we want by changing the version in the curl command.  It _only_ works with version 11!

_Database:_

- These steps weren't in the readme but they are necessary because you have to have the database running.

_Installing Torch:_

- On a .micro instance it hangs during the download because it doesn't have enough memory.  It will make it through this on a .small instance but it won't make it through the installation.  A .medium instance has enough memory. You can also use --no-cache-dir as a flag during the installation!

_Installing pip3:_

- I got a weird error that said it couldn’t install dependencies.  Killing the instance and starting a new one worked.

_pip3 install -r requirements.txt:_

- Don’t use sudo
- If it says “killed” at the end of the output then it stopped with an error, probably not enough memory.  Check /var/log/kern.log.
- "cython not found" - solved by upgrading pip
- Permissions error: check ownership of directory
- Out of space, need 16GB instance

_Cloning the code:_

- Don’t use sudo, it messes up the permissions
- Make sure your account has access first, by checking in the browser!
- There are [four git protocols](https://git-scm.com/book/en/v2/Git-on-the-Server-The-Protocols): local, ssh, https, and git.  Some syntax information is given [here](https://git-scm.com/docs/git-clone). The path for each protocol can be found on the github website, in a dropdown menu by the repo.  HTTPS is very easy for a person to use, but it is harder to set up automatic credentials.  Here we are using ssh with a key, so that it can be automatically authenticated and the script can run without user input.  The ssh key for the github account can be set up following [these instructions](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh).  The "add ssh key to agent" and "passphrase" bits are not important.  The ssh key should have permissions corresponding to chmod 400.  To set it up on the EC2 instance, only the private key is needed.  When ssh operations are performed, some settings are read.  The global settings are in /etc/ssh/ssh_config , but a config file can also be placed at ~/.ssh/config, for user settings which take precedence.  Here we add a rule for "Host github" which specifies: IdentityFile (path to key), IdentitiesOnly (yes), and StrictHostKeyChecking (no).  This tells the ssh protocol that for this host, this specific key should be used, and _only_ this key.  StrictHostKeyChecking=no prevents the host authentication message from appearing, which allows the script to run without input.

_Supervisor:_

- Make sure the directories and paths in the config files are correct, and that they exist!  Some mkdir might need to be done.  In this script, mkdir /var/www/logs is needed to prevent a .sock not found error in supervisor.
- Supervisor launches the celery tasks and gunicorn task through the commands specified in its config files.  The gunicorn task is the one that launches the django server.

_nginx:_

- Here we are configuring nginx as a "reverse proxy server".  There is useful documentation [here](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/).  This means that it takes requests from the http port (80), and passes them to port 8000 internally which is the application port that gunicorn is running django on.
- This is mostly handled by the config file at /etc/nginx/nginx.conf, which also specifies some includes: /etc/nginx/conf.d/\*.conf and /etc/nginx/sites-enabled/\*;
- This script removes the default file at /etc/nginx/sites-enabled/ to prevent those settings from interfering.

_Virtual environment:_

- venv is in .gitignore as “venv/” which ignores any directory with that name
- [https://www.infoworld.com/article/3239675/virtualenv-and-venv-python-virtual-environments-explained.html](https://www.infoworld.com/article/3239675/virtualenv-and-venv-python-virtual-environments-explained.html)
- For some reason the installations done with pip at the beginning of the script have to be done with sudo or the “virtualenv” command wont exist.
