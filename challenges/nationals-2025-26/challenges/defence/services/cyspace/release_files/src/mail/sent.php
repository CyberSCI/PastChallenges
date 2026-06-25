<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$db  = cyspace_db();

$stmt = $db->prepare(
    'SELECT m.id, m.subject, m.is_read, m.created_at, u.id AS to_uid, u.username
     FROM inbox_messages m LEFT JOIN users u ON u.id = m.to_id
     WHERE m.from_id = ? AND m.is_deleted_from = 0
     ORDER BY m.id DESC LIMIT 100');
$stmt->bind_param('i', $uid);
$stmt->execute();
$res = $stmt->get_result();

$PAGE_TITLE = 'mail - sent';
require __DIR__ . '/../inc/header.php';
?>

<h1>Mail &middot; Sent</h1>

<p><font size="-1">
  <a href="/mail/inbox.php">inbox</a> &middot;
  <a href="/mail/sent.php"><b>sent</b></a> &middot;
  <a href="/mail/compose.php">compose</a>
</font></p>

<div class="module">
  <div class="module-title">Sent</div>
  <div class="module-body">
<?php if ($res && $res->num_rows > 0): ?>
<table cellpadding="4" cellspacing="0" border="0" width="100%">
<tr bgcolor="#ffffcc">
  <th align="left">to</th>
  <th align="left">subject</th>
  <th align="left">date</th>
  <th align="left">read?</th>
  <th></th>
</tr>
<?php while ($row = $res->fetch_assoc()): ?>
<tr>
  <td><font size="-1"><a href="/profile.php?id=<?php echo (int)$row['to_uid']; ?>"><?php echo h($row['username']); ?></a></font></td>
  <td><a href="/mail/read.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['subject']); ?></a></td>
  <td><font size="-1" color="#666666"><?php echo h($row['created_at']); ?></font></td>
  <td><font size="-1"><?php echo ((int)$row['is_read'] === 1) ? 'yes' : 'no'; ?></font></td>
  <td>
    <form method="post" action="/mail/delete.php" style="display:inline;">
      <input type="hidden" name="id" value="<?php echo (int)$row['id']; ?>">
      <input type="hidden" name="box" value="sent">
      <input type="submit" value="delete">
    </form>
  </td>
</tr>
<?php endwhile; ?>
</table>
<?php else: ?>
<font size="-1">nothing sent yet.</font>
<?php endif; ?>
  </div>
</div>

<?php require __DIR__ . '/../inc/footer.php'; ?>
