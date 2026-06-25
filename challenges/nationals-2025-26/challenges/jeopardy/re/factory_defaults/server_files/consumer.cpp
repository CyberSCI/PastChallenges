// g++ -std=c++17 consumer.cpp -o consumer -lrt -lpthread

#include "server.h"
#include <cstdio>
#include <cstring>
#include <ctime>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

static const char* FLAG = "CYBERSCI{1t5_alw4y5_adm1n_4dm1n_3281}";

// ── Mock PBX state ────────────────────────────────────────────────────

struct Channel {
    const char* name;
    const char* state;    // "Up", "Ringing", "Down"
    const char* src_ext;
    const char* dst_ext;
};

struct Extension {
    const char* number;
    const char* name;
    const char* status;   // "idle", "inuse", "unavailable"
    int         vm_new;
    int         vm_old;
};

static Channel CHANNELS[] = {
    { "SIP/1001-00000001", "Up",      "1001", "1003" },
    { "SIP/1002-00000002", "Ringing", "1002", "1004" },
    { "SIP/flag-00000000", "Idle",    "0000", "0000" },
};
static constexpr int N_CHANNELS = 3;

static Extension EXTENSIONS[] = {
    { "1001", "Alice",   "inuse",       2, 1 },
    { "1002", "Bob",     "inuse",       0, 4 },
    { "1003", "Charlie", "idle",        1, 0 },
    { "1004", "Dave",    "idle",        0, 2 },
    { "1005", "Eve",     "unavailable", 3, 1 },
};
static constexpr int N_EXTENSIONS = 5;

static uint32_t BOOT_TIME = 0;

// ── Shared memory helpers ─────────────────────────────────────────────

