<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$tgt = isset($_REQUEST['id']) ? (int)$_REQUEST['id'] : 0;
if ($tgt > 0) {
    $db = cyspace_db();
    $stmt = $db->prepare('DELETE FROM favourites WHERE user_id = ? AND fav_id = ?');
    $stmt->bind_param('ii', $uid, $tgt);
    $stmt->execute();
}

header('Location: /favourites.php');
exit;
