<?php
require_once __DIR__ . '/db.php';

$body = file_get_contents('php://input');
$data = json_decode($body, true);
$username = $mysqli->real_escape_string($data['username'] ?? '');
$password = $mysqli->real_escape_string($data['password'] ?? '');

$res = $mysqli->query("SELECT id FROM users WHERE username = '$username' AND password = '$password'");
if ($res && $res->num_rows === 1) {
    $row = $res->fetch_assoc();
    $token = bin2hex(random_bytes(32));
    $user_id = $row['id'];
    $mysqli->query("DELETE FROM tokens WHERE user_id = $user_id");
    $mysqli->query("INSERT INTO tokens (user_id, token) VALUES ($user_id, '$token')");
    json_resp(200, ['token' => $token]);
} else {
    json_resp(401, ['error' => 'Invalid credentials']);
}
