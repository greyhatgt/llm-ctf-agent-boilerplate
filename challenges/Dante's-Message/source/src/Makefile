CC = gcc
CFLAGS = -Wall

# Output binary name
TARGET = target

# Source code file
SRC = challenge.c

# Default target to build the executable
all: $(TARGET)

# Rule to build the target binary
$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET)

# Clean up generated files
clean:
	rm -f $(TARGET)