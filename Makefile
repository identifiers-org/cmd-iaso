# Makefile based DevOps helper
# Author: Manuel Bernal Llinares <mbdebian@gmail.com>

# Environment
# Development support
container_name = identifiersorg/cmd-iaso
docker_compose_development_file = docker-compose-development.yml
tag_version = $(shell cat VERSION)