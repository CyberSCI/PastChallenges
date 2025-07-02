# Compiler and flags
CC = gcc
CFLAGS = -Wall -Wextra -O2
LDFLAGS = -lssl -lcrypto

# Target and source files
TARGET = sign
TARGET_V = badge_firmware
SRC = sign.c
SRC_V = verify.c

# Default target
all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

verr: $(TARGET_V)

$(TARGET_V): $(SRC_V)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Clean up build artifacts
clean:
	rm -f $(TARGET) $(TARGET_V)
