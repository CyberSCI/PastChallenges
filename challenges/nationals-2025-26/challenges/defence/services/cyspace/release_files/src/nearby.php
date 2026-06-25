<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

// "nearby" is a polite fiction. we have no geolocation. we pick a random
// 12 users with a non-null hometown and pretend. -tom 2003-12
$db = cyspace_db();
$res = $db->query(
    "SELECT id, username, mood, avatar_path, hometown FROM users
     WHERE hometown IS NOT NULL AND hometown <> ''
     ORDER BY RAND() LIMIT 12");

$PAGE_TITLE = 'nearby val verde-ites';
require __DIR__ . '/inc/header.php';
?>

<h1>People Near You</h1>

<div class="module">
  <div class="module-title">Probably Within Mesh Range</div>
  <div class="module-body">
<?php if ($res && $res->num_rows > 0): ?>
<table cellpadding="6" cellspacing="0" border="0" width="100%">
<?php $col = 0; while ($row = $res->fetch_assoc()): if ($col === 0) echo '<tr valign="top">'; ?>
  <td align="center" width="120">
    <a href="/profile.php?id=<?php echo (int)$row['id']; ?>">
    <img src="<?php echo h(cyspace_avatar_url($row)); ?>" width="80" height="80" alt="" border="1"></a><br>
    <a href="/profile.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['username']); ?></a><br>
    <font size="-2" color="#666666"><?php echo h($row['hometown']); ?></font>
  </td>
<?php $col++; if ($col === 4) { echo '</tr>'; $col = 0; } endwhile; if ($col !== 0) echo '</tr>'; ?>
</table>
<?php else: ?>
<font size="-1">nobody nearby. tell your neighbours to sign up.</font>
<?php endif; ?>
  </div>
</div>

<p><font size="-2" color="#666666">"nearby" is mood-based. real geolocation is on tom's TODO list.</font></p>

<?php require __DIR__ . '/inc/footer.php'; ?>
