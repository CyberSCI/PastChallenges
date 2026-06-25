<?php
// guestbook v2. v1 lived in /guestbook/ as a directory with separate
// add/view/delete scripts and a flat-file backend. v2 collapsed it all
// into one script after the 2003-08 db migration. -tom
//
// TODO(mandy, 2003-12): figure out how to pin the most-recent N for
// people with thousands of comments. tom said "LIMIT 50 is fine" but
// some accounts (jenn, the recovery committee group) actually hit it.
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$user_id = isset($_GET['user_id']) ? (int)$_GET['user_id'] : 0;
if ($user_id <= 0) { header('Location: /'); exit; }

$db = cyspace_db();
$stmt = $db->prepare('SELECT id, username FROM users WHERE id = ?');
$stmt->bind_param('i', $user_id);
$stmt->execute();
$res = $stmt->get_result();
$target = $res ? $res->fetch_assoc() : null;
if (!$target) {
    http_response_code(404);
    $PAGE_TITLE = 'not found';
    require __DIR__ . '/inc/header.php';
    echo '<h1>no such user</h1>';
    require __DIR__ . '/inc/footer.php';
    exit;
}

$stmt = $db->prepare(
    'SELECT g.author, g.body, g.created_at, u.avatar_path
     FROM guestbook g
     LEFT JOIN users u ON u.username = g.author
     WHERE g.target_user_id = ? ORDER BY g.id DESC LIMIT 50');
$stmt->bind_param('i', $user_id);
$stmt->execute();
$entries = $stmt->get_result();

$PAGE_TITLE = $target['username'] . "'s guestbook";
require __DIR__ . '/inc/header.php';
?>

<h1><?php echo h($target['username']); ?>'s Friends Comments</h1>
<p><font size="-1"><a href="/profile.php?id=<?php echo (int)$user_id; ?>">&laquo; back to <?php echo h($target['username']); ?>'s profile</a></font></p>

<?php if (cyspace_current_user_id() > 0): ?>
<div class="module">
  <div class="module-title">Add Comment</div>
  <div class="module-body">
    <form method="post" action="/post_message.php">
      <input type="hidden" name="user_id" value="<?php echo (int)$user_id; ?>">
      <table border="0" cellpadding="4">
      <tr><td valign="top">message:</td>
          <td><textarea name="body" cols="60" rows="4"></textarea></td></tr>
      <tr><td></td><td><input type="submit" value="Post Comment"></td></tr>
      </table>
    </form>
  </div>
</div>
<?php else: ?>
<div class="module">
  <div class="module-body">
    <p><font size="-1"><a href="/login.php">log in</a> to sign this guestbook.</font></p>
  </div>
</div>
<?php endif; ?>

<div class="module">
  <div class="module-title">Comments</div>
  <div class="module-body">
<?php if ($entries && $entries->num_rows > 0): while ($row = $entries->fetch_assoc()): ?>
  <table cellpadding="4" cellspacing="0" border="0" class="comment-row" width="100%">
  <tr valign="top">
    <td width="80">
      <img src="<?php echo h(cyspace_avatar_url(array('username' => $row['author'], 'avatar_path' => $row['avatar_path']))); ?>"
           width="64" height="64" alt="" border="1">
    </td>
    <td>
      <span class="comment-author"><?php echo h($row['author']); ?></span>
      <span class="comment-time">&mdash; <?php echo h($row['created_at']); ?></span>
      <div class="comment-body">
      <?php echo $row['body']; ?>
      </div>
    </td>
  </tr>
  </table>
<?php endwhile; else: ?>
<font size="-1" color="#666666">no comments yet. be the first!</font>
<?php endif; ?>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
