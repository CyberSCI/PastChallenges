<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';

$bid = isset($_GET['id']) ? (int)$_GET['id'] : 0;
if ($bid <= 0) { header('Location: /bulletins/index.php'); exit; }

$db = cyspace_db();
$stmt = $db->prepare(
    'SELECT b.id, b.subject, b.body, b.created_at, u.id AS uid, u.username, u.avatar_path
     FROM bulletins b JOIN users u ON u.id = b.author_id
     WHERE b.id = ?');
$stmt->bind_param('i', $bid);
$stmt->execute();
$bul = $stmt->get_result()->fetch_assoc();
if (!$bul) {
    http_response_code(404);
    $PAGE_TITLE = 'not found';
    require __DIR__ . '/../inc/header.php';
    echo '<h1>no such bulletin</h1>';
    require __DIR__ . '/../inc/footer.php';
    exit;
}

$PAGE_TITLE = $bul['subject'];
require __DIR__ . '/../inc/header.php';
?>

<h1><?php echo h($bul['subject']); ?></h1>
<p><font size="-1">
  by <a href="/profile.php?id=<?php echo (int)$bul['uid']; ?>"><?php echo h($bul['username']); ?></a>
  &middot; <?php echo h($bul['created_at']); ?>
</font></p>

<table cellpadding="6" cellspacing="0" border="0" width="100%">
<tr valign="top">
  <td width="80"><img src="<?php echo h(cyspace_avatar_url($bul)); ?>" width="64" height="64" alt="" border="1"></td>
  <td>
    <div class="module">
      <div class="module-body">
        <?php echo nl2br(h($bul['body'])); ?>
      </div>
    </div>
  </td>
</tr>
</table>

<p><font size="-1"><a href="/bulletins/index.php">&laquo; back to bulletins</a></font></p>

<?php require __DIR__ . '/../inc/footer.php'; ?>
