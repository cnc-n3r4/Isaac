<?php
/**
 * Get Session Endpoint
 * GET https://n3r4.xyz/isaac/api/get_session.php?user_id=X&filename=Y
 */

require_once 'config.php';

header('Content-Type: application/json');

// Get Authorization header (compatible with all servers)
$auth_header = '';
if (isset($_SERVER['HTTP_AUTHORIZATION'])) {
    $auth_header = $_SERVER['HTTP_AUTHORIZATION'];
} elseif (isset($_SERVER['REDIRECT_HTTP_AUTHORIZATION'])) {
    $auth_header = $_SERVER['REDIRECT_HTTP_AUTHORIZATION'];
}

// Validate API key
if ($auth_header !== 'Bearer ' . API_KEY) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

// Get parameters
if (!isset($_GET['user_id'], $_GET['filename'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing parameters']);
    exit;
}

$user_id = $_GET['user_id'];
$filename = $_GET['filename'];

// Validate filename
if (!in_array($filename, ALLOWED_FILES)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid filename']);
    exit;
}

// Get user directory
$user_id = preg_replace('/[^a-zA-Z0-9_-]/', '_', $user_id);
$user_dir = DATA_DIR . $user_id . '/';
$file_path = $user_dir . $filename;

// Check if file exists
if (!file_exists($file_path)) {
    // Return empty structure for new users
    echo json_encode([]);
    exit;
}

// Read and return file
$data = json_decode(file_get_contents($file_path), true);
echo json_encode($data);
?>