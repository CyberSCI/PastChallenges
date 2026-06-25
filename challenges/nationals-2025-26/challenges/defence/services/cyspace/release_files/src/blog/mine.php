<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$db  = cyspace_db();

$stmt = $db->prepare(
    'SELECT id, title, created_at, mood,
            (SELECT COUNT(*) FROM blog_comments c WHERE c.post_id = blog_posts.id) AS comments
     FROM blog_posts WHERE author_id = ? ORDER BY id DESC LIMIT 100');
$stmt->bind_param('i', $uid);
$stmt->execute();
$res = $stmt->get_result();

$PAGE_TITLE = 'my blog';
require __DIR__ . '/../inc/header.php';
?>

<h1>My Blog</h1>

<div class="module">
  <div class="module-title">My Posts</div>
  <div class="module-body">
<?php if ($res && $res->num_rows > 0): ?>
<table cellpadding="4" cellspacing="0" border="0" width="100%">
<tr bgcolor="#ffffcc">
  <th align="left">date</th>
  <th align="left">title</th>
  <th align="left">mood</th>
  <th align="left">comments</th>
</tr>
<?php while ($row = $res->fetch_assoc()): ?>
<tr>
  <td><font size="-1" color="#666666"><?php echo h($row['created_at']); ?></font></td>
  <td><a href="/blog/view.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['title']); ?></a></td>
  <td><font size="-1"><?php echo h($row['mood']); ?></font></td>
  <td><font size="-1"><?php echo (int)$row['comments']; ?></font></td>
</tr>
<?php endwhile; ?>
</table>
<?php else: ?>
<font size="-1">no posts. <a href="/blog/post.php">write one</a>.</font>
<?php endif; ?>
  </div>
</div>

<?php require __DIR__ . '/../inc/footer.php'; ?>
