<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$db  = cyspace_db();
$err = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $title = trim((string)(isset($_POST['title']) ? $_POST['title'] : ''));
    $body  = trim((string)(isset($_POST['body'])  ? $_POST['body']  : ''));
    $mood  = trim((string)(isset($_POST['mood'])  ? $_POST['mood']  : ''));
    $np    = trim((string)(isset($_POST['now_playing']) ? $_POST['now_playing'] : ''));

    if ($title === '' || strlen($title) > 160) {
        $err = 'title required (max 160 chars).';
    } elseif ($body === '' || strlen($body) > 16000) {
        $err = 'body required (max 16000 chars).';
    } elseif (strlen($mood) > 64 || strlen($np) > 128) {
        $err = 'mood/now-playing too long.';
    } else {
        $stmt = $db->prepare(
            'INSERT INTO blog_posts (author_id, title, body, mood, now_playing)
             VALUES (?, ?, ?, ?, ?)');
        $stmt->bind_param('issss', $uid, $title, $body, $mood, $np);
        $stmt->execute();
        $new_id = $db->insert_id;
        header('Location: /blog/view.php?id=' . (int)$new_id);
        exit;
    }
}

$PAGE_TITLE = 'new blog post';
require __DIR__ . '/../inc/header.php';
?>

<h1>New Blog Post</h1>

<?php if ($err): ?><div class="flash"><?php echo h($err); ?></div><?php endif; ?>

<div class="module">
  <div class="module-title">Write</div>
  <div class="module-body">
    <form method="post" action="/blog/post.php">
    <table border="0" cellpadding="4">
    <tr><td align="right">title:</td>
        <td><input type="text" name="title" size="60" maxlength="160"></td></tr>
    <tr><td align="right">mood (optional):</td>
        <td><input type="text" name="mood" size="20" maxlength="64"></td></tr>
    <tr><td align="right">now playing (optional):</td>
        <td><input type="text" name="now_playing" size="40" maxlength="128"></td></tr>
    <tr><td align="right" valign="top">body:</td>
        <td><textarea name="body" cols="60" rows="12"></textarea></td></tr>
    <tr><td></td><td><input type="submit" value="publish"></td></tr>
    </table>
    </form>
  </div>
</div>

<p><font size="-2" color="#666666">no html. mandy will see. -tom</font></p>

<?php require __DIR__ . '/../inc/footer.php'; ?>