static SharedSlot* shm_attach() {
    int fd = shm_open(SHM_NAME, O_RDWR, 0666);
    if (fd == -1) { perror("shm_open"); return nullptr; }
    void* ptr = mmap(nullptr, sizeof(SharedSlot), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (ptr == MAP_FAILED) { perror("mmap"); return nullptr; }
    return reinterpret_cast<SharedSlot*>(ptr);
}

static void write_response(SharedSlot* slot, ContType ptype, const char* msg) {
    uint32_t len     = static_cast<uint32_t>(strlen(msg));
    if (len > SHM_VALUE_MAX) len = SHM_VALUE_MAX;
    slot->resp_ptype = static_cast<uint32_t>(ptype);
    slot->resp_len   = len;
    memcpy(slot->resp_value, msg, len);
}

// ── STATUS handlers ───────────────────────────────────────────────────

static void handle_sys_info(SharedSlot* slot) {
    uint32_t uptime = static_cast<uint32_t>(time(nullptr)) - BOOT_TIME;
    char buf[SHM_VALUE_MAX];
    snprintf(buf, sizeof(buf),
        "version=1.0.0,"
        "uptime=%u,"
        "active_calls=%d,"
        "registered_peers=%d,"
        "serial=IPBX-1000",
        uptime, N_CHANNELS, N_EXTENSIONS);
    write_response(slot, CONT_RESPONSE, buf);
}

static void handle_chan_list(SharedSlot* slot) {
    char buf[SHM_VALUE_MAX];
    int  pos = 0;
    for (int i = 0; i < N_CHANNELS; i++) {
        pos += snprintf(buf + pos, sizeof(buf) - pos,
            "%schannel=%s,state=%s,src=%s,dst=%s",
            i ? ";" : "",
            CHANNELS[i].name,
            CHANNELS[i].state,
            CHANNELS[i].src_ext,
            CHANNELS[i].dst_ext);
        if (pos >= static_cast<int>(sizeof(buf))) break;
    }
    write_response(slot, CONT_RESPONSE, buf);
}

static void handle_chan_detail(SharedSlot* slot) {
    char chan[SHM_VALUE_MAX] = {};
    uint32_t vlen = slot->req_value_len < SHM_VALUE_MAX - 1 ? slot->req_value_len : SHM_VALUE_MAX - 1;
    memcpy(chan, slot->req_value, vlen);

    for (int i = 0; i < N_CHANNELS; i++) {
        if (strcmp(CHANNELS[i].name, chan) == 0) {
            char buf[SHM_VALUE_MAX];
            if (strcmp(chan, "SIP/flag-00000000") == 0) {
                snprintf(buf, sizeof(buf),
                    "channel=%s,state=%s,src=%s,dst=%s,info=%s",
                    CHANNELS[i].name, CHANNELS[i].state,
                    CHANNELS[i].src_ext, CHANNELS[i].dst_ext, FLAG);
            } else {
                snprintf(buf, sizeof(buf),
                    "channel=%s,state=%s,src=%s,dst=%s",
                    CHANNELS[i].name, CHANNELS[i].state,
                    CHANNELS[i].src_ext, CHANNELS[i].dst_ext);
            }
            write_response(slot, CONT_RESPONSE, buf);
            return;
        }
    }
    write_response(slot, CONT_ERROR, "channel_not_found");
}

static void handle_ext_status(SharedSlot* slot) {
    // value field contains the requested extension number
    char ext[16] = {};
    uint32_t vlen = slot->req_value_len < 15 ? slot->req_value_len : 15;
    memcpy(ext, slot->req_value, vlen);

    for (int i = 0; i < N_EXTENSIONS; i++) {
        if (strcmp(EXTENSIONS[i].number, ext) == 0) {
            char buf[SHM_VALUE_MAX];
            snprintf(buf, sizeof(buf),
                "ext=%s,name=%s,status=%s",
                EXTENSIONS[i].number,
                EXTENSIONS[i].name,
                EXTENSIONS[i].status);
            write_response(slot, CONT_RESPONSE, buf);
            return;
        }
    }
    write_response(slot, CONT_ERROR, "extension_not_found");
}

static void handle_voicemail(SharedSlot* slot) {
    char ext[16] = {};
    uint32_t vlen = slot->req_value_len < 15 ? slot->req_value_len : 15;
    memcpy(ext, slot->req_value, vlen);

    for (int i = 0; i < N_EXTENSIONS; i++) {
        if (strcmp(EXTENSIONS[i].number, ext) == 0) {
            char buf[SHM_VALUE_MAX];
            snprintf(buf, sizeof(buf),
                "ext=%s,new=%d,old=%d",
                EXTENSIONS[i].number,
                EXTENSIONS[i].vm_new,
                EXTENSIONS[i].vm_old);
            write_response(slot, CONT_RESPONSE, buf);
            return;
        }
    }
    write_response(slot, CONT_ERROR, "extension_not_found");
}

// ── COMMAND handlers ──────────────────────────────────────────────────

static void handle_originate(SharedSlot* slot) {
    // value = "src:dst"
    char val[SHM_VALUE_MAX] = {};
    uint32_t vlen = slot->req_value_len < SHM_VALUE_MAX - 1 ? slot->req_value_len : SHM_VALUE_MAX - 1;
    memcpy(val, slot->req_value, vlen);

    char* sep = strchr(val, ':');
    if (!sep) { write_response(slot, CONT_ERROR, "bad_value:expected src:dst"); return; }
    *sep = '\0';
    const char* src = val;
    const char* dst = sep + 1;

    char buf[SHM_VALUE_MAX];
    snprintf(buf, sizeof(buf),
        "channel=SIP/%s-000000%02x,dst=%s,state=Ringing",
        src, static_cast<uint32_t>(time(nullptr)) & 0xFF, dst);
    write_response(slot, CONT_RESPONSE, buf);
}

static void handle_hangup(SharedSlot* slot) {
    // value = channel name
    char chan[SHM_VALUE_MAX] = {};
    uint32_t vlen = slot->req_value_len < SHM_VALUE_MAX - 1 ? slot->req_value_len : SHM_VALUE_MAX - 1;
    memcpy(chan, slot->req_value, vlen);

    for (int i = 0; i < N_CHANNELS; i++) {
        if (strcmp(CHANNELS[i].name, chan) == 0) {
            char buf[SHM_VALUE_MAX];
            snprintf(buf, sizeof(buf), "channel=%s,state=Down", chan);
            write_response(slot, CONT_RESPONSE, buf);
            return;
        }
    }
    write_response(slot, CONT_ERROR, "channel_not_found");
}

static void handle_transfer(SharedSlot* slot) {
    // value = "channel:dst"
    char val[SHM_VALUE_MAX] = {};
    uint32_t vlen = slot->req_value_len < SHM_VALUE_MAX - 1 ? slot->req_value_len : SHM_VALUE_MAX - 1;
    memcpy(val, slot->req_value, vlen);

    char* sep = strchr(val, ':');
    if (!sep) { write_response(slot, CONT_ERROR, "bad_value:expected channel:dst"); return; }
    *sep = '\0';
    const char* chan = val;
    const char* dst  = sep + 1;

    char buf[SHM_VALUE_MAX];
    snprintf(buf, sizeof(buf), "channel=%s,dst=%s,state=Transferred", chan, dst);
    write_response(slot, CONT_RESPONSE, buf);
}

// ── Dispatcher ────────────────────────────────────────────────────────

static void process_request(SharedSlot* slot) {
    MsgType  mtype = static_cast<MsgType>(slot->req_mtype);
    ContType ptype = static_cast<ContType>(slot->req_ptype);

    switch (mtype) {

        case HEARTBEAT:
            write_response(slot, CONT_ACK, "pong");
            break;

        case STATUS:
            switch (ptype) {
                case CONT_SYS_INFO:    handle_sys_info(slot);    break;
                case CONT_CHAN_LIST:   handle_chan_list(slot);   break;
                case CONT_CHAN_DETAIL: handle_chan_detail(slot); break;
                case CONT_EXT_STATUS:  handle_ext_status(slot);  break;
                case CONT_VOICEMAIL:   handle_voicemail(slot);   break;
                default:
                    write_response(slot, CONT_ERROR, "unknown_status_ptype");
            }
            break;

        case COMMAND:
            switch (ptype) {
                case CONT_ORIGINATE: handle_originate(slot); break;
                case CONT_HANGUP:    handle_hangup(slot);    break;
                case CONT_TRANSFER:  handle_transfer(slot);  break;
                default:
                    write_response(slot, CONT_ERROR, "unknown_command_ptype");
            }
            break;

        default:
            write_response(slot, CONT_ERROR, "unhandled_mtype");
            break;
    }
}

// ── Main ──────────────────────────────────────────────────────────────

int main() {
    BOOT_TIME = static_cast<uint32_t>(time(nullptr));

    SharedSlot* slot = nullptr;
    while (!slot) {
        slot = shm_attach();
        if (!slot) sleep(1);
    }

    printf("Consumer attached to %s\n", SHM_NAME);

    while (true) {
        pthread_mutex_lock(&slot->mutex);

        while (!slot->req_pending)
            pthread_cond_wait(&slot->req_ready, &slot->mutex);

        process_request(slot);

        slot->req_pending  = false;
        slot->resp_pending = true;
        pthread_cond_signal(&slot->resp_ready);

        pthread_mutex_unlock(&slot->mutex);
    }
}
