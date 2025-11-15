# TKCTF

This is a template for your docker image that will be used to host
your CTF challenge.

## Overview

Fork `https://github.com/sslab-gatech/ctf-template` and give TAs access
permission to your private Github repo. Please Keep track of your commit
history!

~~~~{.sh}
    $ git clone https://github.com/sslab-gatech/ctf-template

    $ cd ctf-template
    $ make help
    prepare: prepare a docker image for compilation
    build  : build the target
    dist   : build the docker image
    release: build the target, docker image and release them
    run    : run the docker container
    exploit: launch the exploit
    test   : test the docker/exploit
~~~~

Keep in mind that the best challenge should be fun and educational. Please don't
design the challenge that requires any random/pure guessing (but well-designed
bruteforcing is fine).

You can replicate real security vulnerabilities, like `mini-sudo` or
`mini-heartbleed`. There are a few sources that you can refer:

- <https://ctftime.org/>
- <https://www.cvedetails.com/>
- <https://www.exploit-db.com/>

## Structure

~~~~{.sh}
    /NAME                : team-name:challenge-name (e.g., `staff:fmstr`)
    /PORT                : a port number
    /test-all.sh         : a test script to validate the challenge
    /test-patch.sh       : a test scirpt to validate the patch

    # all files to run your service
    /docker/Dockerfile   : Dockerfile
           /target       : target binary
           /flag         : follow this format: tkctf{please submit this flag!}

    # all files to be released to participants
    /release/README.md   : guideline
            /target      : target binary, if you want to release

    # source/exploit for your team and organizer
    /source/exploit.py   : exploit code
           /test.py      : functionality test
           /writeup.txt  : solution
           /patch.diff   : a patch to fix the bug
           /Dockerfile   : Dockerfile for the build environment
           /src/         : source code
~~~~

## Workflow

1. Change the `NAME` file to your challenge name: `teamname:challenge`
   (e.g., `staff:fmtstr`)
2. Change the `docker/flag` file as you wish, but wrap it inside `tkctf{...}`
   (e.g., `tkctf{please submit this flag!}`)
3. `make prepare` to build a docker container for the build process
4. Design your challenge under `source/src/` and `make dist`
   - All code and Makefile go to `source/src/`
   - See `source/src/Makefile` to enable/disable mitigation
   - Put `README.md` under `release/README.md`
   - Put `patch.diff` under `source/patch.diff`
   - `make build` to build the challenge
5. `make dist` to prepare a docker image for exploitation
6. Put an exploit to `source/exploit.py` (exploit test)
   (e.g., `make run` and `make exploit`)
7. Put a test code to `source/test.py` (functionality test)
   (e.g., `make run` and `make test`)
8. Make sure everything is ready `./test-all.sh`
   - Check what's included in `/release/` (`make release`)
   - Check if your exploit and test work
   - Check if your exploit fails yet test works after `patch.diff` is applied
     (i.e, `./test-patch.sh`)

The source code of the challenge locates in `source/src/`, which
contains its source (`fmtstr.c`) and makefile (`Makefile`).
The makefile includes various defense options you can enable
(e.g., `CFLAGS += -fstack-protector`). Please carefully enable them
as you'd like for your challenge.

## Checklist for submission

1) `/NAME`: Team/challenge name
2) `/release/README.md`: Description about the challenge
3) `/release/target`: the target binary to release
4) `/docker/flag`: Flag!
5) `/source/writeup.txt`: Your description on the challenge and solution
6) `/source/exploit.py`: Your _working_ exploit
7) `/source/test.py`: Your functionality testing code
8) `/source/patch.diff`: A patch to fix the bug
9) Make sure `test-all.sh` works!
10) Make sure `test-patch.sh` works!

## The game day
- The organizer will run `make dist` to prepare the docker image
- The organizer will release `/release/*` via CTFd
- Your docker image will be monitored with your test and exploit scripts
