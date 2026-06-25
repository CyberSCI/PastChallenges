<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$mid = isset($_GET['id']) ? (int)$_GET['id'] : 0;
if ($mid <= 0) { header('Location: /mail/inbox.php'); exit; }

$db = cyspace_db();
// must be either sender or recipient
$stmt = $db->prepare(
    'SELECT m.id, m.subject, m.body, m.created_at, m.is_read,
            m.from_id, m.to_id,
            sender.username AS sender_name, sender.id AS sender_uid,
            recv.username AS recv_name,   recv.id AS recv_uid
     FROM inbox_messages m
     LEFT JOIN users sender ON sender.id = m.from_id
     LEFT JOIN users recv   ON recv.id   = m.to_id
     WHERE m.id = ? AND (m.from_id = ? OR m.to_id = ?)');
$stmt->bind_param('iii', $mid, $uid, $uid);
$stmt->execute();
$msg = $stmt->get_result()->fetch_assoc();
if (!$msg) {
    http_response_code(404);
    $PAGE_TITLE = 'not found';
    require __DIR__ . '/../inc/header.php';
    echo '<h1>no such message</h1>';
    require __DIR__ . '/../inc/footer.php';
    exit;
}

// mark read if recipient is viewing
if ((int)$msg['to_id'] === (int)$uid && (int)$msg['is_read'] === 0) {
    $stmt = $db->prepare('UPDATE inbox_messages SET is_read = 1 WHERE id = ?');
    $stmt->bind_param('i', $mid);
    $stmt->execute();
}

$PAGE_TITLE = $msg['subject'];
require __DIR__ . '/../inc/header.php';
?>

<h1><?php echo h($msg['subject']); ?></h1>

<p><font size="-1">
  from <a href="/profile.php?id=<?php echo (int)$msg['sender_uid']; ?>"><?php echo h($msg['sender_name']); ?></a>
  to <a href="/profile.php?id=<?php echo (int)$msg['recv_uid']; ?>"><?php echo h($msg['recv_name']); ?></a>
  &middot; <?php echo h($msg['created_at']); ?>
</font></p>

<div class="module">
  <div class="module-body">
    <?php echo nl2br(h($msg['body'])); ?>
  </div>
</div>

<p><font size="-1">
<?php if ((int)$msg['to_id'] === (int)$uid): ?>
  <a href="/mail/compose.php?reply=<?php echo (int)$mid; ?>">reply</a> &middot;
<?php endif; ?>
  <a href="/mail/inbox.php">&laquo; back to inbox</a>
</font></p>

<?php require __DIR__ . '/../inc/footer.php'; ?>
