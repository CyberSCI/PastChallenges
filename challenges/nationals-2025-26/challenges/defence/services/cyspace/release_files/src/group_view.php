<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$gid = isset($_GET['id']) ? (int)$_GET['id'] : 0;
if ($gid <= 0) { header('Location: /groups.php'); exit; }

$db = cyspace_db();
$stmt = $db->prepare(
    'SELECT g.id, g.name, g.blurb, g.category, g.owner_id, u.username AS owner
     FROM groups g LEFT JOIN users u ON u.id = g.owner_id
     WHERE g.id = ?');
$stmt->bind_param('i', $gid);
$stmt->execute();
$grp = $stmt->get_result()->fetch_assoc();
if (!$grp) {
    http_response_code(404);
    $PAGE_TITLE = 'not found';
    require __DIR__ . '/inc/header.php';
    echo '<h1>no such group</h1>';
    require __DIR__ . '/inc/footer.php';
    exit;
}

// post handling — members can post to the wall
if ($_SERVER['REQUEST_METHOD'] === 'POST' && cyspace_current_user_id() > 0) {
    $body = trim((string)(isset($_POST['body']) ? $_POST['body'] : ''));
    if ($body !== '' && strlen($body) <= 2000) {
        $uid = cyspace_current_user_id();
        // require membership before posting
        $stmt = $db->prepare('SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?');
        $stmt->bind_param('ii', $gid, $uid);
        $stmt->execute();
        $is_member = (bool)$stmt->get_result()->fetch_assoc();
        if ($is_member) {
            $stmt = $db->prepare('INSERT INTO group_posts (group_id, author_id, body) VALUES (?, ?, ?)');
            $stmt->bind_param('iis', $gid, $uid, $body);
            $stmt->execute();
            header('Location: /group_view.php?id=' . (int)$gid);
            exit;
        }
    }
}

$stmt = $db->prepare(
    'SELECT p.id, p.body, p.created_at, u.username, u.id AS uid, u.avatar_path
     FROM group_posts p JOIN users u ON u.id = p.author_id
     WHERE p.group_id = ? ORDER BY p.id DESC LIMIT 50');
$stmt->bind_param('i', $gid);
$stmt->execute();
$posts = $stmt->get_result();

$stmt = $db->prepare(
    'SELECT u.id, u.username FROM group_members m
     JOIN users u ON u.id = m.user_id
     WHERE m.group_id = ? ORDER BY u.username LIMIT 100');
$stmt->bind_param('i', $gid);
$stmt->execute();
$members = $stmt->get_result();

$is_member = false;
if (cyspace_current_user_id() > 0) {
    $uid = cyspace_current_user_id();
    $stmt = $db->prepare('SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?');
    $stmt->bind_param('ii', $gid, $uid);
    $stmt->execute();
    $is_member = (bool)$stmt->get_result()->fetch_assoc();
}

$PAGE_TITLE = $grp['name'];
require __DIR__ . '/inc/header.php';
?>

<h1><?php echo h($grp['name']); ?></h1>
<p><font size="-1">category: <b><?php echo h($grp['category']); ?></b> &middot;
   owner: <b><?php echo h($grp['owner'] ? $grp['owner'] : 'tom'); ?></b></font></p>

<table width="100%" cellpadding="6" cellspacing="0" border="0">
<tr valign="top">
<td>

<div class="module">
  <div class="module-title">About this group</div>
  <div class="module-body">
    <p><?php echo nl2br(h($grp['blurb'])); ?></p>
  </div>
</div>

<?php if ($is_member): ?>
<div class="module">
  <div class="module-title">Post to wall</div>
  <div class="module-body">
    <form method="post" action="/group_view.php?id=<?php echo (int)$gid; ?>">
      <textarea name="body" cols="60" rows="3"></textarea><br>
      <input type="submit" value="post">
    </form>
  </div>
</div>
<?php endif; ?>

<div class="module">
  <div class="module-title">Recent Posts</div>
  <div class="module-body">
<?php if ($posts && $posts->num_rows > 0): while ($p = $posts->fetch_assoc()): ?>
<table cellpadding="4" cellspacing="0" border="0" class="comment-row" width="100%">
<tr valign="top">
  <td width="64"><img src="<?php echo h(cyspace_avatar_url($p)); ?>" width="48" height="48" alt="" border="1"></td>
  <td>
    <span class="comment-author"><a href="/profile.php?id=<?php echo (int)$p['uid']; ?>"><?php echo h($p['username']); ?></a></span>
    <span class="comment-time">&mdash; <?php echo h($p['created_at']); ?></span>
    <div class="comment-body"><?php echo nl2br(h($p['body'])); ?></div>
  </td>
</tr>
</table>
<?php endwhile; else: ?>
<font size="-1">no posts yet.</font>
<?php endif; ?>
  </div>
</div>

</td>
<td width="200">

<div class="module">
  <div class="module-title">Members</div>
  <div class="module-body">
<?php if ($members && $members->num_rows > 0): ?>
<font size="-1">
<?php while ($m = $members->fetch_assoc()): ?>
<a href="/profile.php?id=<?php echo (int)$m['id']; ?>"><?php echo h($m['username']); ?></a><br>
<?php endwhile; ?>
</font>
<?php else: ?>
<font size="-1">no members yet.</font>
<?php endif; ?>
  </div>
</div>

<?php if (cyspace_current_user_id() > 0): ?>
<div class="module">
  <div class="module-body">
    <?php if ($is_member): ?>
      <form method="post" action="/group_join.php"><input type="hidden" name="id" value="<?php echo (int)$gid; ?>"><input type="hidden" name="action" value="leave"><input type="submit" value="leave group"></form>
    <?php else: ?>
      <form method="post" action="/group_join.php"><input type="hidden" name="id" value="<?php echo (int)$gid; ?>"><input type="hidden" name="action" value="join"><input type="submit" value="join group"></form>
    <?php endif; ?>
  </div>
</div>
<?php endif; ?>

</td>
</tr>
</table>

<?php require __DIR__ . '/inc/footer.php'; ?>
