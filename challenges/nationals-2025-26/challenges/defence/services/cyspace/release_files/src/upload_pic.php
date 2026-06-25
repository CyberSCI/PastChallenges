<?php
// replaces upload_old.php after the 2003-09 "shell.gif" incident. the
// shape is the same but we now restrict extension and re-sanitize the
// filename. see upload_old.php for the original code (kept around but
// 410-gated). -tom
//
// TODO(mandy): wire avatar dimension limits. right now we accept any
// size up to 2MB which means the recovered hardware sometimes serves a
// 4000x3000 jpg to render at 64x64. silly.
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
cyspace_require_login();

$msg = '';
$err = '';
$user_id = cyspace_current_user_id();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_FILES['avatar']) || $_FILES['avatar']['error'] !== UPLOAD_ERR_OK) {
        $err = 'upload failed (' . (isset($_FILES['avatar']) ? (int)$_FILES['avatar']['error'] : '?') . ')';
    } else {
        $orig  = $_FILES['avatar']['name'];
        $tmp   = $_FILES['avatar']['tmp_name'];
        $size  = (int)$_FILES['avatar']['size'];
        $lower = strtolower($orig);

        $ok = false;
        foreach (array('.jpg', '.jpeg', '.png', '.gif') as $ext) {
            if (substr($lower, -strlen($ext)) === $ext) { $ok = true; break; }
        }

        if (!$ok) {
            $err = 'only .jpg/.jpeg/.png/.gif allowed';
        } elseif ($size > 2 * 1024 * 1024) {
            $err = 'file too large';
        } else {
            $safe = preg_replace('/[^A-Za-z0-9._-]/', '_', $orig);
            $dest_name = $user_id . '_' . $safe;
            $dest = __DIR__ . '/uploads/' . $dest_name;
            if (move_uploaded_file($tmp, $dest)) {
                $db = cyspace_db();
                $stmt = $db->prepare('UPDATE users SET avatar_path = ? WHERE id = ?');
                $stmt->bind_param('si', $dest_name, $user_id);
                $stmt->execute();
                $msg = 'avatar updated.';
            } else {
                $err = 'could not save file';
            }
        }
    }
}

$PAGE_TITLE = 'upload avatar';
require __DIR__ . '/inc/header.php';
?>

<h1>Upload a Photo</h1>

<?php if ($msg): ?><div class="module"><div class="module-body"><?php echo h($msg); ?></div></div><?php endif; ?>
<?php if ($err): ?><div class="flash"><?php echo h($err); ?></div><?php endif; ?>

<table width="100%" cellpadding="6" cellspacing="0" border="0">
<tr valign="top">
<td>

<div class="module">
  <div class="module-title">Pick a Pic</div>
  <div class="module-body">
    <form method="post" enctype="multipart/form-data" action="/upload_pic.php">
      <input type="hidden" name="MAX_FILE_SIZE" value="2097152">
      <p>file: <input type="file" name="avatar"></p>
      <p><input type="submit" value="upload"></p>
    </form>
  </div>
</div>

</td>
<td width="220">

<div class="module">
  <div class="module-title">Tips</div>
  <div class="module-body">
    <font size="-1">
    <ul style="padding-left: 14px; margin: 0;">
      <li>we accept .jpg .jpeg .png .gif</li>
      <li>max 2MB &mdash; we know, we know</li>
      <li>recovered hardware loves crisp 160x160</li>
      <li>no nudes &mdash; mod_mandy is watching</li>
    </ul>
    </font>
  </div>
</div>

</td>
</tr>
</table>

<?php require __DIR__ . '/inc/footer.php'; ?>
