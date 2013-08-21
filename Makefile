all:
	python manage.py runserver

db:
	python manage.py syncdb --noinput
	python manage.py migrate

test:
	python manage.py test api celerytasks web

test_client:
	python -m unittest client.tests

coverage:
	coverage run manage.py test api celerytasks web
	coverage html

flake8:
	flake8
