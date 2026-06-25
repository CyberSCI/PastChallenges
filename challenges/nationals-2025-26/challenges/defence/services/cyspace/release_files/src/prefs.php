<?php
// theme prefs. the format is "CYP1:" + base64. see inc/prefs_classes.php
// for the wire format. v0 prefs were a plaintext json blob in localstorage
// but ie5 didn't have localstorage and val verde still has ie5 users.
// (looking at you, benny.) -tom
//
// TODO(tom): the inc/prefs_classes.php load/save pair is overdue for a
// rewrite to a class-injection-safe parser. it's on the list.
require_once __DIR__ . '/inc/db.php';
require_once __DIR__ . '/inc/session.php';
require_once __DIR__ . '/inc/prefs_classes.php';

$msg = '';
$prefs = null;

if (isset($_COOKIE['prefs']) && $_COOKIE['prefs'] !== '') {
    $prefs = theme_prefs_load_v1($_COOKIE['prefs']);
}

if (!($prefs instanceof ThemePrefs)) {
    $prefs = new ThemePrefs();
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $bg    = isset($_POST['bgcolor'])   ? (string)$_POST['bgcolor']   : '#e0e8ff';
    $tc    = isset($_POST['textcolor']) ? (string)$_POST['textcolor'] : '#000000';
    $blink = isset($_POST['blink'])     ? true : false;
    if (preg_match('/^#[0-9a-fA-F]{6}$/', $bg)) { $prefs->bgcolor   = $bg; }
    if (preg_match('/^#[0-9a-fA-F]{6}$/', $tc)) { $prefs->textcolor = $tc; }
    $prefs->blink = (bool)$blink;
    setcookie('prefs', theme_prefs_save_v1($prefs), time() + 60 * 60 * 24 * 30, '/');
    $msg = 'saved.';
}

$PAGE_TITLE = 'prefs';
require __DIR__ . '/inc/header.php';
?>

<h1>Customise My Page</h1>

<?php if ($msg): ?><div class="module"><div class="module-body"><?php echo h($msg); ?></div></div><?php endif; ?>

<table width="100%" cellpadding="6" cellspacing="0" border="0">
<tr valign="top">
<td>

<div class="module">
  <div class="module-title">Profile Customization</div>
  <div class="module-body">
    <form method="post" action="/prefs.php">
      <table border="0" cellpadding="4">
      <tr><td align="right">background colour:</td>
          <td><input type="text" name="bgcolor"   value="<?php echo h($prefs->bgcolor);   ?>" size="10"></td></tr>
      <tr><td align="right">text colour:</td>
          <td><input type="text" name="textcolor" value="<?php echo h($prefs->textcolor); ?>" size="10"></td></tr>
      <tr><td align="right">enable &lt;blink&gt;?</td>
          <td><input type="checkbox" name="blink" <?php echo $prefs->blink ? 'checked' : ''; ?>></td></tr>
      <tr><td></td><td><input type="submit" value="save"></td></tr>
      </table>
    </form>
  </div>
</div>

</td>
<td width="240">

<div class="module">
  <div class="module-title">Preview</div>
  <div class="module-body">
    <span style="background: <?php echo h($prefs->bgcolor); ?>; color: <?php echo h($prefs->textcolor); ?>; padding: 4px; display: inline-block;">
    preview text &mdash;
    <?php echo $prefs->blink ? '<blink>blink!</blink>' : 'no blink'; ?>
    </span>
    <p><font size="-2" color="#666666">your scheme is saved in a cookie. note: only this preview reflects it for now.</font></p>
  </div>
</div>

</td>
</tr>
</table>

<?php require __DIR__ . '/inc/footer.php'; ?>
