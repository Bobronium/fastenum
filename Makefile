TEST_PYPI :=  https://test.pypi.org/legacy/
RM := rm -rf

clean:
	find . -name '*.pyc' -exec $(RM) {} +
	find . -name '*.pyo' -exec $(RM) {} +
	find . -name '*~' -exec $(RM)  {} +
	find . -name '__pycache__' -exec $(RM) {} +
	$(RM) build/ dist/ docs/build/ .tox/ .cache/ .pytest_cache/ *.egg-info

build:
	make clean
	python3 setup.py sdist bdist_wheel

test:
	pytest

upload:
	twine upload dist/*

test-upload:
	twine upload --verbose --repository-url $(TEST_PYPI) dist/*

release:
	make clean
	make test
	make clean
	make build

fake-release:
	make clean
	make test
	dephell project bump pre
	make build
	make test-upload


full-release:
	make release
	make upload