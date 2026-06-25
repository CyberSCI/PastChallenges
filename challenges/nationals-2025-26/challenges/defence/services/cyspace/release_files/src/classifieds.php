<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$db = cyspace_db();
$cat = isset($_GET['cat']) ? (string)$_GET['cat'] : '';
$valid_cats = array('forsale', 'wanted', 'services', 'free', 'trade');

if ($cat !== '' && in_array($cat, $valid_cats, true)) {
    $stmt = $db->prepare(
        'SELECT id, category, title, body, price_cents, location, created_at
         FROM classifieds WHERE category = ?
         ORDER BY id DESC LIMIT 50');
    $stmt->bind_param('s', $cat);
    $stmt->execute();
    $listings = $stmt->get_result();
} else {
    $cat = '';
    $listings = $db->query(
        'SELECT id, category, title, body, price_cents, location, created_at
         FROM classifieds ORDER BY id DESC LIMIT 50');
}

$PAGE_TITLE = 'classifieds';
require __DIR__ . '/inc/header.php';
?>

<h1>CySpace Classifieds</h1>

<div class="module">
  <div class="module-title">Categories</div>
  <div class="module-body">
    <font size="-1">
    <a href="/classifieds.php">all</a> &middot;
    <a href="/classifieds.php?cat=forsale">for sale</a> &middot;
    <a href="/classifieds.php?cat=wanted">wanted</a> &middot;
    <a href="/classifieds.php?cat=services">services</a> &middot;
    <a href="/classifieds.php?cat=free">free</a> &middot;
    <a href="/classifieds.php?cat=trade">trade</a>
    </font>
  </div>
</div>

<div class="module">
  <div class="module-title"><?php echo $cat === '' ? 'Latest' : h($cat); ?></div>
  <div class="module-body">
<?php if ($listings && $listings->num_rows > 0): ?>
<table cellpadding="6" cellspacing="0" border="0" width="100%">
<?php while ($row = $listings->fetch_assoc()): ?>
<tr valign="top" class="comment-row">
  <td width="80"><font size="-1" color="#666666"><?php echo h($row['category']); ?></font></td>
  <td>
    <b><?php echo h($row['title']); ?></b><br>
    <font size="-1"><?php echo nl2br(h($row['body'])); ?></font><br>
    <font size="-2" color="#666666">
      <?php if ($row['price_cents']): ?>
        $<?php echo number_format(((int)$row['price_cents']) / 100, 2); ?> &middot;
      <?php endif; ?>
      <?php if ($row['location']): ?>
        <?php echo h($row['location']); ?> &middot;
      <?php endif; ?>
      <?php echo h($row['created_at']); ?>
    </font>
  </td>
</tr>
<?php endwhile; ?>
</table>
<?php else: ?>
<font size="-1">nothing listed in this category yet.</font>
<?php endif; ?>
  </div>
</div>

<p><font size="-2" color="#666666">posting your own listing is on tom's TODO. for now, mail tom and he will add it.</font></p>

<?php require __DIR__ . '/inc/footer.php'; ?>
