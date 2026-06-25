<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$db  = cyspace_db();
$err = '';
$msg = '';

$valid_cats = array('community', 'arts', 'tech', 'sports', 'music', 'school', 'fandom');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name  = trim((string)(isset($_POST['name'])  ? $_POST['name']  : ''));
    $blurb = trim((string)(isset($_POST['blurb']) ? $_POST['blurb'] : ''));
    $cat   = (string)(isset($_POST['category'])   ? $_POST['category'] : '');

    if ($name === '' || strlen($name) > 96) {
        $err = 'name required (max 96 chars).';
    } elseif (strlen($blurb) > 255) {
        $err = 'blurb too long (max 255 chars).';
    } elseif (!in_array($cat, $valid_cats, true)) {
        $err = 'pick a category.';
    } else {
        $stmt = $db->prepare(
            'INSERT INTO groups (owner_id, name, blurb, category) VALUES (?, ?, ?, ?)');
        $stmt->bind_param('isss', $uid, $name, $blurb, $cat);
        $stmt->execute();
        $new_id = $db->insert_id;
        // owner is automatically a member
        $stmt = $db->prepare('INSERT IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)');
        $stmt->bind_param('ii', $new_id, $uid);
        $stmt->execute();
        header('Location: /group_view.php?id=' . (int)$new_id);
        exit;
    }
}

$PAGE_TITLE = 'new group';
require __DIR__ . '/inc/header.php';
?>

<h1>Start a Group</h1>

<?php if ($err): ?><div class="flash"><?php echo h($err); ?></div><?php endif; ?>

<div class="module">
  <div class="module-title">New Group</div>
  <div class="module-body">
    <form method="post" action="/group_new.php">
    <table border="0" cellpadding="4">
    <tr><td align="right">name:</td>
        <td><input type="text" name="name" size="48" maxlength="96"></td></tr>
    <tr><td align="right">category:</td>
        <td><select name="category">
          <?php foreach ($valid_cats as $c): ?>
            <option value="<?php echo h($c); ?>"><?php echo h($c); ?></option>
          <?php endforeach; ?>
        </select></td></tr>
    <tr><td align="right" valign="top">blurb:</td>
        <td><textarea name="blurb" cols="50" rows="3" maxlength="255"></textarea></td></tr>
    <tr><td></td><td><input type="submit" value="create"></td></tr>
    </table>
    </form>
  </div>
</div>

<p><font size="-2" color="#666666">groups are moderated by mod_mandy. spam groups are deleted on sight.</font></p>

<?php require __DIR__ . '/inc/footer.php'; ?>
