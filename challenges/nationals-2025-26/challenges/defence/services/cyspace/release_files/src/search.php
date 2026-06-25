<?php
// LEGACY: this is "search v2". v1 used a full-text index on users.bio
// and was killed in 2003-09 when the recovered hardware started OOMing
// during peak (every saturday afternoon). v2 falls back to a LIKE on
// username only. fuzzy/typo search is on tom's TODO since forever.
// -mandy
//
// TODO(tom, 2003-11): bring back bio/interests search once benny finds
// us more RAM. for now username-only.
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
$PAGE_TITLE = 'search';
require __DIR__ . '/inc/header.php';

$q = isset($_GET['q']) ? (string)$_GET['q'] : '';
$results = null;
$err = null;

if ($q !== '') {
    $db = cyspace_db();
    $sql = "SELECT id, username, mood FROM users WHERE username LIKE '%" . $q . "%' ORDER BY username LIMIT 50";
    $results = $db->query($sql);
    if (!$results) {
        $err = $db->error;
    }
}
?>

<h1>find friends</h1>

<div class="module">
  <div class="module-title">Search CySpace</div>
  <div class="module-body">
    <form method="get" action="/search.php">
      Search by username: <input type="text" name="q" size="32" value="<?php echo h($q); ?>">
      <input type="submit" value="go">
    </form>
  </div>
</div>

<?php if ($q !== ''): ?>
<div class="module">
  <div class="module-title">Results for &ldquo;<?php echo h($q); ?>&rdquo;</div>
  <div class="module-body">
<?php if ($err): ?>
<font color="#c04040" size="-1">database error: <?php echo h($err); ?></font>
<?php elseif ($results && $results->num_rows > 0): ?>
<table border="0" cellpadding="4" cellspacing="0" width="100%">
<tr bgcolor="#ffffcc"><th align="left">username</th><th align="left">mood</th></tr>
<?php while ($row = $results->fetch_assoc()): ?>
<tr>
  <td><a href="/profile.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['username']); ?></a></td>
  <td><font size="-1" color="#555555"><?php echo h($row['mood']); ?></font></td>
</tr>
<?php endwhile; ?>
</table>
<?php else: ?>
<font size="-1">no users found.</font>
<?php endif; ?>
  </div>
</div>
<?php endif; ?>

<?php require __DIR__ . '/inc/footer.php'; ?>
