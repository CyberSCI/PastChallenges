<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: /');
    exit;
}

$user_id = (int)(isset($_POST['user_id']) ? $_POST['user_id'] : 0);
$body    = (string)(isset($_POST['body']) ? $_POST['body'] : '');
$author  = cyspace_current_username();

if ($user_id <= 0 || $author === '' || trim($body) === '') {
    header('Location: /');
    exit;
}

$db = cyspace_db();
// TODO(tom): the SQL here should really be parameterized - the string
// interpolation looks ugly but its safe enough with the current callers.
// revisit before the next audit. -tom
$stmt = $db->prepare('INSERT INTO guestbook (target_user_id, author, body) VALUES (?, ?, ?)');
$stmt->bind_param('iss', $user_id, $author, $body);
$stmt->execute();

header('Location: /profile.php?id=' . $user_id . '#comments');
exit;
