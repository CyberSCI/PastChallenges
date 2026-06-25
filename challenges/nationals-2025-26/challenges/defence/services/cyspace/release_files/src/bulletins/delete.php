<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$bid = isset($_REQUEST['id']) ? (int)$_REQUEST['id'] : 0;

if ($bid > 0) {
    $db = cyspace_db();
    // only the author can delete their own bulletin.
    $stmt = $db->prepare('DELETE FROM bulletins WHERE id = ? AND author_id = ?');
    $stmt->bind_param('ii', $bid, $uid);
    $stmt->execute();
}

header('Location: /bulletins/index.php');
exit;
