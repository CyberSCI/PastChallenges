// g++ -std=c++17 server.cpp -o server -lrt -lpthread

#include "server.h"
#include <arpa/inet.h>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <fcntl.h>
#include <netinet/in.h>
#include <string>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <unistd.h>

static constexpr const char* _u0 = "admin";

static uint32_t hx32(const std::string& s) {
    uint32_t h = 0x811c9dc5u;
    for (unsigned char c : s) h = (h ^ c) * 0x01000193u;
    return h;
}

static constexpr uint32_t _k0 = 0xcfb7e354u;

static const int8_t _lut[256] = {
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,62,-1,-1,-1,63,
    52,53,54,55,56,57,58,59,60,61,-1,-1,-1,-1,-1,-1,
    -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,
    15,16,17,18,19,20,21,22,23,24,25,-1,-1,-1,-1,-1,
    -1,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,
    41,42,43,44,45,46,47,48,49,50,51,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,
};

static std::string xdec(const uint8_t* s, uint32_t n) {
    std::string o;
    o.reserve((n / 4) * 3);
    uint32_t i = 0;
    while (i + 3 < n) {
        int8_t a = _lut[s[i]];
        int8_t b = _lut[s[i+1]];
        int8_t c = _lut[s[i+2]];
        int8_t d = _lut[s[i+3]];
        if (a < 0 || b < 0) break;
        o += static_cast<char>((a << 2) | (b >> 4));
        if (s[i+2] != '=' && c >= 0) o += static_cast<char>(((b & 0xF) << 4) | (c >> 2));
        if (s[i+3] != '=' && d >= 0) o += static_cast<char>(((c & 0x3) << 6) | d);
        i += 4;
    }
    return o;
}

static bool v_ac(const uint8_t* v, uint32_t n) {
    std::string d = xdec(v, n);
    auto p = d.find(':');
    if (p == std::string::npos) return false;
    return d.substr(0, p) == _u0 &&
           hx32(d.substr(p + 1)) == _k0;
}

