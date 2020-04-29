# Makefile based DevOps helper
# Author: Manuel Bernal Llinares <mbdebian@gmail.com>

# Environment
# Google Chrome Driver
version_latest_chrome_driver = 2.42
url_base_chrome_driver = http://chromedriver.storage.googleapis.com/
binary_linux_chromedriver = chromedriver_linux64.zip
binary_mac_chromedriver = chromedriver_mac64.zip
binary_windows_chromedriver = chromedriver_win32.zip
url_download_linux_chromedriver = $(url_base_chrome_driver)$(version_latest_chrome_driver)/$(binary_linux_chromedriver)
url_download_mac_chromedriver = $(url_base_chrome_driver)$(version_latest_chrome_driver)/$(binary_mac_chromedriver)
url_download_windows_chromedriver = $(url_base_chrome_driver)$(version_latest_chrome_driver)/$(binary_windows_chromedriver)
# Development support
container_name = identifiersorg/cmd-iaso
docker_compose_development_file = docker-compose-development.yml
tag_version = $(shell cat VERSION)

# default target
all: deploy

clean:
	@echo "<===|DEVOPS|===> [CLEAN] Running House Keeping tasks"

release: deploy
	@echo "<===|DEVOPS|===> [RELEASE] New Software Release, and next development version prepared"

deploy: clean container_production_push
	@echo "<===|DEVOPS|===> [DEPLOY] Deploying service container version ${tag_version}"

development_env_up: chromedriver
	@echo "<===|DEVOPS|===> [ENVIRONMENT] Bringing development environment UP"

development_env_down:
	@echo "<===|DEVOPS|===> [ENVIRONMENT] Bringing development environment DOWN"

development_run_tests: development_env_up
	@echo "<===|DEVOPS|===> [TESTS] Running Unit Tests"

app_structure:
	@echo "<===|DEVOPS|===> [PACKAGE] Application"

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

.PHONY: all clean development_run_tests app_structure container_production_build container_production_push deploy release sync_project_version set_next_development_version clean_tmp clean_bin chromedriver