<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$tgt = isset($_REQUEST['id']) ? (int)$_REQUEST['id'] : 0;
if ($tgt <= 0 || $tgt === $uid) {
    header('Location: /favourites.php');
    exit;
}

$db = cyspace_db();
$stmt = $db->prepare('SELECT id FROM users WHERE id = ?');
$stmt->bind_param('i', $tgt);
$stmt->execute();
$exists = $stmt->get_result()->fetch_assoc();
if ($exists) {
    $stmt = $db->prepare('INSERT IGNORE INTO favourites (user_id, fav_id) VALUES (?, ?)');
    $stmt->bind_param('ii', $uid, $tgt);
    $stmt->execute();
}

header('Location: /profile.php?id=' . $tgt);
exit;
