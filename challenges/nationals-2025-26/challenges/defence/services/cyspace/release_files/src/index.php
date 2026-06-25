<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$_cyspace_news = array(
    'COMMS RESTORED TO SECTOR 7 &middot; THANKS BENNY',
    'TOM IS YOUR FRIEND (STILL)',
    'RUMOUR: AVRIL IS ON CYSPACE NOW',
    'WE MADE IT BACK ONLINE - DO NOT BREAK IT',
    'GLITTER GIFS UNDER 50KB PLEASE - LOAD TIMES',
    'POST-EMP UPLOAD QUOTA: 2MB - DEAL WITH IT',
);
$_cyspace_headline = $_cyspace_news[ array_rand($_cyspace_news) ];

$PAGE_TITLE = 'home';
require __DIR__ . '/inc/header.php';

$db = cyspace_db();
$recent = $db->query('SELECT id, username, mood, headline, avatar_path FROM users ORDER BY id DESC LIMIT 16');
?>

<marquee class="newsbar" scrolldelay="80" scrollamount="3">
&#9733; <?php echo h($_cyspace_headline); ?> &nbsp;&nbsp; &#9733;
&nbsp; CySpace.com is back &mdash; brought to you by the val verde post-EMP recovery committee
&nbsp; &#9733;
</marquee>

<table width="100%" cellpadding="6" cellspacing="0" border="0">
<tr valign="top">

<!-- left: welcome -->
<td>

<h1>welcome to CySpace</h1>

<div class="module">
  <div class="module-title">a place for friends</div>
  <div class="module-body">
    <p>The val verde community's favourite social network, back online since the recovery.</p>
    <p>
    <?php if (cyspace_current_user_id() > 0): ?>
      visit <a href="/profile.php?id=<?php echo (int)cyspace_current_user_id(); ?>">your page</a>,
      <a href="/upload_pic.php">upload a pic</a>,
      <a href="/prefs.php">customise your profile</a>,
      or browse the cool kids on the right.
    <?php else: ?>
      <a href="/register.php">sign up</a> or <a href="/login.php">log in</a> to leave messages
      on your friends' pages.
    <?php endif; ?>
    </p>
  </div>
</div>

<div class="module">
  <div class="module-title">CySpace Specials</div>
  <div class="module-body">
    <p><b>NEW! &middot; Customise your page colours</b><br>
       <font size="-1">Head to <a href="/prefs.php">prefs</a> and pick your background.</font></p>
    <p><b>NEW! &middot; Friend Space (Top 12)</b><br>
       <font size="-1">Now displays up to twelve friends with chunky 80px thumbnails.</font></p>
    <p><b>BUG &middot; Glitter gifs over 50KB</b><br>
       <font size="-1">Sorry &mdash; the recovered hardware can't take it. mod_mandy says so.</font></p>
  </div>
</div>

<?php if (cyspace_current_user_id() === 0): ?>
<div class="module">
  <div class="module-title">Member Login</div>
  <div class="module-body">
    <form method="post" action="/login.php">
      <table cellpadding="2" border="0">
      <tr><td align="right">username:</td>
          <td><input type="text" name="username" size="20"></td></tr>
      <tr><td align="right">password:</td>
          <td><input type="password" name="password" size="20"></td></tr>
      <tr><td></td><td><input type="submit" value="log in"></td></tr>
      </table>
    </form>
  </div>
</div>
<?php endif; ?>

</td>

<!-- right: cool new people -->
<td width="280">
<div class="module">
  <div class="module-title">Cool New People</div>
  <div class="module-body top8">
    <?php if ($recent && $recent->num_rows > 0): ?>
      <?php while ($row = $recent->fetch_assoc()): ?>
        <div class="friend-cell">
          <a href="/profile.php?id=<?php echo (int)$row['id']; ?>">
          <img src="<?php echo h(cyspace_avatar_url($row)); ?>" width="80" height="80" alt=""></a><br>
          <a href="/profile.php?id=<?php echo (int)$row['id']; ?>"><?php echo h($row['username']); ?></a><br>
          <font size="-2" color="#666666"><?php echo h($row['mood']); ?></font>
        </div>
      <?php endwhile; ?>
    <?php else: ?>
      <p>nobody yet. be the first!</p>
    <?php endif; ?>
  </div>
</div>
</td>

</tr>
</table>

<?php require __DIR__ . '/inc/footer.php'; ?>
