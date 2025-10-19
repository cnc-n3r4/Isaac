<?php


header('Content-Type: application/json');

echo json_encode([
    'status' => 'online',
    'timestamp' => date('c'),
    'version' => '2.0.0'
]);
?>