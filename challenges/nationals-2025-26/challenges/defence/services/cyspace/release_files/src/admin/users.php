<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_admin();

$db = cyspace_db();
$res = $db->query('SELECT id, username, mood, avatar_path, created_at FROM users ORDER BY id DESC');

$PAGE_TITLE = 'staff - users';
require __DIR__ . '/../inc/header.php';
?>

<h1>Tom's Admin Console &middot; Users</h1>
<p><font size="-1">
  logged in as <b><?php echo h(isset($_SESSION['admin_username']) ? $_SESSION['admin_username'] : ''); ?></b>
  &middot; <a href="/admin/notes.php">notes</a>
</font></p>

<div class="module">
  <div class="module-title">Member List</div>
  <div class="module-body">
    <table border="1" cellpadding="4" cellspacing="0" width="100%" style="border-collapse: collapse;">
    <tr bgcolor="#ffffcc">
      <th align="left">id</th>
      <th align="left">avatar</th>
      <th align="left">username</th>
      <th align="left">mood</th>
      <th align="left">joined</th>
    </tr>
    <?php if ($res && $res->num_rows > 0): while ($row = $res->fetch_assoc()): ?>
    <tr>
      <td><?php echo (int)$row['id']; ?></td>
      <td><img src="<?php echo h(cyspace_avatar_url($row)); ?>" width="32" height="32" alt=""></td>
      <td><a href="/profile.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['username']); ?></a></td>
      <td><?php echo h($row['mood']); ?></td>
      <td><?php echo h($row['created_at']); ?></td>
    </tr>
    <?php endwhile; endif; ?>
    </table>
  </div>
</div>

<?php require __DIR__ . '/../inc/footer.php'; ?>
