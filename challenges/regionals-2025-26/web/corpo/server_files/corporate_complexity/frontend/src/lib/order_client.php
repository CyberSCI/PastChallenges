<?php
function submit_order_request($backend, $token, $order) {
    $payload = json_encode(['token'=>$token, 'order'=>$order]);

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, rtrim($backend, '/') . '/submit_order.php');
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);

    $result = curl_exec($ch);
    if ($result === false) {
        curl_close($ch);
        return false;
    }
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode < 200 || $httpCode >= 300) {
        $decoded = json_decode($result, true);
        return $decoded ?: false;
    }

    return json_decode($result, true);
}
