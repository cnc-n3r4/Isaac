<?php
/**
 * Isaac API Configuration
 * Edit API_KEY before uploading to GoDaddy.
 */

// API Key for authentication
define('API_KEY', 'isaac_prod_a8f3k2m9x7q4w1p5z6n8v2c3b7');

// Data directory (relative to this file)
define('DATA_DIR', __DIR__ . '/data/');

// Allowed session files
define('ALLOWED_FILES', [
    'preferences.json',
    'command_history.json',
    'aiquery_history.json',
    'task_history.json',
    'learned_autofixes.json',
    'learned_patterns.json'
]);

/**
 * Validate API key from Authorization header.
 * Returns true if valid, sends 401 and exits if invalid.
 */
function validate_api_key($headers) {
    $auth_header = $headers['Authorization'] ?? '';
    
    if ($auth_header !== 'Bearer ' . API_KEY) {
        http_response_code(401);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Unauthorized']);
        exit;
    }
}

/**
 * Validate filename is in allowed list.
 * Returns true if valid, sends 400 and exits if invalid.
 */
function validate_filename($filename) {
    if (!in_array($filename, ALLOWED_FILES)) {
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Invalid filename']);
        exit;
    }
}

/**
 * Get or create user directory.
 * Returns path to user's data folder.
 */
function get_user_dir($user_id) {
    // Sanitize user_id
    $user_id = preg_replace('/[^a-zA-Z0-9_-]/', '_', $user_id);
    
    $user_dir = DATA_DIR . $user_id . '/';
    
    if (!is_dir($user_dir)) {
        mkdir($user_dir, 0755, true);
    }
    
    return $user_dir;
}
?>