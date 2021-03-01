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

# .env
import dotenv






ROOT_DIR = '/srv/'
IDENTITY_KEY_DIR = '~/.ssh/'
VENV_DIR = '%s/venv/' % ROOT_DIR
APP_NAME = 'Rufus'

env.dotenv_path = '%s%s/.env' % (ROOT_DIR, APP_NAME)
env.use_ssh_config = True
env.forward_agent = True

REMOTES = {
    'westpac': {
        'host': ['westpac-rufus.beagle.ai'],
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

def restart_supervisor():
    run('supervisorctl restart all')

def services_reload():
    result = run('supervisorctl reload')

    if result.failed:
        print(red('Could not reload supervisor'))
        send_email_admins("Could not reload supervisor", "ERROR")

#################### </Services> ####################




#################### <Deploy> ####################
def send_email_admins(subject, level='INFO'):
    pass


def config(action=None, key=None, value=None):
    """Manage project configuration via .env

    e.g: fab config:set,<key>,<value>
         fab config:get,<key>
         fab config:unset,<key>
         fab config:list
    """
    run('touch %(dotenv_path)s' % env)

    with source_virtualenv():
        command = dotenv.get_cli_string(env.dotenv_path, action, key, value)
        run(command)


def deploy(comittish='FETCH_HEAD', reset_npm_packages=False):
    with cd(os.path.join(ROOT_DIR, 'Rufus')):
        # Update code
        git_pull(comittish)

        with source_virtualenv():
            # Install dependencies in requirements.txt
            update_packages()

            # Move static files
            django_collect_static()

            # Cleanup py
            clean_pyc()

            # Migrate DB
            django_migrate()

            # Restrat services
            restart_supervisor()
#################### </Deploy> ####################
