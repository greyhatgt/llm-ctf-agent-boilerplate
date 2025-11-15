CC ?= gcc
CFLAGS ?= -std=gnu99 -O0
LDFLAGS ?=
LIBS ?=

# 32b or 64b
CFLAGS += -m32
# CFLAGS += -m64

# supress warning
CFLAGS += -Wno-format-security
CFLAGS += -Wno-overflow

# enable executable stack
# CFLAGS += -z execstack

# enable SSP
CFLAGS += -fstack-protector

# disable SSP
# CFLAGS += -fno-stack-protector

# enable ASLR
# CFLAGS += -pie -fPIE

# disable ASLR
CFLAGS += -no-pie

ALL := target

.PHONY: all
all: $(ALL)

target: challenge.c flag.h
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS) $(LIBS)
	checksec --file $@

.PHONY: clean
clean:
	$(RM) -f $(ALL)


