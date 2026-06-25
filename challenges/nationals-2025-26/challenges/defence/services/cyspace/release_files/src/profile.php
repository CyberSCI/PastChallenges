<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$id = isset($_GET['id']) ? (int)$_GET['id'] : 0;
if ($id <= 0) {
    header('Location: /');
    exit;
}

$db = cyspace_db();

$stmt = $db->prepare(
    'SELECT id, username, bio, mood, avatar_path, headline, status_field, here_for,
            hometown, zodiac, education, occupation, who_id_meet, interests,
            music, movies, television, books, heroes, now_playing,
            profile_bg, profile_text, profile_link, profile_css, created_at
     FROM users WHERE id = ?');
$stmt->bind_param('i', $id);
$stmt->execute();
$res = $stmt->get_result();
$user = $res ? $res->fetch_assoc() : null;

if (!$user) {
    http_response_code(404);
    $PAGE_TITLE = 'not found';
    require __DIR__ . '/inc/header.php';
    echo '<h1>no such user</h1><p>that page does not exist.</p>';
    require __DIR__ . '/inc/footer.php';
    exit;
}

$stmt = $db->prepare(
    'SELECT u.id, u.username, u.avatar_path FROM friends f
     JOIN users u ON u.id = f.friend_id
     WHERE f.user_id = ? ORDER BY u.username LIMIT 8');
$stmt->bind_param('i', $id);
$stmt->execute();
$friends_res = $stmt->get_result();

$stmt = $db->prepare('SELECT COUNT(*) AS c FROM friends WHERE user_id = ?');
$stmt->bind_param('i', $id);
$stmt->execute();
$cres = $stmt->get_result();
$friend_count = $cres ? (int)$cres->fetch_assoc()['c'] : 0;

$stmt = $db->prepare(
    'SELECT g.author, g.body, g.created_at, u.avatar_path
     FROM guestbook g
     LEFT JOIN users u ON u.username = g.author
     WHERE g.target_user_id = ? ORDER BY g.id DESC LIMIT 10');
$stmt->bind_param('i', $id);
$stmt->execute();
$comments_res = $stmt->get_result();

function _detail($s) {
    $v = trim((string)$s);
    return $v === '' ? '&mdash;' : h($v);
}

function _hex($v) {
    return preg_match('/^#[0-9a-fA-F]{6}$/', (string)$v) ? (string)$v : '';
}
$bg   = _hex($user['profile_bg']);
$text = _hex($user['profile_text']);
$link = _hex($user['profile_link']);

$visitor_count = 1337 + (int)$user['id'] * 73;

$PAGE_TITLE = $user['username'];

$_uname_class = preg_match('/^[A-Za-z0-9_]+$/', $user['username']) ? $user['username'] : '';
$BODY_CLASS  = 'profile-of-' . (int)$user['id']
             . ($_uname_class !== '' ? ' profile-of-' . $_uname_class : '');

ob_start();
?>
<style type="text/css">
<?php if ($bg !== ''): ?>
body.profile-of-<?php echo (int)$user['id']; ?> { background: <?php echo $bg; ?>; }
<?php endif; ?>
<?php if ($text !== ''): ?>
body.profile-of-<?php echo (int)$user['id']; ?> { color: <?php echo $text; ?>; }
<?php endif; ?>
<?php if ($link !== ''): ?>
body.profile-of-<?php echo (int)$user['id']; ?> a { color: <?php echo $link; ?>; }
<?php endif; ?>
<?php if (!empty($user['profile_css'])): ?>
<?php echo htmlspecialchars($user['profile_css'], ENT_NOQUOTES, 'UTF-8'); ?>
<?php endif; ?>
</style>
<?php
$EXTRA_HEAD = ob_get_clean();

require __DIR__ . '/inc/header.php';
?>

<table width="100%" cellpadding="6" cellspacing="0" border="0">
<tr valign="top">

<!-- ======================== LEFT COLUMN ======================== -->
<td width="220">

  <!-- music player widget (top of left column, just like real MySpace) -->
  <?php if (!empty($user['now_playing'])): ?>
  <div class="module music">
    <div class="module-title">Now Playing</div>
    <div class="module-body">
      <div class="player">
        <span class="play">&#9654;</span>
        <span class="track"><?php echo h($user['now_playing']); ?></span>
        <div class="progress"><div class="bar"></div></div>
        <div class="ctl">[ <a href="#">+ add to my profile</a> ]</div>
      </div>
    </div>
  </div>
  <?php endif; ?>

  <!-- avatar + metadata stack -->
  <div class="module">
    <div class="module-title"><?php echo h($user['username']); ?></div>
    <div class="module-body" align="center">
      <img src="<?php echo h(cyspace_avatar_url($user)); ?>" alt="<?php echo h($user['username']); ?>'s avatar"
           width="160" height="160" border="1">
      <br>
      <b><?php echo h($user['username']); ?></b>
      <?php if (!empty($user['headline'])): ?>
        <br><font size="-2" color="#003399">&ldquo;<?php echo h($user['headline']); ?>&rdquo;</font>
      <?php endif; ?>
      <br>
      <span class="online-now">
        <img src="/assets/online_bolt.gif" width="12" height="12" alt="*"> Online Now!
      </span>

      <div class="meta-stack" align="left">
        <hr>
        <div>view my: <a href="#">Pics</a> | <a href="#">Videos</a> | <a href="#">Blog</a></div>
        <div class="views">Profile Views: <?php echo number_format($visitor_count); ?></div>
        <div><?php echo h($user['username']); ?> has
          <b><?php echo (int)$friend_count; ?></b> friends
          &middot; <a href="/guestbook.php?user_id=<?php echo (int)$user['id']; ?>">View All</a>
        </div>
        <div class="last-login">Last Login: today</div>
        <div><font size="-2" color="#666666">Member Since: <?php echo h(substr($user['created_at'], 0, 10)); ?></font></div>
        <hr>
        <div class="shortcut">
          <img src="/assets/online_bolt.gif" width="12" height="12" alt=""> <a href="#">Send Message</a>
        </div>
        <div class="shortcut">
          <img src="/assets/online_bolt.gif" width="12" height="12" alt=""> <a href="#">Add to Friends</a>
        </div>
      </div>
    </div>
  </div>

  <!-- contacting box -->
  <div class="module">
    <div class="module-title">Contacting <?php echo h($user['username']); ?></div>
    <table class="contact-table" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td><a href="#">Send Message</a></td>
      <td><a href="#">Forward to Friend</a></td>
    </tr>
    <tr>
      <td><a href="#">Add to Friends</a></td>
      <td><a href="#">Add to Favorites</a></td>
    </tr>
    <tr>
      <td><a href="#">Instant Message</a></td>
      <td><a href="#">Block User</a></td>
    </tr>
    <tr>
      <td><a href="#">Add to Group</a></td>
      <td><a href="#">Rank User</a></td>
    </tr>
    </table>
  </div>

  <!-- MySpace URL -->
  <div class="module">
    <div class="module-title">CySpace URL:</div>
    <div class="module-body">
      <div class="url-box">http://www.cyspace.com/<?php echo h($user['username']); ?></div>
    </div>
  </div>

  <!-- mood -->
  <div class="module">
    <div class="module-title">Mood</div>
    <div class="module-body mood">
      <span class="label">Mood:</span> <?php echo h($user['mood']); ?>
      <img src="<?php echo h(cyspace_mood_icon($user['mood'])); ?>" width="16" height="16" alt="">
    </div>
  </div>

  <!-- interests teaser -->
  <?php if (!empty($user['interests'])): ?>
  <div class="module">
    <div class="module-title"><?php echo h($user['username']); ?>'s Interests</div>
    <div class="module-body">
      <?php echo nl2br(h($user['interests'])); ?>
    </div>
  </div>
  <?php endif; ?>

  <!-- details key/value -->
  <div class="module">
    <div class="module-title"><?php echo h($user['username']); ?>'s Details</div>
    <div class="module-body">
      <table class="details-table" cellpadding="0" cellspacing="0" border="0">
        <tr><th>Status:</th>     <td><?php echo _detail($user['status_field']); ?></td></tr>
        <tr><th>Here for:</th>   <td><?php echo _detail($user['here_for']);   ?></td></tr>
        <tr><th>Hometown:</th>   <td><?php echo _detail($user['hometown']);   ?></td></tr>
        <tr><th>Body type:</th>  <td>&mdash;</td></tr>
        <tr><th>Ethnicity:</th>  <td>&mdash;</td></tr>
        <tr><th>Zodiac:</th>     <td><?php echo _detail($user['zodiac']);     ?></td></tr>
        <tr><th>Children:</th>   <td>&mdash;</td></tr>
        <tr><th>Smoke/Drink:</th><td>&mdash; / &mdash;</td></tr>
        <tr><th>Education:</th>  <td><?php echo _detail($user['education']);  ?></td></tr>
        <tr><th>Occupation:</th> <td><?php echo _detail($user['occupation']); ?></td></tr>
        <tr><th>Income:</th>     <td>none of your business</td></tr>
      </table>
    </div>
  </div>

</td>

<!-- ======================== MAIN COLUMN ======================== -->
<td>

  <h1><?php echo h($user['username']); ?> is in your extended network</h1>

  <h2><?php echo h($user['username']); ?>'s Latest Blog Entry [<a href="#">Subscribe to this Blog</a>]</h2>
  <div class="module-body">
    <font size="-2" color="#666666">no blog entries yet. check back soon.</font>
  </div>

  <!-- HM6: Blurbs parent header containing About me + Who I'd Like to Meet -->
  <h2><?php echo h($user['username']); ?>'s Blurbs</h2>
  <div class="module-body blurbs">
    <h3 class="label">About me:</h3>
    <div class="profile-bio"><?php echo nl2br(h($user['bio'])); ?></div>
    <h3 class="label">Who I'd Like to Meet:</h3>
    <div><?php echo nl2br(_detail($user['who_id_meet'])); ?></div>
  </div>

  <!-- interest grid -->
  <h2>Interests</h2>
  <table width="100%" cellpadding="4" cellspacing="0" border="0">
  <tr valign="top">
    <td width="100" align="right"><b>General:</b></td>
    <td><?php echo nl2br(_detail($user['interests'])); ?></td>
  </tr>
  <tr valign="top">
    <td align="right"><b>Music:</b></td>
    <td><?php echo nl2br(_detail($user['music'])); ?></td>
  </tr>
  <tr valign="top">
    <td align="right"><b>Movies:</b></td>
    <td><?php echo nl2br(_detail($user['movies'])); ?></td>
  </tr>
  <tr valign="top">
    <td align="right"><b>Television:</b></td>
    <td><?php echo nl2br(_detail($user['television'])); ?></td>
  </tr>
  <tr valign="top">
    <td align="right"><b>Books:</b></td>
    <td><?php echo nl2br(_detail($user['books'])); ?></td>
  </tr>
  <tr valign="top">
    <td align="right"><b>Heroes:</b></td>
    <td><?php echo nl2br(_detail($user['heroes'])); ?></td>
  </tr>
  </table>

  <!-- HM2: Top 8 (was Top 12) -->
  <h2><?php echo h($user['username']); ?>'s Friend Space (Top 8)
    <img src="/assets/glitter/friends.gif" width="140" height="16" alt="" style="vertical-align: middle; margin-left: 6px;">
  </h2>
  <div class="module-body top8">
  <?php if ($friends_res && $friends_res->num_rows > 0): ?>
    <?php while ($f = $friends_res->fetch_assoc()): ?>
      <div class="friend-cell">
        <a href="/profile.php?id=<?php echo (int)$f['id']; ?>">
        <img src="<?php echo h(cyspace_avatar_url($f)); ?>" width="80" height="80" alt=""></a><br>
        <a href="/profile.php?id=<?php echo (int)$f['id']; ?>"><?php echo h($f['username']); ?></a>
      </div>
    <?php endwhile; ?>
  <?php else: ?>
    <font size="-1" color="#666666">no friends yet. add some!</font>
  <?php endif; ?>
  </div>

  <!-- §1: inline comments + Add Comment form -->
  <a name="comments"></a>
  <h2><?php echo h($user['username']); ?>'s Friends Comments</h2>
  <div class="module-body">
  <?php if ($comments_res && $comments_res->num_rows > 0): while ($row = $comments_res->fetch_assoc()): ?>
    <table cellpadding="4" cellspacing="0" border="0" class="comment-row" width="100%">
    <tr valign="top">
      <td width="64">
        <img src="<?php echo h(cyspace_avatar_url(array('username' => $row['author'], 'avatar_path' => $row['avatar_path']))); ?>"
             width="50" height="50" alt="" border="1">
      </td>
      <td>
        <span class="comment-author"><?php echo h($row['author']); ?></span>
        <span class="comment-time">&mdash; <?php echo h($row['created_at']); ?></span>
        <div class="comment-body">
        <?php echo $row['body']; ?>
        </div>
      </td>
    </tr>
    </table>
  <?php endwhile; else: ?>
    <font size="-1" color="#666666">no comments yet. be the first!</font>
  <?php endif; ?>
  </div>

  <?php if (cyspace_current_user_id() > 0): ?>
  <div class="module">
    <div class="module-title">Add Comment</div>
    <div class="module-body">
      <form method="post" action="/post_message.php">
        <input type="hidden" name="user_id" value="<?php echo (int)$user['id']; ?>">
        <table border="0" cellpadding="2">
        <tr><td valign="top">message:</td>
            <td><textarea name="body" cols="60" rows="3"></textarea></td></tr>
        <tr><td></td><td><input type="submit" value="Post Comment"></td></tr>
        </table>
      </form>
      <font size="-2"><a href="/guestbook.php?user_id=<?php echo (int)$user['id']; ?>">View All Comments</a></font>
    </div>
  </div>
  <?php endif; ?>

</td>
</tr>
</table>

<?php require __DIR__ . '/inc/footer.php'; ?>
