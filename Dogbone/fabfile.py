# Python
import os
import json
import time
import requests
from contextlib import contextmanager
from StringIO import StringIO

# fabric
from fabric.colors import green, red
from fabric.api import local, settings, abort, run, cd, env, prefix, shell_env, sudo
from fabric.contrib.console import confirm
from fabric.operations import put

env.use_ssh_config = True
env.forward_agent = True

ROOT_DIR = '/var/www'
IDENTITY_KEY_DIR = '~/.ssh/'
VENV_DIR = '%s/venv/' % ROOT_DIR

# Rufus processing email file path
RUFUS_PROCESSING_SCRIPT_PATH = '/home/ubuntu/%s'
RUFUS_PROCESSING_SCRIPT_FILENAME = 'process_email.py'

RUFUS_ALIASES_PATH = '/etc/aliases'
RUFUS_ALIASES_TEMPLATE_PATH = 'dogbone/conf/rufus/aliases.template'

ADMIN_EMAILS = (
    'cian@beagle.ai',
    'iulius@sniffthefineprint.com',
)

POST_DEPLOY_REQUEST_COUNT = 6  # number of requests
POST_DEPLOY_MAX_WAIT = 16      # seconds

REMOTES = {
    'staging': {
        'host': 'staging.beagle.ai',
        'user': 'ubuntu',
        'identity': 'staging_beagle_key.pem',
        'git_branch': 'staging'
    },

    'dev': {
        'host': 'dev.beagle.ai',
        'user': 'ubuntu',
        'identity': 'dev_beagle_key.pem',
        'git_branch': 'dev'
    },

    'master': {
        'host': 'beta.beagle.ai',
        'user': 'ubuntu',
        'identity': 'beta_beagle_key.pem',
        'git_branch': 'master'
    },

    'westpac': {
        'host': 'westpac.beagle.ai',
        'user': 'ubuntu',
        'identity': 'beta_beagle_key.pem',
        'git_branch': 'dev'
    },

    'tr': {
        'host': 'tr-beta.beagle.ai',
        'user': 'ubuntu',
        'identity': 'beta_beagle_key.pem',
        'git_branch': 'dev'
    }
}

@contextmanager
def source_virtualenv():
    with prefix('source ' + os.path.join(VENV_DIR, 'bin/activate')):
        yield

def test():
    with settings(warn_only=True):
        result = local("./manage.py test --noinput")

    if result.failed and not confirm("Tests failed. Continue anyway?"):
        print(red('Failed.'))
        abort("Aborting at user request.")

    else:
        print(green('Passed.'))

def git_pull(comittish):
    run('git fetch')
    run('git reset --hard %s' % comittish)
    run('git checkout %s' % env.env_dict['git_branch'])
    run('git pull') # If switching branches need to run git pull

def remote(environment='dev', local=False):
    if environment is None or environment not in REMOTES:
        print(red('Environment not found'))
        abort('Aborting')

    env.user = REMOTES[environment]['user']
    env.hosts = [REMOTES[environment]['host']]
    if local:
        env.key_filename = os.path.join(IDENTITY_KEY_DIR, REMOTES[environment]['identity'])
    env.env_dict = REMOTES[environment]
    env.environment = environment


def cleanup():
    """ Tries to free some space by removing logs, temporary files etc. """

    with settings(warn_only=True):
        # Remove all celery logs (except currently used ones)
        run('rm celery.log.*')
        run('rm celery_beat.log.*')

        # Remove legacy temporary documents which should have been removed after processing
        # (but don't touch directories!)
        run('rm dogbone/media/*')

        # Remove other temporary files and directories
        run('rm -rf tmp/*')


def send_email_admins(subject, level='INFO'):
    with settings(warn_only=True):
        for email in ADMIN_EMAILS:
            result = run('echo "From: serverstuff@beagle.ai\nSubject: [BEAGLE:%s:%s] - %s" | sendmail %s' %
                         (level, env.environment, subject, email))

            if result.failed:
                print(red('Could not send email to: %s' % email))

