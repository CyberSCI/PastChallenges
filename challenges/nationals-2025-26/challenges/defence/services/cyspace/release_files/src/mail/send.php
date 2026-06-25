<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid     = cyspace_current_user_id();
$to_name = trim((string)(isset($_POST['to'])      ? $_POST['to']      : ''));
$subject = trim((string)(isset($_POST['subject']) ? $_POST['subject'] : ''));
$body    = trim((string)(isset($_POST['body'])    ? $_POST['body']    : ''));

$err = '';
$db  = cyspace_db();
$to_id = 0;

if ($to_name === '' || !preg_match('/^[A-Za-z0-9_]{1,32}$/', $to_name)) {
    $err = 'recipient username invalid.';
} elseif ($subject === '' || strlen($subject) > 160) {
    $err = 'subject required (max 160).';
} elseif ($body === '' || strlen($body) > 8000) {
    $err = 'message required (max 8000).';
} else {
    $stmt = $db->prepare('SELECT id FROM users WHERE username = ?');
    $stmt->bind_param('s', $to_name);
    $stmt->execute();
    $r = $stmt->get_result()->fetch_assoc();
    if (!$r) {
        $err = 'no such user.';
    } else {
        $to_id = (int)$r['id'];
        if ($to_id === $uid) {
            $err = 'you cannot mail yourself. (yet. on tom\'s TODO.)';
        }
    }
}

if ($err === '') {
    // check both-way block list
    $stmt = $db->prepare(
        'SELECT 1 FROM blocks WHERE (user_id = ? AND blocked_id = ?) OR (user_id = ? AND blocked_id = ?)');
    $stmt->bind_param('iiii', $uid, $to_id, $to_id, $uid);
    $stmt->execute();
    if ($stmt->get_result()->fetch_assoc()) {
        $err = 'cannot mail this user (block in effect).';
    }
}

if ($err === '') {
    $stmt = $db->prepare(
        'INSERT INTO inbox_messages (from_id, to_id, subject, body) VALUES (?, ?, ?, ?)');
    $stmt->bind_param('iiss', $uid, $to_id, $subject, $body);
    $stmt->execute();
    header('Location: /mail/sent.php');
    exit;
}

$PAGE_TITLE = 'mail - send error';
require __DIR__ . '/../inc/header.php';
?>

<h1>Send Mail</h1>

<div class="flash"><?php echo h($err); ?></div>

<p><font size="-1"><a href="/mail/compose.php">&laquo; try again</a></font></p>

<?php require __DIR__ . '/../inc/footer.php'; ?>
