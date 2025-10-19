<?php
/**
 * Save Session Endpoint
 * POST https://n3r4.xyz/isaac/api/save_session.php
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

// Parse request body
$input = json_decode(file_get_contents('php://input'), true);

if (!isset($input['user_id'], $input['filename'], $input['data'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required fields']);
    exit;
}

$user_id = $input['user_id'];
$filename = $input['filename'];
$data = $input['data'];

// Validate filename
if (!in_array($filename, ALLOWED_FILES)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid filename']);
    exit;
}

// Get user directory
$user_id = preg_replace('/[^a-zA-Z0-9_-]/', '_', $user_id);
$user_dir = DATA_DIR . $user_id . '/';

if (!is_dir($user_dir)) {
    mkdir($user_dir, 0755, true);
}

$file_path = $user_dir . $filename;

// Save data
file_put_contents($file_path, json_encode($data, JSON_PRETTY_PRINT));

// Response
echo json_encode([
    'success' => true,
    'message' => 'Session saved',
    'timestamp' => date('c')
]);
?>