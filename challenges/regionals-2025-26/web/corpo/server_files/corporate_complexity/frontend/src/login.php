<?php
require_once __DIR__ . '/lib/auth_client.php';

$backend = getenv('BACKEND_HOST');
$message = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'];
    $password = $_POST['password'];
    $res = auth_request($backend, $username, $password);
    if ($res === false) {
        $message = 'Backend unreachable';
    } elseif (isset($res['token'])) {
        setcookie('token', $res['token'], 0, '/', '', false, true);
        header('Location: /order.php');
        exit;
    } else {
        $message = 'Login failed';
    }
}
?>
<!doctype html>
<html>
  <body>
    <?php if ($message): ?>
      <p><?php echo htmlspecialchars($message); ?></p>
    <?php endif; ?>

    <h2>Login</h2>
    <form method="post" action="/login.php">
      Username: <input name="username"><br>
      Password: <input name="password" type="password"><br>
      <input type="submit" value="Login">
    </form>

    <p><a href="/order.php">Submit an order</a></p>
  </body>
</html>
