<?php
require_once __DIR__ . '/inc/session.php';
$PAGE_TITLE = 'faq';
require __DIR__ . '/inc/header.php';

$topic = isset($_GET['topic']) ? (string)$_GET['topic'] : '';
$known_topics = array('signup', 'profile', 'pics', 'guestbook', 'mail', 'groups', 'glitter');
if (!in_array($topic, $known_topics, true)) { $topic = ''; }
?>

<h1>Frequently Asked Questions</h1>

<div class="module">
  <div class="module-title">Topics</div>
  <div class="module-body">
    <font size="-1">
    <a href="/faq.php?topic=signup">signup</a> &middot;
    <a href="/faq.php?topic=profile">profile</a> &middot;
    <a href="/faq.php?topic=pics">pics</a> &middot;
    <a href="/faq.php?topic=guestbook">guestbook</a> &middot;
    <a href="/faq.php?topic=mail">mail</a> &middot;
    <a href="/faq.php?topic=groups">groups</a> &middot;
    <a href="/faq.php?topic=glitter">glitter</a>
    </font>
  </div>
</div>

<?php if ($topic === '' || $topic === 'signup'): ?>
<div class="module">
  <div class="module-title">Signup</div>
  <div class="module-body">
    <p><b>Q: how do i sign up?</b><br>
       <font size="-1">A: <a href="/register.php">/register.php</a>. pick a username
       (letters/numbers/underscore) and a password.</font></p>
    <p><b>Q: i forgot my password.</b><br>
       <font size="-1">A: mail tom. password reset is on the TODO list since
       2003-09 (sorry).</font></p>
  </div>
</div>
<?php endif; ?>

<?php if ($topic === '' || $topic === 'profile'): ?>
<div class="module">
  <div class="module-title">Profile</div>
  <div class="module-body">
    <p><b>Q: how do i change my mood?</b><br>
       <font size="-1">A: <a href="/mood.php">/mood.php</a>.</font></p>
    <p><b>Q: how do i edit my about-me?</b><br>
       <font size="-1">A: <a href="/blurb.php">/blurb.php</a>.</font></p>
  </div>
</div>
<?php endif; ?>

<?php if ($topic === '' || $topic === 'pics'): ?>
<div class="module">
  <div class="module-title">Pics</div>
  <div class="module-body">
    <p><b>Q: what file types?</b><br>
       <font size="-1">A: .jpg .jpeg .png .gif &mdash; max 2MB.</font></p>
    <p><b>Q: there is an "upload_old" thing in the URL bar sometimes.</b><br>
       <font size="-1">A: yeah ignore it. it is gone since 2003-09 after the
       shell.gif thing.</font></p>
  </div>
</div>
<?php endif; ?>

<?php if ($topic === '' || $topic === 'guestbook'): ?>
<div class="module">
  <div class="module-title">Guestbook</div>
  <div class="module-body">
    <p><b>Q: can my friends leave a comment?</b><br>
       <font size="-1">A: yes, on your <a href="/guestbook.php?user_id=1">guestbook</a>.</font></p>
  </div>
</div>
<?php endif; ?>

<?php if ($topic === '' || $topic === 'mail'): ?>
<div class="module">
  <div class="module-title">Mail</div>
  <div class="module-body">
    <p><b>Q: how do i send mail?</b><br>
       <font size="-1">A: <a href="/mail/compose.php">/mail/compose.php</a>.</font></p>
  </div>
</div>
<?php endif; ?>

<?php if ($topic === '' || $topic === 'groups'): ?>
<div class="module">
  <div class="module-title">Groups</div>
  <div class="module-body">
    <p><b>Q: can i make a group?</b><br>
       <font size="-1">A: yes &mdash; <a href="/groups.php">groups</a>.</font></p>
  </div>
</div>
<?php endif; ?>

<?php if ($topic === '' || $topic === 'glitter'): ?>
<div class="module">
  <div class="module-title">Glitter</div>
  <div class="module-body">
    <p><b>Q: why does the page say "under 50KB"?</b><br>
       <font size="-1">A: the val verde mesh repeater is held together with
       sector 7 spare parts. mandy says 50KB or bust.</font></p>
  </div>
</div>
<?php endif; ?>

<?php require __DIR__ . '/inc/footer.php'; ?>
