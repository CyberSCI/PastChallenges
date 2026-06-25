<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

// "who's online" used to mean something. now it just picks 20 users at
// random because real presence got disabled when the dialup kids started
// using it to figure out who was at school. -mandy
$db = cyspace_db();
$res = $db->query('SELECT id, username, mood, avatar_path FROM users ORDER BY RAND() LIMIT 20');

$PAGE_TITLE = "who's online";
require __DIR__ . '/inc/header.php';
?>

<h1>Who's Online</h1>

<div class="module">
  <div class="module-title">Hanging Out Right Now</div>
  <div class="module-body">
<?php if ($res && $res->num_rows > 0): ?>
<table cellpadding="4" cellspacing="0" border="0" width="100%">
<?php $col = 0; while ($row = $res->fetch_assoc()): if ($col === 0) echo '<tr valign="top">'; ?>
  <td align="center" width="100">
    <a href="/profile.php?id=<?php echo (int)$row['id']; ?>">
    <img src="<?php echo h(cyspace_avatar_url($row)); ?>" width="64" height="64" alt="" border="1"></a><br>
    <font size="-1"><a href="/profile.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['username']); ?></a></font><br>
    <font size="-2" color="#00aa00">&#9679; online</font>
  </td>
<?php $col++; if ($col === 5) { echo '</tr>'; $col = 0; } endwhile; if ($col !== 0) echo '</tr>'; ?>
</table>
<?php endif; ?>
  </div>
</div>

<p><font size="-2" color="#666666">"online" is approximate. our presence service is the val verde mesh repeater and it does not return phone calls.</font></p>

<?php require __DIR__ . '/inc/footer.php'; ?>
