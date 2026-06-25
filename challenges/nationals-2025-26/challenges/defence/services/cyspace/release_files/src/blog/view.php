<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';

$pid = isset($_GET['id']) ? (int)$_GET['id'] : 0;
if ($pid <= 0) { header('Location: /blog/index.php'); exit; }

$db = cyspace_db();
$stmt = $db->prepare(
    'SELECT b.id, b.title, b.body, b.mood, b.now_playing, b.created_at,
            u.id AS uid, u.username, u.avatar_path
     FROM blog_posts b LEFT JOIN users u ON u.id = b.author_id
     WHERE b.id = ?');
$stmt->bind_param('i', $pid);
$stmt->execute();
$post = $stmt->get_result()->fetch_assoc();
if (!$post) {
    http_response_code(404);
    $PAGE_TITLE = 'not found';
    require __DIR__ . '/../inc/header.php';
    echo '<h1>no such post</h1>';
    require __DIR__ . '/../inc/footer.php';
    exit;
}

$stmt = $db->prepare(
    'SELECT c.id, c.body, c.created_at, u.id AS uid, u.username, u.avatar_path
     FROM blog_comments c JOIN users u ON u.id = c.author_id
     WHERE c.post_id = ? ORDER BY c.id ASC LIMIT 100');
$stmt->bind_param('i', $pid);
$stmt->execute();
$comments = $stmt->get_result();

$PAGE_TITLE = $post['title'];
require __DIR__ . '/../inc/header.php';
?>

<h1><?php echo h($post['title']); ?></h1>
<p><font size="-1">
  by <a href="/profile.php?id=<?php echo (int)$post['uid']; ?>"><?php echo h($post['username']); ?></a>
  &middot; <?php echo h($post['created_at']); ?>
  <?php if ($post['mood']): ?>
    &middot; mood: <b><?php echo h($post['mood']); ?></b>
  <?php endif; ?>
  <?php if ($post['now_playing']): ?>
    &middot; now playing: <i><?php echo h($post['now_playing']); ?></i>
  <?php endif; ?>
</font></p>

<div class="module">
  <div class="module-body">
    <?php echo nl2br(h($post['body'])); ?>
  </div>
</div>

<div class="module">
  <div class="module-title">Comments</div>
  <div class="module-body">
<?php if ($comments && $comments->num_rows > 0): while ($c = $comments->fetch_assoc()): ?>
<table cellpadding="4" cellspacing="0" border="0" class="comment-row" width="100%">
<tr valign="top">
  <td width="64"><img src="<?php echo h(cyspace_avatar_url($c)); ?>" width="48" height="48" alt="" border="1"></td>
  <td>
    <span class="comment-author"><a href="/profile.php?id=<?php echo (int)$c['uid']; ?>"><?php echo h($c['username']); ?></a></span>
    <span class="comment-time">&mdash; <?php echo h($c['created_at']); ?></span>
    <div class="comment-body"><?php echo nl2br(h($c['body'])); ?></div>
  </td>
</tr>
</table>
<?php endwhile; else: ?>
<font size="-1">no comments yet.</font>
<?php endif; ?>
  </div>
</div>

<?php if (cyspace_current_user_id() > 0): ?>
<div class="module">
  <div class="module-title">Leave a comment</div>
  <div class="module-body">
    <form method="post" action="/blog/comment.php">
      <input type="hidden" name="post_id" value="<?php echo (int)$pid; ?>">
      <textarea name="body" cols="60" rows="3"></textarea><br>
      <input type="submit" value="comment">
    </form>
  </div>
</div>
<?php else: ?>
<p><font size="-1"><a href="/login.php">log in</a> to comment.</font></p>
<?php endif; ?>

<?php require __DIR__ . '/../inc/footer.php'; ?>
