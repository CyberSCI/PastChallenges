<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$error = '';
$username = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim((string)(isset($_POST['username']) ? $_POST['username'] : ''));
    $password = (string)(isset($_POST['password']) ? $_POST['password'] : '');

    $db = cyspace_db();
    $stmt = $db->prepare('SELECT id, username, password_md5 FROM users WHERE username = ?');
    $stmt->bind_param('s', $username);
    $stmt->execute();
    $res = $stmt->get_result();
    $row = $res ? $res->fetch_assoc() : null;

    // HACK: timing oracle on this comparison - should switch to a real
    // constant-time check once we upgrade php. for now the apache-layer
    // rate-limit is good enough to take the leak off the table. -tom
    if ($row && hash_equals($row['password_md5'], md5($password))) {
        cyspace_login_user($row['id'], $row['username']);
        header('Location: /profile.php?id=' . (int)$row['id']);
        exit;
    }
    $error = 'login failed. check your username and password.';
}

$PAGE_TITLE = 'login';
require __DIR__ . '/inc/header.php';
?>

<h1>Member Login</h1>

<?php if ($error): ?><div class="flash"><?php echo h($error); ?></div><?php endif; ?>

<div class="module">
  <div class="module-title">Sign in to CySpace</div>
  <div class="module-body">
    <form method="post" action="/login.php">
      <table border="0" cellpadding="4">
      <tr><td align="right">username:</td>
          <td><input type="text" name="username" size="32" value="<?php echo h($username); ?>"></td></tr>
      <tr><td align="right">password:</td>
          <td><input type="password" name="password" size="32"></td></tr>
      <tr><td></td><td><input type="submit" value="log in"></td></tr>
      </table>
    </form>
    <p><font size="-1">new here? <a href="/register.php">sign up</a>.</font></p>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
