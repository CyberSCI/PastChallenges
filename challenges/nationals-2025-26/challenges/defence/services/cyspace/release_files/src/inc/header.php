<?php
if (!isset($PAGE_TITLE)) { $PAGE_TITLE = 'CySpace'; }
if (!isset($BODY_CLASS)) { $BODY_CLASS = ''; }
if (!isset($EXTRA_HEAD)) { $EXTRA_HEAD = ''; }
require_once __DIR__ . '/session.php';
?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
  "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title><?php echo h($PAGE_TITLE); ?> &mdash; CySpace</title>
<link rel="stylesheet" type="text/css" href="/assets/style.css">
<?php if ($EXTRA_HEAD !== '') { echo $EXTRA_HEAD; } ?>
</head>
<body bgcolor="#ffffff" text="#000000" link="#003399" vlink="#551a8b"<?php
    if ($BODY_CLASS !== '') { echo ' class="' . h($BODY_CLASS) . '"'; }
?>>

<table width="100%" cellpadding="0" cellspacing="0" border="0" class="banner">
<tr>
<td align="left" valign="middle" width="240">
  <a href="/"><img src="/assets/logo.gif" alt="CySpace.com" border="0" width="220" height="48"></a>
</td>
<td align="right" valign="middle" class="nav">
  <form method="get" action="/search.php">
    <input type="text" name="q" size="14" value="">
    <input type="submit" value="search">
  </form>
  &middot;
<?php if (cyspace_current_user_id() > 0): ?>
  Hello, <b><?php echo h(cyspace_current_username()); ?></b>!
  &middot; <a href="/profile.php?id=<?php echo (int)cyspace_current_user_id(); ?>">Home</a>
  &middot; <a href="/upload_pic.php">Pics</a>
  &middot; <a href="/prefs.php">Settings</a>
  &middot; <a href="/logout.php">Logout</a>
<?php else: ?>
  <a href="/login.php">Login</a>
  &middot; <a href="/register.php">Sign Up</a>
<?php endif; ?>
</td>
</tr>
<tr>
<td colspan="2" class="tagline">
  <img src="/assets/glitter/star.gif" width="16" height="16" alt="" style="vertical-align: middle;">
  <font color="#ffffff" size="-2"><i>a place for friends</i></font>
  <img src="/assets/glitter/star.gif" width="16" height="16" alt="" style="vertical-align: middle;">
</td>
</tr>
</table>

<div class="subnav">
<a href="/">Home</a> |
<a href="/browse.php">Browse</a> |
<a href="/search.php">Search</a> |
<a href="/invite.php">Invite</a> |
<a href="/film.php">Film</a> |
<a href="/mail/inbox.php">Mail</a> |
<a href="/blog/index.php">Blog</a> |
<a href="/favourites.php">Favorites</a> |
<a href="/forum.php">Forum</a> |
<a href="/groups.php">Groups</a> |
<a href="/events.php">Events</a> |
<a href="/videos.php">Videos</a> |
<a href="/music.php">Music</a> |
<a href="/comedy.php">Comedy</a> |
<a href="/classifieds.php">Classifieds</a> |
<a href="/bulletins/index.php">Bulletins</a>
</div>

<div class="page">