# Django
def django_manage(command):
    with settings(warn_only=True):
        return run('./manage.py %s' % (command))

def django_syncdb():
    result = django_manage('syncdb')

    if result.failed:
        print(red('Syncdb could not be applied'))
        send_email_admins("Syncdb failed", "ERROR")
        abort('Aborting.')

def django_test_migrate():
    result = django_manage('migrate --all --no-initial-data --db-dry-run')

    if result.failed:
        print(red('The test migrations could not be applied'))

def django_migrate():
    # result = django_manage('migrate --all --no-initial-data --fake')

    result = django_manage('migrate')
    if result.failed:
        print(red('The migrations could not be applied'))
        send_email_admins("Check migration failed", "ERROR")
        abort('Aborting.')

def django_collect_static():
    result = django_manage('collectstatic --noinput')

    if result.failed:
        print(red('Collect static not completed'))
        send_email_admins("Check migration failed", "ERROR")
        abort('Aborting.')

# Services

def gunicorn_stop():
    run('supervisorctl stop gunicorn')

def gunicorn_start():
    run('supervisorctl start gunicorn')

def gunicorn_restart():
    run('supervisorctl restart gunicorn')

def celery_stop():
    run('supervisorctl stop celery')

def celery_start():
    run('supervisorctl start celery')

def celery_restart():
    run('supervisorctl restart celery')

def celery_beat_stop():
    run('supervisorctl stop celery_beat')

def celery_beat_start():
    run('supervisorctl start celery_beat')

def celery_beat_restart():
    run('supervisorctl restart celery_beat')

def node_start():
    run('supervisorctl start node_notifications')

def node_stop():
    run('supervisorctl stop node_notifications')

def node_restart():
    run('supervisorctl restart node_notifications')

# React

def react_compile():
    with cd('portal/static/react'):
        with shell_env(REACT_ENV=env.environment):
            run('npm install --quiet')
            run('./rebuild_custom.sh')
            run('npm run build')

def react_delete_compiled():
    with settings(warn_only=True):
        with cd('portal/static/react'):
            run("rm -rf build")
            run("rm -rf node_modules")

# Cleanup

def clean_pyc():
    run('echo "pyc files"')
    run('find . -name "*.pyc"')
    run('find . -name "*.pyc" -exec rm -rf {} \;')
    run('echo "pycs deleted"')

def clean_npm_temp_files():
    with settings(warn_only=True):
        sudo('rm -rf /tmp/npm-*')

# Dependencies

def install_notification_server_packages():
    with cd('node_server'):
        result = run('npm install --quiet')

def update_packages():
    with settings(warn_only=True):
        result = run('pip install --upgrade pip -r requirements.txt')

        if result.failed:
            print(red('Something went wrong during pip install'))
            abort('Aborting.')

# Tasks

def post_deploy_test():
    wait = 1
    success = True
    for request_idx in range(POST_DEPLOY_REQUEST_COUNT):
        for host in env.hosts:
            print('Requesting GET %s' % host)
            response = requests.get('http://' + host)

            if response.status_code != 200:
                print(red('Request failed'))
                success = False
            else:
                print(green('Request succeeded'))
                success = True

            print('Waiting %s seconds' % wait)
            time.sleep(wait)

            wait *= 2
            if wait > POST_DEPLOY_MAX_WAIT:
                wait = POST_DEPLOY_MAX_WAIT

    if not success:
        print(red("This did not go as planned :("))
        send_email_admins("Post deploy tests failed", "ERROR")

    else:
        print(green("Deployment seems successful :)"))

def services_stop():
    node_stop()
    gunicorn_stop()
    celery_stop()
    celery_beat_stop()

def services_start():
    celery_start()
    gunicorn_start()
    node_start()
    celery_beat_start()

def services_reload():
    result = run('supervisorctl reload')

    if result.failed:
        print(red('Could not reload supervisor'))
        send_email_admins("Could not reload supervisor", "ERROR")

