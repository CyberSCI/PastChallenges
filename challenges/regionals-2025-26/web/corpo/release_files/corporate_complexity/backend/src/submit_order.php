<?php
require_once __DIR__ . '/db.php';

$body = file_get_contents('php://input');
$data = json_decode($body, true);
$token = $mysqli->real_escape_string($data['token'] ?? '');

$order_data = $data['order'] ;

if (!is_array($order_data)) {
    json_resp(400, ['error' => 'Invalid order format']);
}

$product = $mysqli->real_escape_string($order_data['product'] ?? '');
$quantity = isset($order_data['quantity']) ? $order_data['quantity'] : 0;
$company = $mysqli->real_escape_string($order_data['company'] ?? '');
$contact = $mysqli->real_escape_string($order_data['contact'] ?? '');
$address = $mysqli->real_escape_string($order_data['address'] ?? '');
$delivery_date = $mysqli->real_escape_string($order_data['delivery_date'] ?? '');
$notes = $mysqli->real_escape_string($order_data['notes'] ?? '');
$file = $mysqli->real_escape_string($order_data['file'] ?? '');

$res = $mysqli->query("SELECT user_id FROM tokens WHERE token = '$token'");
if (!$res || $res->num_rows !== 1) {
    json_resp(401, ['error' => 'Invalid token']);
}
$row = $res->fetch_assoc();
$user_id = (int)$row['user_id'];

$insert = $mysqli->multi_query("
    INSERT INTO orders (user_id, product, quantity, company, contact, address, delivery_date, file, notes)
    VALUES ($user_id, '$product', $quantity, '$company', '$contact', '$address', '$delivery_date', '$file', '$notes')
");

if (!$insert) {
    json_resp(500, ['error' => 'Database error']);
}

json_resp(200, ['status' => 'ok']);
