#include <stdio.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <unistd.h>

char buf[0x100];

int main(int argc, char** argv) {
    int fd;

    fd = socket(AF_INET, SOCK_STREAM, 0);

    struct sockaddr_in addr;

    addr.sin_family = AF_INET;
    addr.sin_port = htons(atoi(argv[1]));
    addr.sin_addr.s_addr = inet_addr("127.0.0.1");

    int x = connect(fd, (struct sockaddr*)&addr, sizeof(addr));
    printf("%d\n", x);

    send(fd, buf, 1, MSG_OOB);

    read(0, buf, sizeof(buf));
    return 0;
}
