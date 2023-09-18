ifneq (,$(wildcard ./.env))
  include .env
endif

lint:
	pdm run pre-commit run --all-files

test:
	@pdm run coverage run -m pytest -svv  && pdm run coverage report

publish:
	@pdm publish -u $(PYPI_UNAME) -P $(PYPI_TOKEN)
