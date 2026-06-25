<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
cyspace_require_login();

$uid    = cyspace_current_user_id();
$gid    = isset($_REQUEST['id'])     ? (int)$_REQUEST['id']     : 0;
$action = isset($_REQUEST['action']) ? (string)$_REQUEST['action'] : 'join';

if ($gid > 0) {
    $db = cyspace_db();
    $stmt = $db->prepare('SELECT id FROM groups WHERE id = ?');
    $stmt->bind_param('i', $gid);
    $stmt->execute();
    if ($stmt->get_result()->fetch_assoc()) {
        if ($action === 'leave') {
            $stmt = $db->prepare('DELETE FROM group_members WHERE group_id = ? AND user_id = ?');
            $stmt->bind_param('ii', $gid, $uid);
            $stmt->execute();
        } else {
            $stmt = $db->prepare('INSERT IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)');
            $stmt->bind_param('ii', $gid, $uid);
            $stmt->execute();
        }
    }
}

header('Location: /group_view.php?id=' . (int)$gid);
exit;
