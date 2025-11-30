<?php
require_once __DIR__ . '/lib/order_client.php';

$backend = getenv('BACKEND_HOST');

$upload_dir = getenv('UPLOAD_DIR');
if (!is_dir($upload_dir)) {
    mkdir($upload_dir, 0755, true);
}

$message = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $token = $_COOKIE['token'] ?? '';
    $product = $_POST['product'] ?? '';
    $quantity = (int)($_POST['quantity'] ?? 0);
    $company = $_POST['company'] ?? '';
    $contact = $_POST['contact'] ?? '';
    $address = $_POST['address'] ?? '';
    $delivery = $_POST['delivery_date'] ?? '';
    $notes = $_POST['notes'] ?? '';

    if (isset($_FILES['file']) && $_FILES['file']['error'] === UPLOAD_ERR_OK) {
        $extension = pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION);
        $checksum = md5_file($_FILES['file']['tmp_name']);
        $file_name = $checksum . '.' . $extension;
        $target_path = $upload_dir . '/' . $file_name;
        move_uploaded_file($_FILES['file']['tmp_name'], $target_path);
    }

    $order = [
        'product' => $product,
        'quantity' => $quantity,
        'company' => $company,
        'contact' => $contact,
        'address' => $address,
        'delivery_date' => $delivery,
        'file' => $file_name ?? null,
        'notes' => $notes,
    ];

    $res = submit_order_request($backend, $token, $order);
    if ($res === false) {
        $message = 'Backend unreachable';
    } elseif (isset($res['status'])) {
        $message = 'Order submitted';
    } else {
        $message = 'Order failed: ' . htmlspecialchars($res['error'] ?? 'unknown');
    }
}
?>
<!doctype html>
<html>
  <body>
    <?php if ($message): ?>
      <p><?php echo htmlspecialchars($message); ?></p>
    <?php endif; ?>

    <h2>Submit Order</h2>
    <form method="post" action="/order.php" enctype="multipart/form-data">
      Product: <input name="product"><br>
      Quantity: <input name="quantity" type="number" value="1"><br>
      Company: <input name="company"><br>
      Contact Person: <input name="contact"><br>
      Delivery Address: <input name="address"><br>
      Delivery Date: <input name="delivery_date" type="date"><br>
      Additional Notes: <input name="notes"><br>
      Attachment (optional): <input type="file" name="file"><br>
      <input type="submit" value="Submit Order">
    </form>

    <p><a href="/login.php">Login</a></p>
  </body>
</html>
