<?php

$host = getenv('CYSPACE_DB_HOST') ?: 'db';
$name = getenv('CYSPACE_DB_NAME') ?: 'cyspace';
$user = getenv('CYSPACE_DB_USER') ?: 'cyspace';
$pass = getenv('CYSPACE_DB_PASS') ?: 'cyspace';

// Admin credentials are part of the service contract
// If you try to change these TOM will freak out 
// Just solve the real vulnerability instead of trying to change the admin creds, please
$admin_user = 'admin';
$admin_pass = 'B8KkKmpWPYkdBCtSqJy2';

$mysqli = new mysqli($host, $user, $pass, $name);
if ($mysqli->connect_errno) {
    fwrite(STDERR, "seed-admins: cannot connect: " . $mysqli->connect_error . "\n");
    exit(1);
}

$stmt = $mysqli->prepare('SELECT id FROM admins WHERE username = ?');
$stmt->bind_param('s', $admin_user);
$stmt->execute();
$stmt->store_result();
if ($stmt->num_rows > 0) {
    echo "seed-admins: admin '{$admin_user}' already exists, skipping\n";
    exit(0);
}
$stmt->close();

$hash = password_hash($admin_pass, PASSWORD_BCRYPT);

$stmt = $mysqli->prepare('INSERT INTO admins (username, password_bcrypt) VALUES (?, ?)');
$stmt->bind_param('ss', $admin_user, $hash);
if (!$stmt->execute()) {
    fwrite(STDERR, "seed-admins: insert failed: " . $stmt->error . "\n");
    exit(1);
}
echo "seed-admins: inserted admin '{$admin_user}'\n";
