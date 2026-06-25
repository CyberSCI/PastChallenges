SET NAMES utf8;
SET time_zone = '+00:00';

CREATE TABLE IF NOT EXISTS users (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(32)  NOT NULL UNIQUE,
    password_md5    CHAR(32)     NOT NULL,
    bio             TEXT         NULL,
    avatar_path     VARCHAR(255) NULL,
    mood            VARCHAR(64)  NULL,
    headline        VARCHAR(128) NULL,
    status_field    VARCHAR(32)  NULL,
    here_for        VARCHAR(64)  NULL,
    hometown        VARCHAR(64)  NULL,
    zodiac          VARCHAR(16)  NULL,
    education       VARCHAR(64)  NULL,
    occupation      VARCHAR(64)  NULL,
    who_id_meet     TEXT         NULL,
    interests       TEXT         NULL,
    music           TEXT         NULL,
    movies          TEXT         NULL,
    television      TEXT         NULL,
    books           TEXT         NULL,
    heroes          TEXT         NULL,
    now_playing     VARCHAR(128) NULL,
    profile_bg      VARCHAR(16)  NULL,
    profile_text    VARCHAR(16)  NULL,
    profile_link    VARCHAR(16)  NULL,
    profile_css     TEXT         NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS admins (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(32)  NOT NULL UNIQUE,
    password_bcrypt VARCHAR(255) NOT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS guestbook (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    target_user_id  INT UNSIGNED NOT NULL,
    author          VARCHAR(64)  NOT NULL,
    body            TEXT         NOT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_gb_target (target_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS friends (
    user_id   INT UNSIGNED NOT NULL,
    friend_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (user_id, friend_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS admin_notes (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(128) NOT NULL,
    body            TEXT         NOT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- bulletins board (the "post a bulletin to all your friends" thing).
-- added 2004-02 once the dialup kids stopped flooding guestbooks. -tom
CREATE TABLE IF NOT EXISTS bulletins (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    author_id       INT UNSIGNED NOT NULL,
    subject         VARCHAR(160) NOT NULL,
    body            TEXT         NOT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_bul_author (author_id),
    KEY idx_bul_recent (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bulletin_subs (
    user_id     INT UNSIGNED NOT NULL,
    author_id   INT UNSIGNED NOT NULL,
    PRIMARY KEY (user_id, author_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- blogs. tom said no blogs, then mandy launched it anyway. it stuck. -tom
CREATE TABLE IF NOT EXISTS blog_posts (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    author_id       INT UNSIGNED NOT NULL,
    title           VARCHAR(160) NOT NULL,
    body            TEXT         NOT NULL,
    mood            VARCHAR(64)  NULL,
    now_playing     VARCHAR(128) NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_blog_author (author_id),
    KEY idx_blog_recent (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS blog_comments (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    post_id         INT UNSIGNED NOT NULL,
    author_id       INT UNSIGNED NOT NULL,
    body            TEXT         NOT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_bc_post (post_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- private mail. internal only, sender_id 0 means system. -tom
CREATE TABLE IF NOT EXISTS inbox_messages (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    from_id         INT UNSIGNED NOT NULL,
    to_id           INT UNSIGNED NOT NULL,
    subject         VARCHAR(160) NOT NULL,
    body            TEXT         NOT NULL,
    is_read         TINYINT(1)   NOT NULL DEFAULT 0,
    is_deleted_to   TINYINT(1)   NOT NULL DEFAULT 0,
    is_deleted_from TINYINT(1)   NOT NULL DEFAULT 0,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_inbox_to (to_id, is_read),
    KEY idx_inbox_from (from_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- top 8 slots per user. slot 1..8. -tom
CREATE TABLE IF NOT EXISTS top8 (
    user_id   INT UNSIGNED NOT NULL,
    slot      TINYINT UNSIGNED NOT NULL,
    friend_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (user_id, slot)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS favourites (
    user_id   INT UNSIGNED NOT NULL,
    fav_id    INT UNSIGNED NOT NULL,
    PRIMARY KEY (user_id, fav_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS blocks (
    user_id    INT UNSIGNED NOT NULL,
    blocked_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (user_id, blocked_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_ratings (
    rater_id   INT UNSIGNED NOT NULL,
    rated_id   INT UNSIGNED NOT NULL,
    score      TINYINT UNSIGNED NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (rater_id, rated_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS groups (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    owner_id    INT UNSIGNED NOT NULL,
    name        VARCHAR(96)  NOT NULL,
    blurb       VARCHAR(255) NULL,
    category    VARCHAR(48)  NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_grp_cat (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS group_members (
    group_id  INT UNSIGNED NOT NULL,
    user_id   INT UNSIGNED NOT NULL,
    PRIMARY KEY (group_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS group_posts (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    group_id    INT UNSIGNED NOT NULL,
    author_id   INT UNSIGNED NOT NULL,
    body        TEXT         NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_gp_group (group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS events (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    owner_id    INT UNSIGNED NOT NULL,
    title       VARCHAR(128) NOT NULL,
    location    VARCHAR(128) NULL,
    when_dt     DATETIME     NULL,
    body        TEXT         NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_ev_when (when_dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS event_rsvps (
    event_id INT UNSIGNED NOT NULL,
    user_id  INT UNSIGNED NOT NULL,
    status   VARCHAR(16) NOT NULL DEFAULT 'going',
    PRIMARY KEY (event_id, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS forum_threads (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    author_id   INT UNSIGNED NOT NULL,
    subject     VARCHAR(160) NOT NULL,
    category    VARCHAR(48)  NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_ft_cat (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS forum_posts (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    thread_id   INT UNSIGNED NOT NULL,
    author_id   INT UNSIGNED NOT NULL,
    body        TEXT         NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_fp_thread (thread_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS classifieds (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    owner_id    INT UNSIGNED NOT NULL,
    category    VARCHAR(32)  NOT NULL,
    title       VARCHAR(128) NOT NULL,
    body        TEXT         NOT NULL,
    price_cents INT UNSIGNED NULL,
    location    VARCHAR(96)  NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_cl_cat (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- seeded glitter / blink / mood content. consumed by /blurb, /mood etc.
CREATE TABLE IF NOT EXISTS mood_catalog (
    code  VARCHAR(32) NOT NULL PRIMARY KEY,
    label VARCHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS site_news (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    headline    VARCHAR(200) NOT NULL,
    body        TEXT         NULL,
    pinned      TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO mood_catalog (code, label) VALUES
    ('rockin','rockin'), ('melancholy','melancholy'), ('bored','bored'),
    ('sparkly','sparkly'), ('annoyed','annoyed'), ('proud','proud'),
    ('hopeful','hopeful'), ('busy','busy'), ('smug','smug'),
    ('paranoid','paranoid'), ('worried','worried'), ('chill','chill');

INSERT IGNORE INTO site_news (headline, body, pinned) VALUES
    ('COMMS RESTORED TO SECTOR 7','sector 7 mesh repeater is back online courtesy of benny.',1),
    ('TOM IS YOUR FRIEND (STILL)','reminder.',1),
    ('GLITTER GIFS UNDER 50KB PLEASE','the recovered hardware cannot.',0),
    ('POST-EMP UPLOAD QUOTA: 2MB','deal with it.',0),
    ('RUMOUR: AVRIL IS ON CYSPACE NOW','unconfirmed. mandy is investigating.',0);

INSERT IGNORE INTO groups (id, owner_id, name, blurb, category) VALUES
    (1, 1, 'val verde post-emp recovery committee', 'official committee group.', 'community'),
    (2, 1, 'glitter gif appreciation society', '<50KB only.', 'arts'),
    (3, 1, 'tom is your friend', 'self explanatory.', 'community'),
    (4, 1, 'sector 7 mesh repeater fans', 'we love sector 7.', 'tech');

INSERT IGNORE INTO classifieds (id, owner_id, category, title, body, price_cents, location) VALUES
    (1, 1, 'wanted', 'looking for a working CRT', 'must be <=21 inch. trinitron preferred.', NULL, 'val verde'),
    (2, 1, 'forsale', 'kandi bracelets bulk lot', '40+ assorted. fair condition post-emp.', 1500, 'val verde'),
    (3, 1, 'forsale', 'walkman tapes', 'mostly ska, some emo.', 500, 'val verde'),
    (4, 1, 'services', 'i will fix your dialup', 'i am benny from sector 7. trade for ramen.', NULL, 'sector 7');

INSERT IGNORE INTO events (id, owner_id, title, location, when_dt, body) VALUES
    (1, 1, 'val verde recovery jam', 'community centre, val verde', '2004-06-12 19:00:00', 'bring your guitar.'),
    (2, 1, 'kandi bracelet swap', 'recovered hardware co-op', '2004-06-19 14:00:00', 'fair trade values posted at the door.');

