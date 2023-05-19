ifneq (,$(wildcard ./.env))
  include .env
endif

lint:
	pdm run pre-commit run --all-files

test:
	pdm run pytest --cov --cov-report html --cov-report term

publish:
	@pdm publish -u $(PYPI_UNAME) -P $(PYPI_TOKEN)
