# Makefile based DevOps helper
# Author: Manuel Bernal Llinares <mbdebian@gmail.com>

# Environment
# Development support
container_name = identifiersorg/cmd-iaso
docker_compose_development_file = docker-compose-development.yml
tag_version = $(shell cat VERSION)

# default target
all: deploy

# Local Installation
install: dev_environment
	@echo "<===|DEVOPS|===> [INSTALL] Installing the tool locally"

dev_environment: setup_tool
	@echo "<===|DEVOPS|===> [ENVIRONMENT] Preparing development environment"

python_install:
	@echo "<===|DEVOPS|===> [INSTALL] Preparing Python Virtual Environment"
	@pip install --upgrade --user virtualenv
	@virtualenv -p `which python3` python_install

setup_tool: python_install
	@echo "<===|DEVOPS|===> [INSTALL] Setting up the tool within the virtual environment"
	@python_install/bin/python setup.py install

# END - Local Installation

clean:
	@echo "<===|DEVOPS|===> [CLEAN] Running House Keeping tasks"

release: deploy
	@echo "<===|DEVOPS|===> [RELEASE] New Software Release, and next development version prepared"

deploy: clean container_production_push
	@echo "<===|DEVOPS|===> [DEPLOY] Deploying service container version ${tag_version}"

development_env_up:
	@echo "<===|DEVOPS|===> [ENVIRONMENT] Bringing development environment UP"
	@docker-compose -f $(docker_compose_development_file) up -d
	@# TODO Clean this way of referencing the target name in future iterations
	@rm -f development_env_down
	@touch development_env_up

development_env_down:
	@echo "<===|DEVOPS|===> [ENVIRONMENT] Bringing development environment DOWN"
	@docker-compose -f $(docker_compose_development_file) down
	@# TODO Clean this way of referencing the target name in future iterations
	@rm -f development_env_up
	@touch development_env_down

development_run_tests: development_env_up
	@echo "<===|DEVOPS|===> [TESTS] Running Unit Tests"
	# TODO

app_structure:
	@echo "<===|DEVOPS|===> [PACKAGE] Application"
	# TODO

container_production_build: app_structure
	@echo "<===|DEVOPS|===> [BUILD] Production container $(container_name):$(tag_version)"
	@docker build -t $(container_name):$(tag_version) -t $(container_name):latest .

container_production_push: container_production_build
	@echo "<===|DEVOPS|===> [PUBLISH]> Production container $(container_name):$(tag_version)"
	@docker push $(container_name):$(tag_version)
	@docker push $(container_name):latest

# Folders
tmp:
	@echo "<===|DEVOPS|===> [FOLDER] Preparing temporary folder"
	@mkdir tmp
# END - Folders

# House keeping tasks
clean_tmp:
	@echo "<===|DEVOPS|===> [HOUSEKEEPING] Removing temporary folder"
	@rm -rf tmp

.PHONY: all install dev_environment setup_tool clean development_run_tests app_structure container_production_build container_production_push deploy release clean_tmp clean_bin
