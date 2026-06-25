<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
$PAGE_TITLE = 'about cyspace';
require __DIR__ . '/inc/header.php';

$db = cyspace_db();
$users_count = 0;
$res = $db->query('SELECT COUNT(*) AS c FROM users');
if ($res) { $row = $res->fetch_assoc(); $users_count = (int)$row['c']; }
?>

<h1>About CySpace</h1>

<div class="module">
  <div class="module-title">What is CySpace?</div>
  <div class="module-body">
    <p>CySpace is the val verde community's social network, brought to you by
       the post-EMP recovery committee and running on hardware recovered from
       the old sector 7 datacentre.</p>
    <p>We currently have <b><?php echo (int)$users_count; ?></b> registered val
       verde-ites. tom is your friend.</p>
  </div>
</div>

<div class="module">
  <div class="module-title">Staff</div>
  <div class="module-body">
    <font size="-1">
    <ul style="padding-left: 14px; margin: 0;">
      <li><b>tom</b> &mdash; founder, sysadmin, your friend</li>
      <li><b>mandy</b> &mdash; head of moderation (mod_mandy in the logs)</li>
      <li><b>benny</b> &mdash; hardware, sector 7 mesh repeater</li>
      <li><b>jenn</b> &mdash; design / glitter approval</li>
    </ul>
    </font>
  </div>
</div>

<div class="module">
  <div class="module-title">Press</div>
  <div class="module-body">
    <font size="-1">
    <ul style="padding-left: 14px; margin: 0;">
      <li>"a place for friends" &mdash; <i>val verde gazette</i>, 2003-10</li>
      <li>"more friends than the dialup BBS used to" &mdash; <i>sector 7 monthly</i>, 2003-12</li>
    </ul>
    </font>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
