<?php
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$db  = cyspace_db();
$err = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $subject = trim((string)(isset($_POST['subject']) ? $_POST['subject'] : ''));
    $body    = trim((string)(isset($_POST['body'])    ? $_POST['body']    : ''));

    if ($subject === '' || strlen($subject) > 160) {
        $err = 'subject required (max 160 chars).';
    } elseif ($body === '' || strlen($body) > 8000) {
        $err = 'body required (max 8000 chars).';
    } else {
        $stmt = $db->prepare(
            'INSERT INTO bulletins (author_id, subject, body) VALUES (?, ?, ?)');
        $stmt->bind_param('iss', $uid, $subject, $body);
        $stmt->execute();
        $new_id = $db->insert_id;
        header('Location: /bulletins/view.php?id=' . (int)$new_id);
        exit;
    }
}

$PAGE_TITLE = 'post bulletin';
require __DIR__ . '/../inc/header.php';
?>

<h1>Post a Bulletin</h1>

<?php if ($err): ?><div class="flash"><?php echo h($err); ?></div><?php endif; ?>

<div class="module">
  <div class="module-title">New Bulletin</div>
  <div class="module-body">
    <form method="post" action="/bulletins/post.php">
    <table border="0" cellpadding="4">
    <tr><td align="right">subject:</td>
        <td><input type="text" name="subject" size="60" maxlength="160"></td></tr>
    <tr><td align="right" valign="top">body:</td>
        <td><textarea name="body" cols="60" rows="8" maxlength="8000"></textarea></td></tr>
    <tr><td></td><td><input type="submit" value="post bulletin"></td></tr>
    </table>
    </form>
  </div>
</div>

<p><font size="-2" color="#666666">your bulletin goes to everyone subscribed to you and to all your friends. tom is everyone's friend so tom sees them all. mandy too.</font></p>

<?php require __DIR__ . '/../inc/footer.php'; ?>
