<?php
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
cyspace_require_login();

$uid = cyspace_current_user_id();
$db  = cyspace_db();
$msg = '';
$err = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $target = isset($_POST['target']) ? (int)$_POST['target'] : 0;
    $score  = isset($_POST['score'])  ? (int)$_POST['score']  : 0;
    if ($target <= 0 || $target === $uid) {
        $err = 'invalid target.';
    } elseif ($score < 1 || $score > 5) {
        $err = 'score must be 1..5.';
    } else {
        $stmt = $db->prepare(
            'INSERT INTO user_ratings (rater_id, rated_id, score) VALUES (?, ?, ?)
             ON DUPLICATE KEY UPDATE score = VALUES(score), created_at = CURRENT_TIMESTAMP');
        $stmt->bind_param('iii', $uid, $target, $score);
        $stmt->execute();
        $msg = 'thanks for rating.';
    }
}

$tgt_id = isset($_GET['id']) ? (int)$_GET['id'] : 0;
if ($tgt_id > 0) {
    $stmt = $db->prepare(
        'SELECT u.id, u.username, u.avatar_path,
                AVG(r.score) AS avg_score, COUNT(r.score) AS n
         FROM users u LEFT JOIN user_ratings r ON r.rated_id = u.id
         WHERE u.id = ? GROUP BY u.id');
    $stmt->bind_param('i', $tgt_id);
    $stmt->execute();
    $tgt = $stmt->get_result()->fetch_assoc();
} else {
    $tgt = null;
}

$PAGE_TITLE = 'rate a profile';
require __DIR__ . '/inc/header.php';
?>

<h1>Rate-a-Profile</h1>

<?php if ($msg): ?><div class="module"><div class="module-body"><?php echo h($msg); ?></div></div><?php endif; ?>
<?php if ($err): ?><div class="flash"><?php echo h($err); ?></div><?php endif; ?>

<?php if ($tgt): ?>
<div class="module">
  <div class="module-title">Rate <?php echo h($tgt['username']); ?></div>
  <div class="module-body">
    <table cellpadding="6" border="0">
    <tr valign="top">
    <td><img src="<?php echo h(cyspace_avatar_url($tgt)); ?>" width="80" height="80" alt="" border="1"></td>
    <td>
      <p>average: <b><?php echo $tgt['n'] > 0 ? number_format((float)$tgt['avg_score'], 2) : 'unrated'; ?></b>
         (<?php echo (int)$tgt['n']; ?> ratings)</p>
      <form method="post" action="/ratecard.php">
        <input type="hidden" name="target" value="<?php echo (int)$tgt['id']; ?>">
        score:
        <?php for ($s = 1; $s <= 5; $s++): ?>
          <label><input type="radio" name="score" value="<?php echo (int)$s; ?>"<?php if ($s === 3) echo ' checked'; ?>><?php echo (int)$s; ?></label>
        <?php endfor; ?>
        <input type="submit" value="rate">
      </form>
    </td>
    </tr>
    </table>
  </div>
</div>
<?php else: ?>
<div class="module">
  <div class="module-body">
    <font size="-1">go to a user's profile and click "rate this profile".</font>
  </div>
</div>
<?php endif; ?>

<?php require __DIR__ . '/inc/footer.php'; ?>
