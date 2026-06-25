<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$letter = isset($_GET['l']) ? strtolower((string)$_GET['l']) : '';
if (!preg_match('/^[a-z0-9]$/', $letter)) { $letter = 'a'; }

$db = cyspace_db();
$pat = $letter . '%';
$stmt = $db->prepare(
    'SELECT id, username, mood, avatar_path FROM users
     WHERE username LIKE ? ORDER BY username LIMIT 100');
$stmt->bind_param('s', $pat);
$stmt->execute();
$res = $stmt->get_result();

$PAGE_TITLE = 'directory';
require __DIR__ . '/inc/header.php';
?>

<h1>CySpace Directory</h1>

<div class="module">
  <div class="module-title">Browse by Initial</div>
  <div class="module-body">
    <font size="-1">
    <?php for ($c = ord('a'); $c <= ord('z'); $c++): $ch = chr($c); ?>
      <a href="/whitepages.php?l=<?php echo h($ch); ?>"<?php if ($ch === $letter) echo ' style="font-weight: bold; text-decoration: underline;"'; ?>><?php echo h($ch); ?></a>
    <?php endfor; ?>
    &middot;
    <?php for ($c = ord('0'); $c <= ord('9'); $c++): $ch = chr($c); ?>
      <a href="/whitepages.php?l=<?php echo h($ch); ?>"<?php if ($ch === $letter) echo ' style="font-weight: bold;"'; ?>><?php echo h($ch); ?></a>
    <?php endfor; ?>
    </font>
  </div>
</div>

<div class="module">
  <div class="module-title">Users starting with "<?php echo h($letter); ?>"</div>
  <div class="module-body">
<?php if ($res && $res->num_rows > 0): ?>
<table cellpadding="4" cellspacing="0" border="0" width="100%">
<tr bgcolor="#ffffcc"><th align="left">username</th><th align="left">mood</th></tr>
<?php while ($row = $res->fetch_assoc()): ?>
<tr>
  <td>
    <img src="<?php echo h(cyspace_avatar_url($row)); ?>" width="24" height="24" alt="" align="absmiddle">
    <a href="/profile.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['username']); ?></a>
  </td>
  <td><font size="-1" color="#666666"><?php echo h($row['mood']); ?></font></td>
</tr>
<?php endwhile; ?>
</table>
<?php else: ?>
<font size="-1">nobody yet under this letter.</font>
<?php endif; ?>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
