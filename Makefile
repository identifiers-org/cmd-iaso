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