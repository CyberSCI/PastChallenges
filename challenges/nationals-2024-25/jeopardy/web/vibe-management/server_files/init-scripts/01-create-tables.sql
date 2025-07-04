CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS management_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL
);

INSERT INTO management_keys (id, public_key, private_key) VALUES
  (
    '4dc15b91-77bf-4988-a596-57abc188657a',
    'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILFVdnxv0qBDjepfErZHoCN0D0n+D+UTSTVWMqrsY5ds',
    $PRIVATE_KEY_1$-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACCxVXZ8b9KgQ43qXxK2R6AjdA9J/g/lE0k1VjKq7GOXbAAAAJjYS4cw2EuH
MAAAAAtzc2gtZWQyNTUxOQAAACCxVXZ8b9KgQ43qXxK2R6AjdA9J/g/lE0k1VjKq7GOXbA
AAAECxBAqmjbGnxBvADl7spoGOVTk4g4+y0YSuj1+5zr4pe7FVdnxv0qBDjepfErZHoCN0
D0n+D+UTSTVWMqrsY5dsAAAAEXVidW50dUBzaW1wbGUtZGV2AQIDBA==
-----END OPENSSH PRIVATE KEY-----
$PRIVATE_KEY_1$
  ),
  (
    '45fbe025-befb-4500-8872-4cbe919df2ec',
    'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGM5GseD3TXL4XiGWIqfgmmF9hwutu1slCDsJVcxRUUh',
    $PRIVATE_KEY_2$-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBjORrHg901y+F4hliKn4JphfYcLrbtbJQg7CVXMUVFIQAAAJgxHQcmMR0H
JgAAAAtzc2gtZWQyNTUxOQAAACBjORrHg901y+F4hliKn4JphfYcLrbtbJQg7CVXMUVFIQ
AAAEBlfYlV+FOFUwTCOsHEVaNOksPX4v5yMaU2laNAyqju62M5GseD3TXL4XiGWIqfgmmF
9hwutu1slCDsJVcxRUUhAAAAEXVidW50dUBzaW1wbGUtZGV2AQIDBA==
-----END OPENSSH PRIVATE KEY-----
$PRIVATE_KEY_2$
  ),
  (
    'e2cfac45-7082-4c36-abaa-dfeafe565187',
    'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINeDSB1VVYeie//+0KZta8+3UOAI0WU7vh8DCt0Mt1yV',
    $PRIVATE_KEY_3$-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACDXg0gdVVWHonv//tCmbWvPt1DgCNFlO74fAwrdDLdclQAAAJg5wLk1OcC5
NQAAAAtzc2gtZWQyNTUxOQAAACDXg0gdVVWHonv//tCmbWvPt1DgCNFlO74fAwrdDLdclQ
AAAEBPlo7HhjSNXtnH+2Tpq8TgJ8kEXrmy4Ys04pQgTRjRxteDSB1VVYeie//+0KZta8+3
UOAI0WU7vh8DCt0Mt1yVAAAAEXVidW50dUBzaW1wbGUtZGV2AQIDBA==
-----END OPENSSH PRIVATE KEY-----
$PRIVATE_KEY_3$
  );