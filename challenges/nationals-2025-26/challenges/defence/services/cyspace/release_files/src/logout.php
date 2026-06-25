<?php
require_once __DIR__ . '/inc/session.php';
cyspace_logout();
header('Location: /');
exit;
