<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$db  = cyspace_db();

$to_username = '';
$subject     = '';
$body        = '';

$reply_to = isset($_GET['reply']) ? (int)$_GET['reply'] : 0;
$to_id    = isset($_GET['to'])    ? (int)$_GET['to']    : 0;

if ($reply_to > 0) {
    $stmt = $db->prepare(
        'SELECT u.username, m.subject FROM inbox_messages m
         JOIN users u ON u.id = m.from_id
         WHERE m.id = ? AND m.to_id = ?');
    $stmt->bind_param('ii', $reply_to, $uid);
    $stmt->execute();
    $r = $stmt->get_result()->fetch_assoc();
    if ($r) {
        $to_username = (string)$r['username'];
        $subject     = 'Re: ' . (string)$r['subject'];
    }
} elseif ($to_id > 0) {
    $stmt = $db->prepare('SELECT username FROM users WHERE id = ?');
    $stmt->bind_param('i', $to_id);
    $stmt->execute();
    $r = $stmt->get_result()->fetch_assoc();
    if ($r) { $to_username = (string)$r['username']; }
}

$PAGE_TITLE = 'compose mail';
require __DIR__ . '/../inc/header.php';
?>

<h1>Compose Mail</h1>

<p><font size="-1">
  <a href="/mail/inbox.php">inbox</a> &middot;
  <a href="/mail/sent.php">sent</a> &middot;
  <a href="/mail/compose.php"><b>compose</b></a>
</font></p>

<div class="module">
  <div class="module-title">New Message</div>
  <div class="module-body">
    <form method="post" action="/mail/send.php">
    <table border="0" cellpadding="4">
    <tr><td align="right">to (username):</td>
        <td><input type="text" name="to" size="32" maxlength="32" value="<?php echo h($to_username); ?>"></td></tr>
    <tr><td align="right">subject:</td>
        <td><input type="text" name="subject" size="48" maxlength="160" value="<?php echo h($subject); ?>"></td></tr>
    <tr><td align="right" valign="top">message:</td>
        <td><textarea name="body" cols="60" rows="10"><?php echo h($body); ?></textarea></td></tr>
    <tr><td></td><td><input type="submit" value="send"></td></tr>
    </table>
    </form>
  </div>
</div>

<p><font size="-2" color="#666666">no html. mandy will see. block list applies in both directions.</font></p>

<?php require __DIR__ . '/../inc/footer.php'; ?>
