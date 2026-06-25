<?php
require_once __DIR__ . '/inc/session.php';
$PAGE_TITLE = 'comedy';
require __DIR__ . '/inc/header.php';

// hardcoded list of jokes mandy approved. NO USER SUBMISSIONS — last
// time we let people submit, the dialup kids posted nothing but
// "ur mom" jokes. -tom 2003-11
$jokes = array(
    "the val verde mesh repeater walks into a bar. the bartender says, "
        . "'why the long ping?'",
    "knock knock. who's there? tom. tom who? exactly.",
    "two glitter gifs walk into a bandwidth cap.",
    "how many recovery committee members does it take to change a "
        . "lightbulb? we are still recovering, please be patient.",
    "i told my crush i had a cyspace and now they have one too. "
        . "tom is also their friend.",
    "the only thing slower than dialup is mandy's response time to "
        . "abuse reports on a friday.",
    "what's the difference between sector 7 and sector 8? sector 8 has "
        . "a working air conditioner.",
);
$pick = $jokes[array_rand($jokes)];
?>

<h1>Comedy Page</h1>

<div class="module">
  <div class="module-title">Joke of the Refresh</div>
  <div class="module-body">
    <p style="font-style: italic;"><?php echo h($pick); ?></p>
    <p><font size="-2"><a href="/comedy.php">tell me another</a></font></p>
  </div>
</div>

<div class="module">
  <div class="module-title">Comedy Groups</div>
  <div class="module-body">
    <font size="-1">
    <ul>
      <li><a href="/groups.php?cat=arts">arts groups</a> include the val verde improv squad</li>
      <li>jokes about the dialup are welcome &mdash; jokes about mandy are not</li>
    </ul>
    </font>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
