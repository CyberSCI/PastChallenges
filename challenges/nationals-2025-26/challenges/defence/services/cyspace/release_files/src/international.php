<?php
require_once __DIR__ . '/inc/session.php';
$PAGE_TITLE = 'international';
require __DIR__ . '/inc/header.php';

// the international localisations never shipped past stub state. the
// /international/ link is in the footer because tom hasn't deleted it. -mandy
$lang = isset($_GET['lang']) ? (string)$_GET['lang'] : '';
$valid = array('en', 'fr', 'es', 'de', 'jp', 'kr', 'cn');
if (!in_array($lang, $valid, true)) { $lang = 'en'; }
?>

<h1>CySpace International</h1>

<div class="module">
  <div class="module-title">Pick a language</div>
  <div class="module-body">
    <font size="-1">
    <a href="/international.php?lang=en">English (val verde)</a> &middot;
    <a href="/international.php?lang=fr">Fran&ccedil;ais</a> &middot;
    <a href="/international.php?lang=es">Espa&ntilde;ol</a> &middot;
    <a href="/international.php?lang=de">Deutsch</a> &middot;
    <a href="/international.php?lang=jp">&#26085;&#26412;&#35486;</a> &middot;
    <a href="/international.php?lang=kr">&#54620;&#44397;&#50612;</a> &middot;
    <a href="/international.php?lang=cn">&#20013;&#25991;</a>
    </font>
  </div>
</div>

<div class="module">
  <div class="module-title">Status</div>
  <div class="module-body">
    <font size="-1">
    <p>Selected: <b><?php echo h($lang); ?></b></p>
    <p>Honestly &mdash; localisation never made it past stub. the translation
       project lives in <a href="/groups.php?id=2">a small group</a> and they
       have about 40 strings done out of 600. patches welcome.</p>
    </font>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
