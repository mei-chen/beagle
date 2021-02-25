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


REMOTES = {
    'master': {
        'host': ['kibble.beagle.ai'],
        'user': 'ubuntu',
        'identity': 'staging_beagle_key.pem',
        'git_branch': 'master'
    }
}


def remote(environment='master', local=False):
    if not environment or environment not in REMOTES:
        print(red('Environment not found'))
        abort('Aborting')

    env.user = REMOTES[environment]['user']
    env.hosts = REMOTES[environment]['host']
    if local:
        env.key_filename = os.path.join(IDENTITY_KEY_DIR, REMOTES[environment]['identity'])
    env.env_dict = REMOTES[environment]
    env.environment = environment


@contextmanager
def source_virtualenv():
    with prefix('source ' + os.path.join(VENV_DIR, 'bin/activate')):
        yield


def git_pull(comittish):
    run('git fetch')
    run('git reset --hard %s' % comittish)
    run('git checkout %s' % env.env_dict['git_branch'])
    run('git pull') # If switching branches need to run git pull


#################### <Django & Dependencies> ####################

def update_packages():
    with settings(warn_only=True):
        result = run('pip install --upgrade pip -r requirements.txt')

        if result.failed:
            print(red('Something went wrong during pip install'))
            abort('Aborting.')


def clean_pyc():
    run('echo "pyc files"')
    run('find . -name "*.pyc"')
    run('find . -name "*.pyc" -exec rm -rf {} \;')
    run('echo "pycs deleted"')


def django_manage(command):
    with settings(warn_only=True):
        return run('./manage.py %s' % (command))


def django_migrate():
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

#################### </Django & Dependencies> ####################


#################### <Services> ####################

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

#################### </Services> ####################




#################### <NPM> ####################

def install_notification_server_packages():
    with cd('realtime/node'):
        result = run('npm install --quiet')


def npm_compile():
    with cd('portal/static/js'):
        with shell_env(REACT_ENV=env.environment):
            run('npm install --quiet')
            run('npm run dist')


def npm_delete_compiled():
    with settings(warn_only=True):
        with cd('portal/static/js'):
            run("rm -rf build")
            run("rm -rf node_modules")


def clean_npm_temp_files():
    with settings(warn_only=True):
        sudo('rm -rf /tmp/npm-*')

#################### </NPM> ####################



#################### <Deploy> ####################
def send_email_admins(subject, level='INFO'):
    pass


def deploy(comittish='FETCH_HEAD', reset_npm_packages=False):
    with cd(os.path.join(ROOT_DIR, 'kibble')):
        # Update code
        git_pull(comittish)

        with source_virtualenv():
            # Install dependencies in requirements.txt
            update_packages()

            # Install notification server dependencies
            install_notification_server_packages()

            if reset_npm_packages:
                # Cleanup react
                npm_delete_compiled()

            # Build react
            npm_compile()

            # Cleanup npm
            clean_npm_temp_files()

            # Move static files
            django_collect_static()

            # Cleanup py
            clean_pyc()

            # Migrate DB
            django_migrate()

            # Restrat services
            services_stop()
            services_start()
#################### </Deploy> ####################
