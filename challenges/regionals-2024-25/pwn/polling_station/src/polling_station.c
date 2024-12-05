#include <stdio.h>
#include <poll.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>

#define NRESULTS 10
#define NFDS (NRESULTS + 1)
#define TIMEOUT 30000

#define POLL_MESSAGE "Who will you be voting for?\n"

struct poll_result {
    int size;
    char* buf;
};

char buf[0x1000];
struct pollfd fds[NFDS];
struct poll_result poll_results[NRESULTS];

int init() {
    int sfd;
    socklen_t addr_size;
    struct sockaddr_in server_addr;

    for (int i = 0; i < NFDS; i++) {
        fds[i].fd = -1;
        fds[i].events = 0;
        fds[i].revents = 0;
    }

    for (int i = 0; i < NRESULTS; i++) {
        poll_results[i].buf = NULL;
    }

    sfd = socket(AF_INET, SOCK_STREAM, 0);

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = 0;
    server_addr.sin_addr.s_addr = inet_addr("0.0.0.0");
    bind(sfd, (struct sockaddr*)&server_addr, sizeof(server_addr));

    addr_size = sizeof(server_addr);
    getsockname(sfd, (struct sockaddr*)&server_addr, &addr_size);

    fds[0].fd = sfd;
    fds[0].events = 0xffff;

    listen(sfd, 10);

    printf("Listening on port %d\n", ntohs(server_addr.sin_port));
    fflush(stdout);

    return sfd;
}

int main(int argc, char** argv) {
    int sfd;

    sfd = init();

    while(true) {
        poll(fds, NFDS, TIMEOUT);

        for (int i = 1; i < NFDS; i++) {
            if (!fds[i].revents)
                continue;

            int n = read(fds[i].fd, buf, sizeof(buf));

            poll_results[i - 1].size = n;
            poll_results[i - 1].buf = malloc(n + 1);
            strlcpy(poll_results[i - 1].buf, buf, n);

            close(fds[i].fd);
            fds[i].fd = -1;
        }

        if (fds[0].revents) {
            for (int i = 1; i < NFDS; i++) {
                if (fds[i].fd < 0) {
                    fds[i].fd = accept(sfd, NULL, NULL);
                    fds[i].events = ~(POLLOUT | POLLWRNORM);

                    write(fds[i].fd, POLL_MESSAGE, strlen(POLL_MESSAGE));
                    break;
                }
            }
        }

        for (int i = 0; i < NRESULTS; i++) {
            if (!poll_results[i].buf)
                continue;

            printf("Response received: ");
            fwrite(poll_results[i].buf, 1, poll_results[i].size, stdout);
            printf("\n");
            fflush(stdout);

            free(poll_results[i].buf);
            poll_results[i].buf = NULL;
        }
    }

    return 0;
}
