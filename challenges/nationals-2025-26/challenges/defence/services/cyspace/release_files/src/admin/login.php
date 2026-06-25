<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';

$error = '';
$username = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim((string)(isset($_POST['username']) ? $_POST['username'] : ''));
    $password = (string)(isset($_POST['password']) ? $_POST['password'] : '');

    $db = cyspace_db();
    $stmt = $db->prepare('SELECT id, username, password_bcrypt FROM admins WHERE username = ?');
    $stmt->bind_param('s', $username);
    $stmt->execute();
    $res = $stmt->get_result();
    $row = $res ? $res->fetch_assoc() : null;

    if ($row && password_verify($password, $row['password_bcrypt'])) {
        cyspace_login_admin($row['id'], $row['username']);
        header('Location: /admin/users.php');
        exit;
    }
    $error = 'login failed.';
}

$PAGE_TITLE = 'staff login';
require __DIR__ . '/../inc/header.php';
?>

<h1>Tom's Admin Console</h1>
<p><font size="-1" color="#666666">staff only &mdash; if you are not on the moderator list please <a href="/">go away</a>.</font></p>

<?php if ($error): ?><div class="flash"><?php echo h($error); ?></div><?php endif; ?>

<div class="module">
  <div class="module-title">Staff Sign-in</div>
  <div class="module-body">
    <form method="post" action="/admin/login.php">
      <table border="0" cellpadding="4">
      <tr><td align="right">staff username:</td>
          <td><input type="text" name="username" size="32" value="<?php echo h($username); ?>"></td></tr>
      <tr><td align="right">password:</td>
          <td><input type="password" name="password" size="32"></td></tr>
      <tr><td></td><td><input type="submit" value="log in"></td></tr>
      </table>
    </form>
  </div>
</div>

<?php require __DIR__ . '/../inc/footer.php'; ?>
