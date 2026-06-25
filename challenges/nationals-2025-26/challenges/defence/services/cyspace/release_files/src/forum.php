<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$cat = isset($_GET['cat']) ? (string)$_GET['cat'] : '';
$valid_cats = array('general', 'music', 'tech', 'school', 'videos', 'arts', 'sector7');

$db = cyspace_db();
if ($cat !== '' && in_array($cat, $valid_cats, true)) {
    $stmt = $db->prepare(
        'SELECT t.id, t.subject, t.category, u.username, u.id AS uid,
                (SELECT COUNT(*) FROM forum_posts p WHERE p.thread_id = t.id) AS posts
         FROM forum_threads t LEFT JOIN users u ON u.id = t.author_id
         WHERE t.category = ? ORDER BY t.id DESC LIMIT 50');
    $stmt->bind_param('s', $cat);
    $stmt->execute();
    $threads = $stmt->get_result();
} else {
    $cat = '';
    $threads = $db->query(
        'SELECT t.id, t.subject, t.category, u.username, u.id AS uid,
                (SELECT COUNT(*) FROM forum_posts p WHERE p.thread_id = t.id) AS posts
         FROM forum_threads t LEFT JOIN users u ON u.id = t.author_id
         ORDER BY t.id DESC LIMIT 50');
}

$PAGE_TITLE = 'forum';
require __DIR__ . '/inc/header.php';
?>

<h1>CySpace Forum</h1>

<div class="module">
  <div class="module-title">Boards</div>
  <div class="module-body">
    <font size="-1">
    <a href="/forum.php">all</a>
    <?php foreach ($valid_cats as $c): ?>
     &middot; <a href="/forum.php?cat=<?php echo h($c); ?>"><?php echo h($c); ?></a>
    <?php endforeach; ?>
    </font>
  </div>
</div>

<div class="module">
  <div class="module-title"><?php echo $cat === '' ? 'Recent threads' : ('board: ' . h($cat)); ?></div>
  <div class="module-body">
<?php if ($threads && $threads->num_rows > 0): ?>
<table cellpadding="4" cellspacing="0" border="0" width="100%">
<tr bgcolor="#ffffcc">
  <th align="left">subject</th>
  <th align="left">category</th>
  <th align="left">posts</th>
  <th align="left">by</th>
</tr>
<?php while ($row = $threads->fetch_assoc()): ?>
<tr>
  <td><a href="/forum_thread.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['subject']); ?></a></td>
  <td><font size="-1" color="#666666"><?php echo h($row['category']); ?></font></td>
  <td><font size="-1"><?php echo (int)$row['posts']; ?></font></td>
  <td><font size="-1"><a href="/profile.php?id=<?php echo (int)$row['uid']; ?>"><?php echo h($row['username']); ?></a></font></td>
</tr>
<?php endwhile; ?>
</table>
<?php else: ?>
<font size="-1">no threads on this board yet.</font>
<?php endif; ?>
  </div>
</div>

<?php if (cyspace_current_user_id() > 0): ?>
<p><font size="-1"><a href="/forum_new.php">start a new thread</a></font></p>
<?php endif; ?>

<?php require __DIR__ . '/inc/footer.php'; ?>
