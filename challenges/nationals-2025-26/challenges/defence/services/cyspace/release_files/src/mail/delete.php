<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$mid = isset($_REQUEST['id'])  ? (int)$_REQUEST['id']  : 0;
$box = isset($_REQUEST['box']) ? (string)$_REQUEST['box'] : 'inbox';

if ($mid > 0) {
    $db = cyspace_db();
    if ($box === 'sent') {
        $stmt = $db->prepare(
            'UPDATE inbox_messages SET is_deleted_from = 1 WHERE id = ? AND from_id = ?');
        $stmt->bind_param('ii', $mid, $uid);
        $stmt->execute();
        header('Location: /mail/sent.php');
        exit;
    }
    // default = inbox
    $stmt = $db->prepare(
        'UPDATE inbox_messages SET is_deleted_to = 1 WHERE id = ? AND to_id = ?');
    $stmt->bind_param('ii', $mid, $uid);
    $stmt->execute();
}

header('Location: /mail/inbox.php');
exit;
