NAME := $(shell cat NAME)
PORT := $(shell cat PORT)


help:
	@echo "prepare: prepare a docker image for compilation"
	@echo "build  : build the target"
	@echo "dist   : build the docker image"
	@echo "release: build the target, docker image and release them"
	@echo "run    : run the docker container"
	@echo "exploit: launch the exploit"
	@echo "test   : test the docker/exploit"

build:
	cp -f source/src/target.py docker/

dist:
	(cd docker; docker build -t $(NAME) .)

release:
	make build
	make dist

run:
	docker run -p $(PORT):9999 --rm -i -t $(NAME)

exploit:
	PORT=$(PORT) REMOTE=1 source/exploit.py

test:
	PORT=$(PORT) REMOTE=1 source/test.py

.PHONY: dist build run exploit test help clean release
