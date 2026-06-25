<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$tgt = isset($_REQUEST['id']) ? (int)$_REQUEST['id'] : 0;
if ($tgt <= 0 || $tgt === $uid) {
    header('Location: /friends.php'); exit;
}

$db = cyspace_db();

// check the target exists, and check we haven't blocked them or been blocked
$stmt = $db->prepare('SELECT id FROM users WHERE id = ?');
$stmt->bind_param('i', $tgt);
$stmt->execute();
$exists = $stmt->get_result()->fetch_assoc();
if (!$exists) {
    header('Location: /friends.php'); exit;
}

$stmt = $db->prepare('SELECT 1 FROM blocks WHERE (user_id = ? AND blocked_id = ?) OR (user_id = ? AND blocked_id = ?)');
$stmt->bind_param('iiii', $uid, $tgt, $tgt, $uid);
$stmt->execute();
$blocked = $stmt->get_result()->fetch_assoc();
if ($blocked) {
    header('Location: /profile.php?id=' . (int)$tgt); exit;
}

$stmt = $db->prepare('INSERT IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)');
$stmt->bind_param('ii', $uid, $tgt);
$stmt->execute();

// reciprocal — this is cyspace, friendships are mutual. tom said so.
$stmt = $db->prepare('INSERT IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)');
$stmt->bind_param('ii', $tgt, $uid);
$stmt->execute();

header('Location: /profile.php?id=' . (int)$tgt);
exit;
