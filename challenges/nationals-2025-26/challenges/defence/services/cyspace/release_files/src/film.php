<?php
require_once __DIR__ . '/inc/session.php';
$PAGE_TITLE = 'film';
require __DIR__ . '/inc/header.php';

// hardcoded film list. there was a "submit a film review" form here
// but it got removed in 2003-10 after the great review-spam wave. -mandy
$films = array(
    array('title' => 'Predator',         'year' => 1987, 'note' => 'classic. val verde represent.'),
    array('title' => 'Commando',         'year' => 1985, 'note' => 'arnold loves val verde.'),
    array('title' => 'Die Hard',         'year' => 1988, 'note' => 'not val verde but tom keeps it on the list.'),
    array('title' => 'The Matrix',       'year' => 1999, 'note' => 'mandy says no spoilers.'),
    array('title' => 'Empire Records',   'year' => 1995, 'note' => 'tom puts this on whenever the dialup is slow.'),
    array('title' => 'Clueless',         'year' => 1995, 'note' => 'as if.'),
    array('title' => 'Donnie Darko',     'year' => 2001, 'note' => 'jenn approves.'),
    array('title' => 'Office Space',     'year' => 1999, 'note' => 'the mesh repeater has a tps cover sheet on it.'),
);
?>

<h1>Film</h1>

<div class="module">
  <div class="module-title">Tom's Recommended Films</div>
  <div class="module-body">
    <table cellpadding="4" cellspacing="0" border="0" width="100%">
    <tr bgcolor="#ffffcc">
      <th align="left">title</th><th align="left">year</th><th align="left">note</th>
    </tr>
    <?php foreach ($films as $f): ?>
    <tr>
      <td><b><?php echo h($f['title']); ?></b></td>
      <td><?php echo (int)$f['year']; ?></td>
      <td><font size="-1"><?php echo h($f['note']); ?></font></td>
    </tr>
    <?php endforeach; ?>
    </table>
  </div>
</div>

<p><font size="-2" color="#666666">to add a film, mail tom. user-submitted reviews disabled until mandy is back from sector 7.</font></p>

<?php require __DIR__ . '/inc/footer.php'; ?>
