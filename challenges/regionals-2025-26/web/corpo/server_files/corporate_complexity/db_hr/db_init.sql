CREATE DATABASE IF NOT EXISTS hr;
USE hr;

CREATE TABLE IF NOT EXISTS employees (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  position VARCHAR(100),
  salary INT,
  notes TEXT
);

INSERT INTO employees (name, position, salary, notes) VALUES ('John Doe', 'System Administrator', 100000, 'cybersci{s3nsit1ve_dat4_p1llag3d}');