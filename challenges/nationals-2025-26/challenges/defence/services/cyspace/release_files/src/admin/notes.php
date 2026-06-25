<?php
// Tom's Admin Console. notes pad for staff. the highlight thing was
// added 2003-10-31 when mandy was triaging hundreds of bulletins and
// wanted to ctrl-F across all the recent notes at once. -tom
//
// TODO(tom): real per-admin notes (right now it's a global pad).
require_once __DIR__ . '/../inc/db.php';
require_once __DIR__ . '/../inc/session.php';
cyspace_require_admin();

$db = cyspace_db();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $title = trim((string)(isset($_POST['title']) ? $_POST['title'] : ''));
    $body  = trim((string)(isset($_POST['body'])  ? $_POST['body']  : ''));
    if ($title !== '') {
        $stmt = $db->prepare('INSERT INTO admin_notes (title, body) VALUES (?, ?)');
        $stmt->bind_param('ss', $title, $body);
        $stmt->execute();
    }
    header('Location: /admin/notes.php');
    exit;
}

$res = $db->query('SELECT id, title, body, created_at FROM admin_notes ORDER BY id DESC LIMIT 25');
$latest_res = $db->query('SELECT title FROM admin_notes ORDER BY id DESC LIMIT 1');
$latest = $latest_res ? $latest_res->fetch_assoc() : null;

$PAGE_TITLE = 'staff - notes';
require __DIR__ . '/../inc/header.php';
?>

<h1>Tom's Admin Console &middot; Notes</h1>
<p><font size="-1">
  logged in as <b><?php echo h(isset($_SESSION['admin_username']) ? $_SESSION['admin_username'] : ''); ?></b>
  &middot; <a href="/admin/users.php">users</a>
</font></p>

<script>
/* highlight a search term across the notes panel.
   pass ?highlight=foo to use. legacy admin convenience feature. */
var HIGHLIGHT = '<?php echo addslashes(isset($_GET['highlight']) ? (string)$_GET['highlight'] : ''); ?>';
function applyHighlight() {
    if (!HIGHLIGHT) { return; }
    var notes = document.getElementsByTagName('p');
    for (var i = 0; i < notes.length; i++) {
        var t = notes[i].innerHTML;
        if (t.indexOf(HIGHLIGHT) !== -1) {
            notes[i].style.background = '#ffffaa';
        }
    }
}
applyHighlight();
</script>

<?php if ($latest && !empty($latest['title'])): ?>
<div class="module">
  <div class="module-title">Last Note</div>
  <div class="module-body">
    <font size="-1">last note: <b><?php echo h($latest['title']); ?></b></font>
  </div>
</div>
<?php endif; ?>

<table width="100%" cellpadding="6" cellspacing="0" border="0">
<tr valign="top">
<td>

<div class="module">
  <div class="module-title">New Note</div>
  <div class="module-body">
    <form method="post" action="/admin/notes.php">
      <table border="0" cellpadding="4">
      <tr><td align="right">title:</td>
          <td><input type="text" name="title" size="48"></td></tr>
      <tr><td align="right" valign="top">body:</td>
          <td><textarea name="body" cols="60" rows="5"></textarea></td></tr>
      <tr><td></td><td><input type="submit" value="save note"></td></tr>
      </table>
    </form>
  </div>
</div>

<div class="module">
  <div class="module-title">Recent Notes</div>
  <div class="module-body">
<?php if ($res && $res->num_rows > 0): while ($row = $res->fetch_assoc()): ?>
<p>
  <b><?php echo h($row['title']); ?></b>
  <font size="-2" color="#666666"> &mdash; <?php echo h($row['created_at']); ?></font><br>
  <?php echo nl2br(h($row['body'])); ?>
</p>
<hr noshade size="1">
<?php endwhile; else: ?>
<font size="-1">no notes yet.</font>
<?php endif; ?>
  </div>
</div>

</td>
<td width="220">

<div class="module">
  <div class="module-title">Tom Says</div>
  <div class="module-body">
    <font size="-1">
      hey <?php echo h(isset($_SESSION['admin_username']) ? $_SESSION['admin_username'] : 'staff'); ?>!<br>
      thanks for moderating CySpace. remember:
      <ul style="padding-left: 14px; margin: 4px 0;">
        <li>delete the spam</li>
        <li>be nice</li>
        <li>tom is your friend</li>
      </ul>
      &mdash; tom
    </font>
  </div>
</div>

</td>
</tr>
</table>

<?php require __DIR__ . '/../inc/footer.php'; ?>
