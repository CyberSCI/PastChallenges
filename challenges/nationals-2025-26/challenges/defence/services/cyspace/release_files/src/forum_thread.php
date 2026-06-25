<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$tid = isset($_GET['id']) ? (int)$_GET['id'] : 0;
if ($tid <= 0) { header('Location: /forum.php'); exit; }

$db = cyspace_db();
$stmt = $db->prepare(
    'SELECT t.id, t.subject, t.category, t.created_at, u.id AS uid, u.username
     FROM forum_threads t LEFT JOIN users u ON u.id = t.author_id
     WHERE t.id = ?');
$stmt->bind_param('i', $tid);
$stmt->execute();
$thread = $stmt->get_result()->fetch_assoc();
if (!$thread) {
    http_response_code(404);
    $PAGE_TITLE = 'not found';
    require __DIR__ . '/inc/header.php';
    echo '<h1>no such thread</h1>';
    require __DIR__ . '/inc/footer.php';
    exit;
}

// reply handling
if ($_SERVER['REQUEST_METHOD'] === 'POST' && cyspace_current_user_id() > 0) {
    $body = trim((string)(isset($_POST['body']) ? $_POST['body'] : ''));
    if ($body !== '' && strlen($body) <= 4000) {
        $uid = cyspace_current_user_id();
        $stmt = $db->prepare('INSERT INTO forum_posts (thread_id, author_id, body) VALUES (?, ?, ?)');
        $stmt->bind_param('iis', $tid, $uid, $body);
        $stmt->execute();
        header('Location: /forum_thread.php?id=' . (int)$tid);
        exit;
    }
}

$stmt = $db->prepare(
    'SELECT p.id, p.body, p.created_at, u.id AS uid, u.username, u.avatar_path
     FROM forum_posts p JOIN users u ON u.id = p.author_id
     WHERE p.thread_id = ? ORDER BY p.id ASC LIMIT 200');
$stmt->bind_param('i', $tid);
$stmt->execute();
$posts = $stmt->get_result();

$PAGE_TITLE = $thread['subject'];
require __DIR__ . '/inc/header.php';
?>

<h1><?php echo h($thread['subject']); ?></h1>
<p><font size="-1">
  in <a href="/forum.php?cat=<?php echo h($thread['category']); ?>"><?php echo h($thread['category']); ?></a> &middot;
  started by <a href="/profile.php?id=<?php echo (int)$thread['uid']; ?>"><?php echo h($thread['username']); ?></a>
  on <?php echo h($thread['created_at']); ?>
</font></p>

<div class="module">
  <div class="module-title">Posts</div>
  <div class="module-body">
<?php if ($posts && $posts->num_rows > 0): while ($p = $posts->fetch_assoc()): ?>
<table cellpadding="4" cellspacing="0" border="0" class="comment-row" width="100%">
<tr valign="top">
  <td width="80"><img src="<?php echo h(cyspace_avatar_url($p)); ?>" width="48" height="48" alt="" border="1"></td>
  <td>
    <span class="comment-author"><a href="/profile.php?id=<?php echo (int)$p['uid']; ?>"><?php echo h($p['username']); ?></a></span>
    <span class="comment-time">&mdash; <?php echo h($p['created_at']); ?></span>
    <div class="comment-body"><?php echo nl2br(h($p['body'])); ?></div>
  </td>
</tr>
</table>
<?php endwhile; else: ?>
<font size="-1">no posts in this thread yet.</font>
<?php endif; ?>
  </div>
</div>

<?php if (cyspace_current_user_id() > 0): ?>
<div class="module">
  <div class="module-title">Reply</div>
  <div class="module-body">
    <form method="post" action="/forum_thread.php?id=<?php echo (int)$tid; ?>">
      <textarea name="body" cols="60" rows="4"></textarea><br>
      <input type="submit" value="post reply">
    </form>
  </div>
</div>
<?php else: ?>
<p><font size="-1"><a href="/login.php">log in</a> to reply.</font></p>
<?php endif; ?>

<?php require __DIR__ . '/inc/footer.php'; ?>
