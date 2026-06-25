<?php

function cyspace_db() {
    static $mysqli = null;
    if ($mysqli !== null) {
        return $mysqli;
    }
    $host = getenv('CYSPACE_DB_HOST') ?: 'db';
    $name = getenv('CYSPACE_DB_NAME') ?: 'cyspace';
    $user = getenv('CYSPACE_DB_USER') ?: 'cyspace';
    $pass = getenv('CYSPACE_DB_PASS') ?: 'cyspace';

    $mysqli = @new mysqli($host, $user, $pass, $name);
    if ($mysqli->connect_errno) {
        error_log('cyspace_db connect failed: ' . $mysqli->connect_error);
        http_response_code(500);
        echo 'service temporarily unavailable';
        exit;
    }
    $mysqli->set_charset('utf8mb4');
    return $mysqli;
}
