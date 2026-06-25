<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$db  = cyspace_db();
$msg = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = isset($_POST['action']) ? (string)$_POST['action'] : '';
    $target = isset($_POST['target']) ? (int)$_POST['target']    : 0;
    if ($target > 0 && $target !== $uid) {
        if ($action === 'sub') {
            $stmt = $db->prepare('INSERT IGNORE INTO bulletin_subs (user_id, author_id) VALUES (?, ?)');
            $stmt->bind_param('ii', $uid, $target);
            $stmt->execute();
            $msg = 'subscribed.';
        } elseif ($action === 'unsub') {
            $stmt = $db->prepare('DELETE FROM bulletin_subs WHERE user_id = ? AND author_id = ?');
            $stmt->bind_param('ii', $uid, $target);
            $stmt->execute();
            $msg = 'unsubscribed.';
        }
    }
}

$stmt = $db->prepare(
    'SELECT u.id, u.username FROM bulletin_subs b
     JOIN users u ON u.id = b.author_id
     WHERE b.user_id = ? ORDER BY u.username LIMIT 100');
$stmt->bind_param('i', $uid);
$stmt->execute();
$subs = $stmt->get_result();

$PAGE_TITLE = 'manage subscriptions';
require __DIR__ . '/../inc/header.php';
?>

<h1>Bulletin Subscriptions</h1>

<?php if ($msg): ?><div class="module"><div class="module-body"><?php echo h($msg); ?></div></div><?php endif; ?>

<div class="module">
  <div class="module-title">I subscribe to bulletins from</div>
  <div class="module-body">
<?php if ($subs && $subs->num_rows > 0): ?>
<table cellpadding="4" border="0" width="100%">
<?php while ($row = $subs->fetch_assoc()): ?>
<tr><td><a href="/profile.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['username']); ?></a></td>
    <td align="right">
      <form method="post" action="/bulletins/subscribe.php" style="display: inline;">
        <input type="hidden" name="action" value="unsub">
        <input type="hidden" name="target" value="<?php echo (int)$row['id']; ?>">
        <input type="submit" value="unsubscribe">
      </form>
    </td></tr>
<?php endwhile; ?>
</table>
<?php else: ?>
<font size="-1">no subscriptions. you only see bulletins from friends. add subscriptions to follow folks who aren't friends.</font>
<?php endif; ?>
  </div>
</div>

<p><font size="-2" color="#666666">to subscribe, click "subscribe to bulletins" on someone's profile.</font></p>

<?php require __DIR__ . '/../inc/footer.php'; ?>
