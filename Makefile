default: init test
travis: init check_lint test

init:
	pip install pipenv
	pipenv install --dev

test: lint
	pipenv run run-contexts -sv

lint:
	pipenv run black . --exclude "${BLACK_EXCLUSION}"

check_lint:
	pipenv run black --check . --exclude "${BLACK_EXCLUSION}"