def deploy(comittish='FETCH_HEAD'):
    with cd(os.path.join(ROOT_DIR, 'dogbone')):
        # Update code
        git_pull(comittish)

        with source_virtualenv():
            # Install dependencies in requirements.txt
            update_packages()

            # Install notification server dependencies
            install_notification_server_packages()

            # Testing if migrations can be applied
            django_test_migrate()

            # Cleanup react
            # react_delete_compiled()

            # Build react
            react_compile()

            # Cleanup npm
            clean_npm_temp_files()

            # Move static files
            django_collect_static()

            # Cleanup py
            clean_pyc()

            # Migrate DB
            django_syncdb()
            django_migrate()

            # Restrat services
            services_stop()
            services_start()

            # Send success emails to admins
            send_email_admins("Deployment successful", "SUCCESS")



def reboot():
    with settings(warn_only=True):
        cmd = 'reboot'
        result = sudo(cmd)

        if result.failed:
            print(red('Something went wrong during %s' % cmd))

# Github

def download_github_file(github_url):
    """
    GitHub URL should be something similar to raw.github.com etc ...
    Example: https://raw.githubusercontent.com/BeagleInc/dogbone/staging/rufus/process_mail.py
    :param github_url:
    :return:
    """
    headers = {
        'Authorization': 'token %s' % os.environ['GITHUB_PERSONAL_ACCESS_TOKEN'],
        'Accept': 'application/vnd.github.v3.raw',
    }

    response = requests.get(github_url, headers=headers)
    return response.content

def list_github_folder(github_url):
    return json.loads(download_github_file(github_url))

def download_github_folder(github_url, destination_folder):
    item_list = list_github_folder(github_url)
    run('mkdir %s' % destination_folder)

    for item in item_list:
        if item['type'] == 'file':
            file_contents = download_github_file(item['_links']['self'])
            file_path = os.path.join(destination_folder, item['name'])
            put(StringIO(file_contents), file_path)

        elif item['type'] == 'dir':
            folder_path = os.path.join(destination_folder, item['name'])
            download_github_folder(item['_links']['self'], folder_path)






##################################################################################################################
#
# Rufus Related commands
#
##################################################################################################################


def rufus_generate_aliases(git_branch='dev'):
    github_url = 'https://api.github.com/repos/BeagleInc/dogbone/contents/%s?ref=%s' % (RUFUS_ALIASES_TEMPLATE_PATH, git_branch)

    print("GitHub URL for aliases.template: %s" % github_url)

    file_contents = download_github_file(github_url)
    print "Retrieved template: %s" % file_contents

    file_contents = file_contents.replace('{{ RUFUS_FOLDER }}', env.rufus_folder)
    file_contents = file_contents.replace('{{ ENVIRONMENT }}', env.environment)
    file_contents = file_contents.replace('{{ RUFUS_USER }}', 'ubuntu')

    print "Generated: %s" % file_contents

    result = put(StringIO(file_contents), RUFUS_ALIASES_PATH, use_sudo=True)

    if result.failed:
        print(red('Could not deploy rufus!'))
        send_email_admins("Could not deploy Rufus", "ERROR")

def rufus_download(path, git_branch='dev'):
    rufus_github_url = 'https://api.github.com/repos/BeagleInc/dogbone/contents/rufus?ref=%s' % git_branch
    download_github_folder(rufus_github_url, path)

def rufus_install_requirements():
    with cd(env.rufus_versioned_path):
        sudo('pip install -r requirements.txt')

def rufus_deploy():
    print(green('Deploying Rufus ...'))

    rufus_folder = 'rufus_%s' % time.time()
    env.rufus_folder = rufus_folder

    rufus_versioned_path = RUFUS_PROCESSING_SCRIPT_PATH % rufus_folder
    env.rufus_versioned_path = rufus_versioned_path

    rufus_download(rufus_versioned_path, git_branch=env.git_branch)
    rufus_generate_aliases(git_branch=env.git_branch)
    rufus_install_requirements()

    sudo("chmod 0777 /etc/aliases.db")
    sudo("newaliases")
    sudo("touch %s/rufus.log" % env.rufus_versioned_path)
    sudo("chmod -R 0777 %s" % env.rufus_versioned_path)

    postfix_reload()




