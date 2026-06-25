<?php
// LEGACY: deprecated 2003-09-15. Replaced by upload_pic.php after the
// "shell.gif" incident. Keep around in case we need to rollback. -tom
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

http_response_code(410);
exit;

// ----- everything below this point is unreachable but kept for ref -----

cyspace_require_login();
$user_id = cyspace_current_user_id();

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['avatar'])) {
    $name = $_FILES['avatar']['name'];
    $dest = __DIR__ . '/uploads/' . $user_id . '_' . $name;
    move_uploaded_file($_FILES['avatar']['tmp_name'], $dest);
    header('Location: /profile.php?id=' . $user_id);
    exit;
}
?>
<!-- legacy upload form, unused -->
<form method="post" enctype="multipart/form-data" action="/upload_old.php">
  <input type="file" name="avatar">
  <input type="submit" value="upload">
</form>
