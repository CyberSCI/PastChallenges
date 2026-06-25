<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$db  = cyspace_db();
$msg = '';
$err = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $now = trim((string)(isset($_POST['now_playing']) ? $_POST['now_playing'] : ''));
    if (strlen($now) > 128) {
        $err = 'too long (max 128 chars).';
    } else {
        $stmt = $db->prepare('UPDATE users SET now_playing = ? WHERE id = ?');
        $stmt->bind_param('si', $now, $uid);
        $stmt->execute();
        $msg = 'now playing updated.';
    }
}

$stmt = $db->prepare('SELECT now_playing, music FROM users WHERE id = ?');
$stmt->bind_param('i', $uid);
$stmt->execute();
$row = $stmt->get_result()->fetch_assoc();
$row = $row ? $row : array('now_playing'=>'', 'music'=>'');

$PAGE_TITLE = 'music';
require __DIR__ . '/inc/header.php';
?>

<h1>My Music</h1>

<?php if ($msg): ?><div class="module"><div class="module-body"><?php echo h($msg); ?></div></div><?php endif; ?>
<?php if ($err): ?><div class="flash"><?php echo h($err); ?></div><?php endif; ?>

<table width="100%" cellpadding="6" cellspacing="0" border="0">
<tr valign="top">
<td>

<div class="module">
  <div class="module-title">Now Playing</div>
  <div class="module-body">
    <form method="post" action="/music.php">
      <input type="text" name="now_playing" size="40" maxlength="128"
             value="<?php echo h($row['now_playing']); ?>">
      <input type="submit" value="set">
    </form>
    <p><font size="-2" color="#666666">e.g. "weezer &mdash; say it ain't so"</font></p>
  </div>
</div>

<div class="module">
  <div class="module-title">My Bands</div>
  <div class="module-body">
    <font size="-1">your full music list goes on <a href="/blurb.php">your blurb</a>. this page just sets the "now playing" ticker.</font>
  </div>
</div>

</td>
<td width="220">

<div class="module">
  <div class="module-title">Featured Artist</div>
  <div class="module-body">
    <font size="-1">
    <b>The Recovery</b><br>
    a val verde post-emp 3-piece. catch them at the next community jam.
    </font>
  </div>
</div>

</td>
</tr>
</table>

<?php require __DIR__ . '/inc/footer.php'; ?>
