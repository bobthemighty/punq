BLACK_EXCLUSION=docs/source/conf.py
default: init test
travis: init check_lint test

init:
	pip install pipenv coveralls
	pipenv install --dev

test: lint
	pipenv run pytest --cov=punq --doctest-modules -p tests.doctest_namespace

lint:
	pipenv run black . --exclude "${BLACK_EXCLUSION}"

check_lint:
	pipenv run black --check . --exclude "${BLACK_EXCLUSION}"
