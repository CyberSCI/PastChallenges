<?php
require_once __DIR__ . '/inc/session.php';
$PAGE_TITLE = 'promote cyspace';
require __DIR__ . '/inc/header.php';

$kind = isset($_GET['k']) ? (string)$_GET['k'] : '';
$valid_kinds = array('button', 'banner', 'badge');
if (!in_array($kind, $valid_kinds, true)) { $kind = 'button'; }
?>

<h1>Promote CySpace!</h1>

<div class="module">
  <div class="module-title">Spread the word</div>
  <div class="module-body">
    <p><font size="-1">tell your friends. tell your school. tell the val verde
       gazette (they already know but tell them anyway).</font></p>
    <p><font size="-1">format:
       <a href="/promote.php?k=button">button</a> &middot;
       <a href="/promote.php?k=banner">banner</a> &middot;
       <a href="/promote.php?k=badge">badge</a>
    </font></p>
  </div>
</div>

<div class="module">
  <div class="module-title">Code</div>
  <div class="module-body">
    <?php if ($kind === 'button'): ?>
      <p><b>88x31 button</b>:</p>
      <pre>&lt;a href="http://cyspace.valverde/"&gt;&lt;img src="http://cyspace.valverde/assets/promo/button.gif" width="88" height="31" border="0" alt="CySpace"&gt;&lt;/a&gt;</pre>
    <?php elseif ($kind === 'banner'): ?>
      <p><b>468x60 banner</b>:</p>
      <pre>&lt;a href="http://cyspace.valverde/"&gt;&lt;img src="http://cyspace.valverde/assets/promo/banner.gif" width="468" height="60" border="0" alt="CySpace - a place for friends"&gt;&lt;/a&gt;</pre>
    <?php else: ?>
      <p><b>120x60 badge</b>:</p>
      <pre>&lt;a href="http://cyspace.valverde/"&gt;&lt;img src="http://cyspace.valverde/assets/promo/badge.gif" width="120" height="60" border="0" alt="i&#39;m on cyspace"&gt;&lt;/a&gt;</pre>
    <?php endif; ?>
    <p><font size="-2" color="#666666">images are placeholder until benny re-renders them. -tom</font></p>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
