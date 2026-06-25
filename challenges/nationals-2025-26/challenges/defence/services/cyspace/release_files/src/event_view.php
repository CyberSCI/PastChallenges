<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$eid = isset($_GET['id']) ? (int)$_GET['id'] : 0;
if ($eid <= 0) { header('Location: /events.php'); exit; }

$db = cyspace_db();
$stmt = $db->prepare(
    'SELECT e.id, e.title, e.location, e.when_dt, e.body, e.created_at, u.username AS owner
     FROM events e LEFT JOIN users u ON u.id = e.owner_id
     WHERE e.id = ?');
$stmt->bind_param('i', $eid);
$stmt->execute();
$ev = $stmt->get_result()->fetch_assoc();
if (!$ev) {
    http_response_code(404);
    $PAGE_TITLE = 'not found';
    require __DIR__ . '/inc/header.php';
    echo '<h1>no such event</h1>';
    require __DIR__ . '/inc/footer.php';
    exit;
}

// rsvp handling
if ($_SERVER['REQUEST_METHOD'] === 'POST' && cyspace_current_user_id() > 0) {
    $uid    = cyspace_current_user_id();
    $status = isset($_POST['status']) ? (string)$_POST['status'] : '';
    if (in_array($status, array('going', 'maybe', 'no'), true)) {
        $stmt = $db->prepare(
            'INSERT INTO event_rsvps (event_id, user_id, status) VALUES (?, ?, ?)
             ON DUPLICATE KEY UPDATE status = VALUES(status)');
        $stmt->bind_param('iis', $eid, $uid, $status);
        $stmt->execute();
        header('Location: /event_view.php?id=' . (int)$eid);
        exit;
    }
}

$stmt = $db->prepare(
    'SELECT r.status, u.id AS uid, u.username
     FROM event_rsvps r JOIN users u ON u.id = r.user_id
     WHERE r.event_id = ? ORDER BY r.status, u.username LIMIT 200');
$stmt->bind_param('i', $eid);
$stmt->execute();
$rsvps = $stmt->get_result();
$my_status = '';
if (cyspace_current_user_id() > 0) {
    $uid = cyspace_current_user_id();
    $stmt = $db->prepare('SELECT status FROM event_rsvps WHERE event_id = ? AND user_id = ?');
    $stmt->bind_param('ii', $eid, $uid);
    $stmt->execute();
    $r = $stmt->get_result()->fetch_assoc();
    if ($r) { $my_status = (string)$r['status']; }
}

$PAGE_TITLE = $ev['title'];
require __DIR__ . '/inc/header.php';
?>

<h1><?php echo h($ev['title']); ?></h1>
<p><font size="-1">
  when: <b><?php echo h($ev['when_dt']); ?></b> &middot;
  where: <b><?php echo h($ev['location']); ?></b> &middot;
  hosted by: <b><?php echo h($ev['owner'] ? $ev['owner'] : 'tom'); ?></b>
</font></p>

<div class="module">
  <div class="module-title">Details</div>
  <div class="module-body">
    <p><?php echo nl2br(h($ev['body'])); ?></p>
  </div>
</div>

<?php if (cyspace_current_user_id() > 0): ?>
<div class="module">
  <div class="module-title">Your RSVP</div>
  <div class="module-body">
    <form method="post" action="/event_view.php?id=<?php echo (int)$eid; ?>">
      <label><input type="radio" name="status" value="going"<?php if ($my_status==='going') echo ' checked'; ?>> going</label>
      <label><input type="radio" name="status" value="maybe"<?php if ($my_status==='maybe') echo ' checked'; ?>> maybe</label>
      <label><input type="radio" name="status" value="no"<?php if ($my_status==='no') echo ' checked'; ?>> no</label>
      <input type="submit" value="save">
    </form>
  </div>
</div>
<?php endif; ?>

<div class="module">
  <div class="module-title">Who's Going</div>
  <div class="module-body">
<?php if ($rsvps && $rsvps->num_rows > 0): ?>
<font size="-1">
<?php while ($r = $rsvps->fetch_assoc()): ?>
<a href="/profile.php?id=<?php echo (int)$r['uid']; ?>"><?php echo h($r['username']); ?></a>
<font color="#666666">(<?php echo h($r['status']); ?>)</font> &middot;
<?php endwhile; ?>
</font>
<?php else: ?>
<font size="-1">nobody yet. be the first to RSVP.</font>
<?php endif; ?>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
