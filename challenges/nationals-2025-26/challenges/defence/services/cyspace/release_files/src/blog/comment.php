<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid     = cyspace_current_user_id();
$post_id = isset($_POST['post_id']) ? (int)$_POST['post_id'] : 0;
$body    = trim((string)(isset($_POST['body']) ? $_POST['body'] : ''));

if ($post_id <= 0 || $body === '' || strlen($body) > 2000) {
    header('Location: /blog/index.php');
    exit;
}

$db = cyspace_db();
$stmt = $db->prepare('SELECT id FROM blog_posts WHERE id = ?');
$stmt->bind_param('i', $post_id);
$stmt->execute();
if (!$stmt->get_result()->fetch_assoc()) {
    header('Location: /blog/index.php');
    exit;
}

$stmt = $db->prepare('INSERT INTO blog_comments (post_id, author_id, body) VALUES (?, ?, ?)');
$stmt->bind_param('iis', $post_id, $uid, $body);
$stmt->execute();

header('Location: /blog/view.php?id=' . (int)$post_id);
exit;
