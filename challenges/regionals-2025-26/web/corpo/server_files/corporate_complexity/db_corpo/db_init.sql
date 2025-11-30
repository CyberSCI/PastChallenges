CREATE DATABASE IF NOT EXISTS corpo;
USE corpo;

GRANT FILE ON *.* to 'corpo'@'%';

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) UNIQUE,
  password VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS tokens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  token VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  product VARCHAR(255),
  quantity INT DEFAULT 0,
  company VARCHAR(255),
  contact VARCHAR(255),
  address VARCHAR(255),
  delivery_date VARCHAR(100),
  file VARCHAR(255),
  notes TEXT
);

INSERT INTO users (username, password) VALUES ('admin', 'cybersci{p1v0t_and_c0nqu3r}');
INSERT INTO users (username, password) VALUES ('customer1', 'Dedicator2-Villain-External');

INSERT INTO orders (user_id, product, quantity, address, notes) VALUES (1, 'Starter Kit', 1, '100 Example Rd', 'Initial order');