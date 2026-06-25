<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';

$db = cyspace_db();

// month grouping. user can pick yyyy-mm via ?ym=2004-02. otherwise we
// show the index of months with counts.
$ym = isset($_GET['ym']) ? (string)$_GET['ym'] : '';
if (!preg_match('/^\d{4}-\d{2}$/', $ym)) { $ym = ''; }

if ($ym !== '') {
    $stmt = $db->prepare(
        "SELECT b.id, b.title, b.created_at, u.id AS uid, u.username
         FROM blog_posts b LEFT JOIN users u ON u.id = b.author_id
         WHERE DATE_FORMAT(b.created_at, '%Y-%m') = ?
         ORDER BY b.id DESC LIMIT 200");
    $stmt->bind_param('s', $ym);
    $stmt->execute();
    $posts = $stmt->get_result();
    $months = null;
} else {
    $posts = null;
    $months = $db->query(
        "SELECT DATE_FORMAT(created_at, '%Y-%m') AS ym, COUNT(*) AS n
         FROM blog_posts
         GROUP BY DATE_FORMAT(created_at, '%Y-%m')
         ORDER BY ym DESC LIMIT 36");
}

$PAGE_TITLE = 'blog archive';
require __DIR__ . '/../inc/header.php';
?>

<h1>Blog Archive</h1>

<?php if ($ym === ''): ?>
<div class="module">
  <div class="module-title">By Month</div>
  <div class="module-body">
<?php if ($months && $months->num_rows > 0): ?>
<ul>
<?php while ($m = $months->fetch_assoc()): ?>
<li><a href="/blog/archive.php?ym=<?php echo h($m['ym']); ?>"><?php echo h($m['ym']); ?></a>
    <font size="-1" color="#666666">(<?php echo (int)$m['n']; ?>)</font></li>
<?php endwhile; ?>
</ul>
<?php else: ?>
<font size="-1">no posts in the archive yet.</font>
<?php endif; ?>
  </div>
</div>
<?php else: ?>
<div class="module">
  <div class="module-title">Posts from <?php echo h($ym); ?></div>
  <div class="module-body">
<?php if ($posts && $posts->num_rows > 0): ?>
<ul>
<?php while ($row = $posts->fetch_assoc()): ?>
<li><a href="/blog/view.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['title']); ?></a>
    <font size="-2" color="#666666">by <?php echo h($row['username']); ?> &middot; <?php echo h($row['created_at']); ?></font></li>
<?php endwhile; ?>
</ul>
<?php else: ?>
<font size="-1">no posts in <?php echo h($ym); ?>.</font>
<?php endif; ?>
  </div>
</div>
<p><font size="-1"><a href="/blog/archive.php">&laquo; back to archive index</a></font></p>
<?php endif; ?>

<?php require __DIR__ . '/../inc/footer.php'; ?>
