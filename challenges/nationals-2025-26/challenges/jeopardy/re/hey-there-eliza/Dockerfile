# Use a modern GCC image
FROM gcc:16

# Install socat
RUN apt-get update && \
    apt-get install -y socat && \
    rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Copy source code
COPY server_files server_files

WORKDIR /app/server_files

# Compile the program
RUN g++ -std=c++20 -O2 -o cli_app eliza.cpp

# Expose TCP port
EXPOSE 8888

# Start a new instance of the app for every TCP connection
CMD socat TCP-LISTEN:8888,reuseaddr,fork EXEC:"/app/server_files/cli_app my_script.txt",pty,echo=0