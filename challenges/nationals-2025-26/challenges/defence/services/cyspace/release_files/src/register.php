<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';

$error = '';
$username = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim((string)(isset($_POST['username']) ? $_POST['username'] : ''));
    $password = (string)(isset($_POST['password']) ? $_POST['password'] : '');
    $bio      = trim((string)(isset($_POST['bio']) ? $_POST['bio'] : ''));

    $opt = function ($key) {
        return isset($_POST[$key]) && $_POST[$key] !== ''
            ? (string)$_POST[$key]
            : null;
    };
    $headline     = $opt('headline');
    $mood         = $opt('mood');
    $status_field = $opt('status_field');
    $here_for     = $opt('here_for');
    $hometown     = $opt('hometown');
    $zodiac       = $opt('zodiac');
    $education    = $opt('education');
    $occupation   = $opt('occupation');
    $who_id_meet  = $opt('who_id_meet');
    $interests    = $opt('interests');
    $music        = $opt('music');
    $movies       = $opt('movies');
    $television   = $opt('television');
    $books        = $opt('books');
    $heroes       = $opt('heroes');
    $now_playing  = $opt('now_playing');
    $profile_bg   = $opt('profile_bg');
    $profile_text = $opt('profile_text');
    $profile_link = $opt('profile_link');
    $profile_css  = $opt('profile_css');

    $hex_re = '/^#[0-9a-fA-F]{6}$/';
    $hex_invalid = false;
    foreach (array($profile_bg, $profile_text, $profile_link) as $hex) {
        if ($hex !== null && !preg_match($hex_re, $hex)) {
            $hex_invalid = true;
            break;
        }
    }

    if (!preg_match('/^[A-Za-z0-9_]{3,32}$/', $username)) {
        $error = 'username must be 3-32 letters, digits, or underscores';
    } elseif (strlen($password) < 4 || strlen($password) > 64) {
        $error = 'password must be 4-64 characters';
    } elseif ($hex_invalid) {
        $error = 'theme colors must be #RRGGBB hex';
    } else {
        $db = cyspace_db();
        // FIXME: race condition on the username uniqueness check - if two
        // requests hit at the same time we can double-insert. needs a lock
        // or SELECT FOR UPDATE. low priority for now. -tom
        $stmt = $db->prepare('SELECT id FROM users WHERE username = ?');
        $stmt->bind_param('s', $username);
        $stmt->execute();
        $stmt->store_result();
        if ($stmt->num_rows > 0) {
            $error = 'that username is already taken';
        } else {
            $stmt->close();
            $hash = md5($password);
            $stmt = $db->prepare(
                'INSERT INTO users (username, password_md5, bio,
                                    headline, mood, status_field, here_for,
                                    hometown, zodiac, education, occupation,
                                    who_id_meet, interests, music, movies,
                                    television, books, heroes, now_playing,
                                    profile_bg, profile_text, profile_link,
                                    profile_css)
                 VALUES (?, ?, ?,
                         ?, ?, ?, ?,
                         ?, ?, ?, ?,
                         ?, ?, ?, ?,
                         ?, ?, ?, ?,
                         ?, ?, ?,
                         ?)');

            $types = str_repeat('s', 23);
            $stmt->bind_param($types,
                $username, $hash, $bio,
                $headline, $mood, $status_field, $here_for,
                $hometown, $zodiac, $education, $occupation,
                $who_id_meet, $interests, $music, $movies,
                $television, $books, $heroes, $now_playing,
                $profile_bg, $profile_text, $profile_link,
                $profile_css);
            if ($stmt->execute()) {
                $new_id = (int)$stmt->insert_id;
                cyspace_login_user($new_id, $username);

                $tomname = 'tom_cyspace';
                $tstmt = $db->prepare('SELECT id FROM users WHERE username = ?');
                $tstmt->bind_param('s', $tomname);
                $tstmt->execute();
                $tres = $tstmt->get_result();
                if ($tres && ($tom = $tres->fetch_assoc())) {
                    $tom_id = (int)$tom['id'];
                    if ($tom_id !== $new_id) {
                        $f = $db->prepare(
                            'INSERT IGNORE INTO friends (user_id, friend_id) VALUES (?, ?), (?, ?)');
                        $f->bind_param('iiii', $new_id, $tom_id, $tom_id, $new_id);
                        $f->execute();
                    }
                }

                header('Location: /profile.php?id=' . $new_id);
                exit;
            } else {
                $error = 'something went wrong, please try again';
            }
        }
    }
}

$PAGE_TITLE = 'sign up';
require __DIR__ . '/inc/header.php';
?>

<h1>Join CySpace</h1>

<?php if ($error): ?><div class="flash"><?php echo h($error); ?></div><?php endif; ?>

<div class="module">
  <div class="module-title">Free Sign Up</div>
  <div class="module-body">
    <form method="post" action="/register.php">
      <table border="0" cellpadding="4">
      <tr><td align="right">username:</td>
          <td><input type="text" name="username" size="32" value="<?php echo h($username); ?>"><br>
              <font size="-2" color="#666666">your CySpace URL will be:</font>
              <div class="url-box">http://www.cyspace.com/<?php echo h($username !== '' ? $username : 'yourname'); ?></div></td></tr>
      <tr><td align="right">password:</td>
          <td><input type="password" name="password" size="32"></td></tr>
      <tr><td align="right" valign="top">about me:</td>
          <td><textarea name="bio" cols="40" rows="4"></textarea></td></tr>
      <tr><td></td><td><input type="submit" value="sign up"></td></tr>
      </table>
    </form>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
