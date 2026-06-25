<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$tgt = isset($_REQUEST['id']) ? (int)$_REQUEST['id'] : 0;
if ($tgt > 0 && $tgt !== $uid) {
    $db = cyspace_db();
    $stmt = $db->prepare('DELETE FROM friends WHERE user_id = ? AND friend_id = ?');
    $stmt->bind_param('ii', $uid, $tgt);
    $stmt->execute();
    // reciprocal removal too
    $stmt = $db->prepare('DELETE FROM friends WHERE user_id = ? AND friend_id = ?');
    $stmt->bind_param('ii', $tgt, $uid);
    $stmt->execute();
    // and clear them out of top 8 if present
    $stmt = $db->prepare('DELETE FROM top8 WHERE user_id = ? AND friend_id = ?');
    $stmt->bind_param('ii', $uid, $tgt);
    $stmt->execute();
}

header('Location: /friends.php');
exit;
