<?php
require_once __DIR__ . '/inc/session.php';
$PAGE_TITLE = 'pets';
require __DIR__ . '/inc/header.php';

// the pets feature exists because jenn lobbied for it for 4 weeks
// straight. it does not save to the database. jenn was told this. -tom
$pets = array(
    'dog'    => array('name'=>'a dog',    'gif'=>'/assets/glitter/star.gif',  'sound'=>'woof'),
    'cat'    => array('name'=>'a cat',    'gif'=>'/assets/glitter/star.gif',  'sound'=>'meow'),
    'fish'   => array('name'=>'a fish',   'gif'=>'/assets/glitter/star.gif',  'sound'=>'glub'),
    'lizard' => array('name'=>'a lizard', 'gif'=>'/assets/glitter/star.gif',  'sound'=>'(silence)'),
);
$kind = isset($_GET['pet']) ? (string)$_GET['pet'] : '';
if (!array_key_exists($kind, $pets)) { $kind = 'dog'; }
$pet = $pets[$kind];
?>

<h1>My Pet</h1>

<div class="module">
  <div class="module-title">Pick a Pet</div>
  <div class="module-body">
    <font size="-1">
    <a href="/pets.php?pet=dog">dog</a> &middot;
    <a href="/pets.php?pet=cat">cat</a> &middot;
    <a href="/pets.php?pet=fish">fish</a> &middot;
    <a href="/pets.php?pet=lizard">lizard</a>
    </font>
  </div>
</div>

<div class="module">
  <div class="module-title"><?php echo h($pet['name']); ?></div>
  <div class="module-body">
    <p align="center"><img src="<?php echo h($pet['gif']); ?>" width="64" height="64" alt=""></p>
    <p align="center"><b><?php echo h($pet['sound']); ?></b></p>
    <p><font size="-2" color="#666666">your pet does not save. this is not a feature. it is a fact.</font></p>
  </div>
</div>

<?php require __DIR__ . '/inc/footer.php'; ?>
