<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$db = cyspace_db();
$res = $db->query(
    'SELECT e.id, e.title, e.location, e.when_dt, e.body, u.username AS owner,
            (SELECT COUNT(*) FROM event_rsvps r WHERE r.event_id = e.id AND r.status = "going") AS going
     FROM events e LEFT JOIN users u ON u.id = e.owner_id
     ORDER BY e.when_dt ASC LIMIT 50');

$PAGE_TITLE = 'events';
require __DIR__ . '/inc/header.php';
?>

<h1>Upcoming Events</h1>

<div class="module">
  <div class="module-title">Val Verde Calendar</div>
  <div class="module-body">
<?php if ($res && $res->num_rows > 0): ?>
<table cellpadding="6" cellspacing="0" border="0" width="100%">
<?php while ($row = $res->fetch_assoc()): ?>
<tr valign="top" class="comment-row">
  <td width="100">
    <font size="-1" color="#666666"><?php echo h($row['when_dt']); ?></font>
  </td>
  <td>
    <b><a href="/event_view.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['title']); ?></a></b>
    <font size="-2" color="#666666">(<?php echo (int)$row['going']; ?> going)</font><br>
    <font size="-1"><?php echo h($row['location']); ?> &middot; hosted by <?php echo h($row['owner'] ? $row['owner'] : 'tom'); ?></font><br>
    <font size="-1"><?php echo h(substr($row['body'], 0, 140)); ?><?php if (strlen($row['body']) > 140) echo '...'; ?></font>
  </td>
</tr>
<?php endwhile; ?>
</table>
<?php else: ?>
<font size="-1">no upcoming events.</font>
<?php endif; ?>
  </div>
</div>

<?php if (cyspace_current_user_id() > 0): ?>
<p><font size="-1"><a href="/event_new.php">post a new event</a></font></p>
<?php endif; ?>

<?php require __DIR__ . '/inc/footer.php'; ?>
