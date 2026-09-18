<?php
/*
 * Simple PHP IDE configuration
 *
 * SECURITY NOTES:
 * - WORKING_DIR is the only folder where Python CRUD operations are allowed.
 * - MEDIA_ROOTS are separate allowlisted folders for media preview/upload/download.
 * - ACTIVE_SCRIPT_FILE may be outside WORKING_DIR, but it is never editable through normal CRUD.
 * - The "Run this File" button copies the currently opened editor content into ACTIVE_SCRIPT_FILE.
 */

define('IDE_TITLE', 'CodyNick Advanced On-Device IDE — Rev.B2');
define('CODYNICK_RELEASE_REVISION', 'Rev.B2');

// Optional logo. Use a relative URL, absolute URL, or leave empty.
define('IDE_LOGO_URL', '/assets/logo.png');

// Directory where the user can create/read/update/delete files and folders.
define('WORKING_DIR', '/home/client/userfiles');

// Active script shown as read-only and protected from rename/delete/save.
define('ACTIVE_SCRIPT_FILE', '/home/client/active_script.py');

// Limit upload size in bytes. Example: 100 kb.
define('MAX_UPLOAD_BYTES', 100 * 1024);

// Upload is restricted to these extensions.
define('ALLOWED_UPLOAD_EXTENSIONS', ['py']);

// Canonical student media folders. The IDE displays these as virtual roots;
// files are never copied into WORKING_DIR.
define('MEDIA_ROOTS', [
    'images' => [
        'label' => 'Images',
        'path' => '/home/client/images',
        'extensions' => ['jpg', 'jpeg', 'png', 'webp', 'json'],
    ],
    'audio' => [
        'label' => 'Audio',
        'path' => '/home/client/audio',
        'extensions' => ['wav', 'mp3', 'ogg', 'flac', 'json'],
    ],
]);

// Media can be substantially larger than Python source files.
define('MAX_MEDIA_UPLOAD_BYTES', 50 * 1024 * 1024);

// Files larger than this are not opened in the browser editor.
define('MAX_EDIT_BYTES', 101 * 1024);

// log file for upload logs
define('LOG_FILE', '/home/client/log.log');
define('LOG_TAIL_BYTES', 262144);
define('LOG_POLL_MS', 1000);
