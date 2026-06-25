#pragma once
#include <cstdint>
#include <pthread.h>

// ── Magic & constants ─────────────────────────────────────────────────

static constexpr uint32_t MAGIC       = 0xa1307f49;
static constexpr uint16_t SERVER_PORT = 5038;
static constexpr const char* SHM_NAME = "/ipbx_ami";

// ── Enums ─────────────────────────────────────────────────────────────

enum MsgType : uint32_t {
    HEARTBEAT    = 0x01,
    AUTH         = 0x02,
    KEY_EXCHANGE = 0x03,
    STATUS       = 0x04,
    COMMAND      = 0x05,
};

enum ContType : uint32_t {
    CONT_PING     = 0x10,
    CONT_ACK      = 0x11,

    CONT_REQUEST  = 0x20,
    CONT_RESPONSE = 0x21,

    // STATUS sub-commands
    CONT_SYS_INFO    = 0x30,   // system uptime, version, call count
    CONT_CHAN_LIST   = 0x31,   // list active channels
    CONT_EXT_STATUS  = 0x32,   // extension status  (value = extension number string)
    CONT_VOICEMAIL   = 0x33,   // voicemail summary (value = extension number string)
    CONT_CHAN_DETAIL  = 0x34,   // channel details   (value = channel name)

    // COMMAND sub-commands
    CONT_ORIGINATE   = 0x40,   // originate call    (value = "src:dst")
    CONT_HANGUP      = 0x41,   // hangup channel    (value = channel name)
    CONT_TRANSFER    = 0x42,   // transfer call     (value = "channel:dst")

    CONT_ERROR    = 0xFF,
};

// ── Wire structs (tightly packed, no padding) ─────────────────────────

#pragma pack(push, 1)

struct CtlHdr {
    uint32_t magic;      // must equal MAGIC
    uint32_t mtype;      // MsgType
    uint32_t src;        // source device id
    uint32_t dest;       // destination device id
    uint32_t stype;      // sub-type / session type
    uint32_t flags;      // reserved, must be 0
    uint32_t msg_len;    // byte length of CtlBody that follows
    uint32_t msg_hash;   // XOR checksum (see compute_hash)
    uint32_t timestamp;  // unix timestamp (ignored by server)
    uint32_t client_id;  // arbitrary client identifier
};                       // total: 40 bytes

struct CtlBody {
    uint32_t ptype;      // ContType
    uint32_t length;     // byte length of value[]
    uint8_t  value[];    // flexible array member
};                       // base: 8 bytes

#pragma pack(pop)

// ── Hash ──────────────────────────────────────────────────────────────
//
//  msg_hash = XOR of every CtlHdr field except msg_hash (treated as 0)
//             XOR'd with each body byte shifted by (i % 4) * 8
//
static inline uint32_t compute_hash(const CtlHdr& hdr, const uint8_t* body, uint32_t body_len) {
    uint32_t h = 0;
    h ^= hdr.magic;
    h ^= hdr.mtype;
    h ^= hdr.src;
    h ^= hdr.dest;
    h ^= hdr.stype;
    h ^= hdr.flags;
    h ^= hdr.msg_len;
    // skip hdr.msg_hash (treated as 0)
    h ^= hdr.timestamp;
    h ^= hdr.client_id;
    for (uint32_t i = 0; i < body_len; i++)
        h ^= static_cast<uint32_t>(body[i]) << ((i % 4) * 8);
    return h;
}

// ── Shared memory layout ──────────────────────────────────────────────
//
//  One slot: server writes a validated request, consumer writes the response.
//  Synchronised with a process-shared mutex + two condition variables.
//
static constexpr uint32_t SHM_VALUE_MAX = 256;

struct SharedSlot {
    // Synchronisation primitives (must be initialised with PTHREAD_PROCESS_SHARED)
    pthread_mutex_t mutex;
    pthread_cond_t  req_ready;    // server  → consumer : new request available
    pthread_cond_t  resp_ready;   // consumer → server  : response is ready

    // State
    bool req_pending;             // server set; consumer clears
    bool resp_pending;            // consumer set; server clears

    // Request written by server (already validated)
    uint32_t req_mtype;
    uint32_t req_ptype;
    uint32_t req_client_id;
    uint32_t req_value_len;
    uint8_t  req_value[SHM_VALUE_MAX];

    // Response written by consumer
    uint32_t resp_ptype;
    uint32_t resp_len;
    uint8_t  resp_value[SHM_VALUE_MAX];
};
