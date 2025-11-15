NAME := $(shell cat NAME)
PORT := $(shell cat PORT)

DOCKER_BUILD := docker run -v ./source/src:/src --rm -i -t $(NAME)-build bash -c

help:
	@echo "prepare: prepare a docker image for compilation"
	@echo "build  : build the target"
	@echo "dist   : build the docker image"
	@echo "release: build the target, docker image and release them"
	@echo "run    : run the docker container"
	@echo "exploit: launch the exploit"
	@echo "test   : test the docker/exploit"

prepare:
	(cd source; docker build -t $(NAME)-build .)

build:
	$(DOCKER_BUILD) 'cd src; make'
	cp -f source/src/target docker/

clean:
	$(DOCKER_BUILD) 'cd src; make clean'

dist:
	(cd docker; docker build -t $(NAME) .)

release:
	make build
	make dist
	cp -f docker/target release/target

run:
	docker run -p $(PORT):9999 --rm -i -t $(NAME)

exploit:
	PORT=$(PORT) REMOTE=1 source/exploit.py

test:
	PORT=$(PORT) REMOTE=1 source/test.py

.PHONY: dist build run exploit test help clean release