static SharedSlot* m_open() {
    int fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    if (fd == -1) { perror("shm_open"); return nullptr; }

    if (ftruncate(fd, sizeof(SharedSlot)) == -1) { perror("ftruncate"); return nullptr; }

    void* p = mmap(nullptr, sizeof(SharedSlot), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (p == MAP_FAILED) { perror("mmap"); return nullptr; }

    SharedSlot* s = reinterpret_cast<SharedSlot*>(p);

    pthread_mutexattr_t ma;
    pthread_mutexattr_init(&ma);
    pthread_mutexattr_setpshared(&ma, PTHREAD_PROCESS_SHARED);
    pthread_mutex_init(&s->mutex, &ma);
    pthread_mutexattr_destroy(&ma);

    pthread_condattr_t ca;
    pthread_condattr_init(&ca);
    pthread_condattr_setpshared(&ca, PTHREAD_PROCESS_SHARED);
    pthread_cond_init(&s->req_ready,  &ca);
    pthread_cond_init(&s->resp_ready, &ca);
    pthread_condattr_destroy(&ca);

    s->req_pending  = false;
    s->resp_pending = false;

    return s;
}

static void wr_e(int fd, const char* m) {
    char b[128];
    int n = snprintf(b, sizeof(b), "ERR:%s\r\n", m);
    send(fd, b, n, 0);
}

static void wr_p(int fd, MsgType mt, ContType pt, const char* m) {
    uint32_t vl = static_cast<uint32_t>(strlen(m));
    uint32_t bl = sizeof(CtlBody) + vl;
    uint8_t* b  = new uint8_t[sizeof(CtlHdr) + bl];

    CtlBody* bd = reinterpret_cast<CtlBody*>(b + sizeof(CtlHdr));
    bd->ptype   = static_cast<uint32_t>(pt);
    bd->length  = vl;
    memcpy(bd->value, m, vl);

    CtlHdr* h   = reinterpret_cast<CtlHdr*>(b);
    h->magic     = MAGIC;
    h->mtype     = static_cast<uint32_t>(mt);
    h->src       = 0;
    h->dest      = 0;
    h->stype     = 0;
    h->flags     = 0;
    h->msg_len   = bl;
    h->timestamp = static_cast<uint32_t>(time(nullptr));
    h->client_id = 0;
    h->msg_hash  = compute_hash(*h, b + sizeof(CtlHdr), bl);

    send(fd, b, sizeof(CtlHdr) + bl, 0);
    delete[] b;
}

static void wr_r(int fd, SharedSlot* s) {
    uint32_t vl  = s->resp_len;
    uint32_t bl  = sizeof(CtlBody) + vl;
    uint8_t* b   = new uint8_t[sizeof(CtlHdr) + bl];

    CtlBody* bd  = reinterpret_cast<CtlBody*>(b + sizeof(CtlHdr));
    bd->ptype    = s->resp_ptype;
    bd->length   = vl;
    if (vl > 0)
        memcpy(bd->value, s->resp_value, vl);

    CtlHdr* h    = reinterpret_cast<CtlHdr*>(b);
    h->magic     = MAGIC;
    h->mtype     = static_cast<uint32_t>(STATUS);
    h->src       = 0;
    h->dest      = s->req_client_id;
    h->stype     = 0;
    h->flags     = 0;
    h->msg_len   = bl;
    h->timestamp = static_cast<uint32_t>(time(nullptr));
    h->client_id = 0;
    h->msg_hash  = compute_hash(*h, b + sizeof(CtlHdr), bl);

    send(fd, b, sizeof(CtlHdr) + bl, 0);
    delete[] b;
}

enum class Rc { Ok, E0, E1, E2, E3, E4, E5 };

static Rc p_chk(const uint8_t* b, ssize_t n, CtlHdr& h) {
    if (n < static_cast<ssize_t>(sizeof(CtlHdr)))
        return Rc::E0;

    memcpy(&h, b, sizeof(CtlHdr));

    if (h.magic != MAGIC)
        return Rc::E1;

    if (h.flags != 0)
        return Rc::E2;

    if (n < static_cast<ssize_t>(sizeof(CtlHdr) + h.msg_len))
        return Rc::E3;

    const uint8_t* bb = b + sizeof(CtlHdr);
    uint32_t eh       = compute_hash(h, bb, h.msg_len);
    if (h.msg_hash != eh)
        return Rc::E4;

    switch (static_cast<MsgType>(h.mtype)) {
        case HEARTBEAT:
        case AUTH:
        case KEY_EXCHANGE:
        case STATUS:
        case COMMAND:
            break;
        default:
            return Rc::E5;
    }

    return Rc::Ok;
}

static bool rd_p(int fd, uint8_t* b, ssize_t bs, CtlHdr& h, ssize_t& n) {
    n = recv(fd, b, bs, 0);
    if (n <= 0) return false;

    Rc r = p_chk(b, n, h);
    switch (r) {
        case Rc::E0: wr_e(fd, "too_short");  return false;
        case Rc::E1: wr_e(fd, "bad_magic");  return false;
        case Rc::E2: wr_e(fd, "bad_flags");  return false;
        case Rc::E3: wr_e(fd, "bad_length"); return false;
        case Rc::E4: wr_e(fd, "bad_hash");   return false;
        case Rc::E5: wr_e(fd, "bad_mtype");  return false;
        case Rc::Ok: return true;
    }
    return false;
}

static void svc(int fd, SharedSlot* s) {
    const char* bn = "IPBX-AMI/1.0\r\n";
    send(fd, bn, strlen(bn), 0);

    uint8_t b[4096];
    CtlHdr  h;
    ssize_t n;

    if (!rd_p(fd, b, sizeof(b), h, n)) { close(fd); return; }

    if (static_cast<MsgType>(h.mtype) != AUTH) {
        wr_e(fd, "auth_required");
        close(fd);
        return;
    }

    if (h.msg_len < sizeof(CtlBody)) {
        wr_e(fd, "bad_body");
        close(fd);
        return;
    }

    CtlBody ab;
    const uint8_t* abuf = b + sizeof(CtlHdr);
    memcpy(&ab, abuf, sizeof(CtlBody));

    uint32_t cl = ab.length;
    if (cl == 0 || cl > SHM_VALUE_MAX || !v_ac(abuf + sizeof(CtlBody), cl)) {
        wr_p(fd, AUTH, CONT_ERROR, "auth_failed");
        close(fd);
        return;
    }

    wr_p(fd, AUTH, CONT_ACK, "authenticated");

    if (!rd_p(fd, b, sizeof(b), h, n)) { close(fd); return; }

    if (static_cast<MsgType>(h.mtype) == AUTH) {
        wr_e(fd, "already_authed");
        close(fd);
        return;
    }

    const uint8_t* bb = b + sizeof(CtlHdr);
    CtlBody bh;
    memcpy(&bh, bb, sizeof(CtlBody));

    uint32_t vl = (h.msg_len >= sizeof(CtlBody)) ? bh.length : 0;
    if (vl > SHM_VALUE_MAX) vl = SHM_VALUE_MAX;

    pthread_mutex_lock(&s->mutex);

    s->req_mtype     = h.mtype;
    s->req_ptype     = (h.msg_len >= sizeof(CtlBody)) ? bh.ptype : 0;
    s->req_client_id = h.client_id;
    s->req_value_len = vl;
    if (vl > 0)
        memcpy(s->req_value, bb + sizeof(CtlBody), vl);

    s->resp_pending = false;
    s->req_pending  = true;
    pthread_cond_signal(&s->req_ready);

    while (!s->resp_pending)
        pthread_cond_wait(&s->resp_ready, &s->mutex);

    wr_r(fd, s);

    s->resp_pending = false;
    pthread_mutex_unlock(&s->mutex);

    close(fd);
}

int main() {
    SharedSlot* s = m_open();
    if (!s) return 1;

    int sd = socket(AF_INET, SOCK_STREAM, 0);
    if (sd < 0) { perror("socket"); return 1; }

    int o = 1;
    setsockopt(sd, SOL_SOCKET, SO_REUSEADDR, &o, sizeof(o));

    sockaddr_in sa{};
    sa.sin_family      = AF_INET;
    sa.sin_addr.s_addr = INADDR_ANY;
    sa.sin_port        = htons(SERVER_PORT);

    if (bind(sd, reinterpret_cast<sockaddr*>(&sa), sizeof(sa)) < 0) {
        perror("bind"); return 1;
    }
    if (listen(sd, 5) < 0) { perror("listen"); return 1; }

    printf("Listening on :%d\n", SERVER_PORT);

    while (true) {
        int c = accept(sd, nullptr, nullptr);
        if (c < 0) continue;
        if (fork() == 0) {
            close(sd);
            svc(c, s);
            return 0;
        }
        close(c);
    }
}
