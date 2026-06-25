<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$db  = cyspace_db();

$stmt = $db->prepare(
    'SELECT u.id, u.username, u.mood, u.avatar_path
     FROM favourites f
     JOIN users u ON u.id = f.fav_id
     WHERE f.user_id = ?
     ORDER BY u.username
     LIMIT 200');
$stmt->bind_param('i', $uid);
$stmt->execute();
$favs = $stmt->get_result();

$PAGE_TITLE = 'my favourites';
require __DIR__ . '/inc/header.php';
?>

<h1>My Favourites</h1>

<div class="module">
  <div class="module-title">Pages You've Bookmarked</div>
  <div class="module-body">
<?php if ($favs && $favs->num_rows > 0): ?>
<table cellpadding="6" cellspacing="0" border="0" width="100%">
<?php $col = 0; while ($row = $favs->fetch_assoc()): if ($col === 0) echo '<tr valign="top">'; ?>
  <td align="center" width="120">
    <a href="/profile.php?id=<?php echo (int)$row['id']; ?>">
    <img src="<?php echo h(cyspace_avatar_url($row)); ?>" width="80" height="80" alt="" border="1"></a><br>
    <a href="/profile.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['username']); ?></a><br>
    <font size="-2" color="#666666"><?php echo h($row['mood']); ?></font><br>
    <font size="-2"><a href="/fav_remove.php?id=<?php echo (int)$row['id']; ?>">remove</a></font>
  </td>
<?php $col++; if ($col === 4) { echo '</tr>'; $col = 0; } endwhile; if ($col !== 0) echo '</tr>'; ?>
</table>
<?php else: ?>
<font size="-1">no favourites yet. find someone you like and click "add to favourites" on their profile.</font>
<?php endif; ?>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
