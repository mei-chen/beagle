#
# constants
#

SHELL=/bin/bash

PROJECT_NAME=kibble
BIND_TO=0.0.0.0
RUNSERVER_PORT=8000
DEVSERVER_PORT=8001
MAILSERVER_PORT=1025
SETTINGS=kibble.settings
REDIS_BROKER_URL=redis://localhost:6379/0
TEST_SETTINGS=kibble.app_settings.test_settings
TEST_APP?=

PYTHONPATH=$(CURDIR)

MANAGE_PREFIX= PYTHONPATH=$(PYTHONPATH) DJANGO_SETTINGS_MODULE=$(SETTINGS)
MANAGE_CMD=./manage.py
MANAGE= PYTHONPATH=$(PYTHONPATH) DJANGO_SETTINGS_MODULE=$(SETTINGS) $(MANAGE_CMD)


-include Makefile.def

#
# end of constants
#

#
# targets
#

.PHONY: run worker realtime react-dev syncdb initproject dumpdata shell djangotest collectstatic dist clean manage migrate only_migrate init_migrate

run:
	@echo Starting $(PROJECT_NAME)...
	BROKER_URL=$(REDIS_BROKER_URL) $(MANAGE) runserver $(BIND_TO):$(RUNSERVER_PORT)

dev:
	@echo Starting $(PROJECT_NAME)...
	BROKER_URL=$(REDIS_BROKER_URL) $(MANAGE) runserver $(BIND_TO):$(DEVSERVER_PORT)

worker:
	BROKER_URL=$(REDIS_BROKER_URL) celery -B -A kibble worker -l info

realtime:
	(cd realtime/node && npm start)

react-dev:
	(cd portal/static/js && npm start)

syncdb:
	@echo Syncing...
	$(MANAGE) syncdb --noinput
	$(MANAGE) migrate --noinput
	@echo Done

initproject: syncdb
	$(MANAGE) migrate --noinput

dumpdata:
	$(MANAGE) dumpdata --indent 2 --exclude admin.logentry --exclude sessions --exclude auth --exclude contenttypes --exclude core.loginattempt >dump.json

shell:
	@echo Starting shell...
	$(MANAGE) shell

djangotest:
	mkdir -p /tmp/kibble_test_files
	TESTING=1 PYTHONWARNINGS=ignore $(MANAGE) test --settings=$(TEST_SETTINGS) $(TEST_APP) -v 2
	rm -rf /tmp/kibble_test_files/*

coverage:
	mkdir -p /tmp/kibble_test_files
	TESTING=1 PYTHONWARNINGS=ignore $(MANAGE_PREFIX) coverage run --source . \
	    $(MANAGE_CMD) test --settings=$(TEST_SETTINGS) $(TEST_APP) -v 2 && \
	    (coverage html --fail-under=100 || coverage report --fail-under=100)
	rm -rf /tmp/kibble_test_files/*


test: djangotest

collectstatic:
	@echo Collecting static
	$(MANAGE) collectstatic --noinput
	@echo Done

dist:
	cd portal/static/js && npm install && npm run dist

clean:
	@echo Cleaning up...
	find ./$(PROJECT_NAME) | grep '\.pyc$$' | xargs -I {} rm {}
	@echo Done

manage:
ifndef CMD
	@echo Please, specify -e CMD=command argument to execute
else
	ELASTICSEARCH_URL=$(ELASTICSEARCH_URL) $(MANAGE) $(CMD)
endif

only_migrate:
ifndef APP_NAME
	@echo Please, specify -e APP_NAME=appname argument
else
	@echo Starting of migration of $(APP_NAME)
	$(MANAGE) migrate $(APP_NAME)
	@echo Done
endif

migrate:
ifndef APP_NAME
	@echo "You can also specify -e APP_NAME='app' to check if new migrations needed for some app"
	$(MANAGE) migrate
else
	@echo Starting of migration of $(APP_NAME)
	$(MANAGE) schemamigration $(APP_NAME) --auto
	$(MANAGE) migrate $(APP_NAME)
	@echo Done
endif

init_migrate:
ifndef APP_NAME
	@echo Please, specify -e APP_NAME=appname argument
else
	@echo Starting init migration of $(APP_NAME)
	$(MANAGE) schemamigration $(APP_NAME) --initial
	$(MANAGE) migrate $(APP_NAME)
	@echo Done
endif

#
# end targets
