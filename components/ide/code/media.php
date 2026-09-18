<?php
require_once __DIR__ . '/config.php';

function media_json($data, int $status = 200): void {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function media_fail(string $message, int $status = 400): void {
    media_json(['ok' => false, 'error' => $message], $status);
}

function media_config(string $key): array {
    $roots = defined('MEDIA_ROOTS') ? MEDIA_ROOTS : [];
    if (!isset($roots[$key]) || !is_array($roots[$key])) {
        media_fail('Unknown media root.', 404);
    }
    return $roots[$key];
}

function media_normalize(string $path): string {
    $path = str_replace('\\', '/', trim($path));
    $path = ltrim($path, '/');
    if ($path === '') return '';
    if (strpos($path, "\0") !== false || preg_match('~^[A-Za-z]:/~', $path)) {
        media_fail('Invalid media path.', 403);
    }
    $parts = [];
    foreach (explode('/', $path) as $part) {
        if ($part === '' || $part === '.') continue;
        if ($part === '..' || str_starts_with($part, '.')) {
            media_fail('Hidden paths and parent traversal are not allowed.', 403);
        }
        $parts[] = $part;
    }
    return implode('/', $parts);
}

function media_base(string $key): string {
    $config = media_config($key);
    $configured = rtrim(str_replace('\\', '/', (string)($config['path'] ?? '')), '/');
    if ($configured === '') media_fail('Media root has no configured path.', 500);
    if (!is_dir($configured)) @mkdir($configured, 0775, true);
    $real = realpath($configured);
    if ($real === false || !is_dir($real)) {
        media_fail('Media folder is unavailable: ' . ($config['label'] ?? $key), 500);
    }
    return rtrim(str_replace('\\', '/', $real), '/');
}

function media_sandbox(string $key, string $path, bool $mustExist = true): array {
    $base = media_base($key);
    $relative = media_normalize($path);
    $candidate = $relative === '' ? $base : $base . '/' . $relative;
    if ($mustExist) {
        $real = realpath($candidate);
        if ($real === false) media_fail('Media path does not exist.', 404);
        $real = str_replace('\\', '/', $real);
        if ($real !== $base && !str_starts_with($real, $base . '/')) {
            media_fail('Access outside the media folder is not allowed.', 403);
        }
        if (is_link($real)) media_fail('Symbolic links are not supported.', 403);
        return [$real, $relative];
    }

    $parentRelative = dirname($relative);
    if ($parentRelative === '.' || $parentRelative === '') $parentRelative = '';
    [$parent] = media_sandbox($key, $parentRelative, true);
    $name = basename($relative);
    if ($name === '' || $name === '.' || $name === '..' || str_starts_with($name, '.')) {
        media_fail('Invalid media filename.', 400);
    }
    return [str_replace('\\', '/', $parent . '/' . $name), $relative];
}

function media_extensions(string $key): array {
    $config = media_config($key);
    return array_map('strtolower', $config['extensions'] ?? []);
}

function media_kind(string $name): string {
    $extension = strtolower(pathinfo($name, PATHINFO_EXTENSION));
    if (in_array($extension, ['jpg', 'jpeg', 'png', 'webp'], true)) return 'image';
    if (in_array($extension, ['wav', 'mp3', 'ogg', 'flac'], true)) return 'audio';
    if ($extension === 'json') return 'json';
    return 'download';
}

function media_mime(string $extension): string {
    return match (strtolower($extension)) {
        'jpg', 'jpeg' => 'image/jpeg',
        'png' => 'image/png',
        'webp' => 'image/webp',
        'wav' => 'audio/wav',
        'mp3' => 'audio/mpeg',
        'ogg' => 'audio/ogg',
        'flac' => 'audio/flac',
        'json' => 'application/json; charset=utf-8',
        default => 'application/octet-stream',
    };
}

function media_detected_mime(string $path): string {
    if (class_exists('finfo')) {
        $finfo = new finfo(FILEINFO_MIME_TYPE);
        $value = $finfo->file($path);
        if (is_string($value)) return strtolower($value);
    }
    $value = function_exists('mime_content_type') ? @mime_content_type($path) : false;
    return is_string($value) ? strtolower($value) : 'application/octet-stream';
}

function media_validate_upload(string $path, string $extension): void {
    $allowedMimes = [
        'jpg' => ['image/jpeg'],
        'jpeg' => ['image/jpeg'],
        'png' => ['image/png'],
        'webp' => ['image/webp'],
        'wav' => ['audio/wav', 'audio/x-wav', 'audio/vnd.wave'],
        'mp3' => ['audio/mpeg', 'audio/mp3'],
        'ogg' => ['audio/ogg', 'application/ogg'],
        'flac' => ['audio/flac', 'audio/x-flac'],
        'json' => ['application/json', 'text/plain'],
    ];
    $detected = media_detected_mime($path);
    if (!isset($allowedMimes[$extension]) || !in_array($detected, $allowedMimes[$extension], true)) {
        media_fail('The uploaded file content does not match its extension.', 415);
    }
    if ($extension === 'json') {
        $decoded = json_decode((string)file_get_contents($path), true);
        if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded)) {
            media_fail('Uploaded JSON is not valid.', 415);
        }
    }
}

function media_relative(string $base, string $full): string {
    return ltrim(substr(str_replace('\\', '/', $full), strlen($base)), '/');
}

function media_tree_nodes(string $key, string $directory): array {
    $base = media_base($key);
    $items = @scandir($directory);
    if ($items === false) return [];
    $directories = [];
    $files = [];
    $allowed = media_extensions($key);
    foreach ($items as $name) {
        if ($name === '.' || $name === '..' || str_starts_with($name, '.')) continue;
        $full = str_replace('\\', '/', $directory . '/' . $name);
        if (is_link($full)) continue;
        $relative = media_relative($base, $full);
        if (is_dir($full)) {
            $directories[] = [
                'type' => 'dir', 'name' => $name, 'path' => $relative,
                'root' => $key, 'scope' => 'media',
                'children' => media_tree_nodes($key, $full),
            ];
        } elseif (is_file($full)) {
            $extension = strtolower(pathinfo($name, PATHINFO_EXTENSION));
            if (!in_array($extension, $allowed, true)) continue;
            $files[] = [
                'type' => 'file', 'name' => $name, 'path' => $relative,
                'root' => $key, 'scope' => 'media', 'kind' => media_kind($name),
                'size' => filesize($full), 'modified' => filemtime($full),
            ];
        }
    }
    usort($directories, fn($a, $b) => strnatcasecmp($a['name'], $b['name']));
    usort($files, fn($a, $b) => strnatcasecmp($a['name'], $b['name']));
    return array_merge($directories, $files);
}

function media_unique_upload(string $key, string $directory, string $originalName): array {
    $info = pathinfo($originalName);
    $baseName = preg_replace('/[^A-Za-z0-9._-]+/', '_', $info['filename'] ?? 'uploaded');
    $baseName = trim((string)$baseName, '._-');
    if ($baseName === '') $baseName = 'uploaded';
    $extension = strtolower($info['extension'] ?? '');
    $counter = 0;
    do {
        $suffix = $counter === 0 ? '' : '_' . $counter;
        $name = $baseName . $suffix . '.' . $extension;
        [$full, $relative] = media_sandbox($key, trim($directory . '/' . $name, '/'), false);
        $counter++;
    } while (file_exists($full));
    return [$full, $relative, $name];
}

$action = $_GET['action'] ?? $_POST['action'] ?? '';

if ($action === 'tree') {
    $roots = [];
    foreach ((defined('MEDIA_ROOTS') ? MEDIA_ROOTS : []) as $key => $config) {
        $base = media_base((string)$key);
        $roots[] = [
            'type' => 'dir', 'name' => $config['label'] ?? ucfirst((string)$key),
            'path' => '', 'root' => (string)$key, 'scope' => 'media',
            'children' => media_tree_nodes((string)$key, $base),
        ];
    }
    media_json(['ok' => true, 'roots' => $roots]);
}

if ($action === 'info') {
    $key = (string)($_GET['root'] ?? '');
    [$full, $relative] = media_sandbox($key, (string)($_GET['path'] ?? ''), true);
    if (!is_file($full)) media_fail('Media file was not found.', 404);
    media_json([
        'ok' => true,
        'root' => $key,
        'path' => $relative,
        'name' => basename($full),
        'kind' => media_kind(basename($full)),
        'modified' => filemtime($full),
    ]);
}

if ($action === 'file' || $action === 'download') {
    $key = (string)($_GET['root'] ?? '');
    [$full] = media_sandbox($key, (string)($_GET['path'] ?? ''), true);
    if (!is_file($full) || !is_readable($full)) media_fail('Media file is not readable.', 404);
    $extension = strtolower(pathinfo($full, PATHINFO_EXTENSION));
    if (!in_array($extension, media_extensions($key), true)) media_fail('Unsupported media type.', 403);
    header('X-Content-Type-Options: nosniff');
    header('Cache-Control: no-store');
    header('Content-Type: ' . media_mime($extension));
    $disposition = $action === 'download' ? 'attachment' : 'inline';
    header("Content-Disposition: $disposition; filename*=UTF-8''" . rawurlencode(basename($full)));
    header('Content-Length: ' . filesize($full));
    readfile($full);
    exit;
}

if ($action === 'upload') {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') media_fail('POST is required.', 405);
    $key = (string)($_POST['root'] ?? '');
    [$directory, $directoryRelative] = media_sandbox($key, (string)($_POST['dir'] ?? ''), true);
    if (!is_dir($directory)) media_fail('Upload destination must be a folder.', 400);
    if (!isset($_FILES['file']) || !is_uploaded_file($_FILES['file']['tmp_name'])) {
        media_fail('No uploaded file received.', 400);
    }
    if ($_FILES['file']['error'] !== UPLOAD_ERR_OK) media_fail('The upload did not complete.', 400);
    $maximum = defined('MAX_MEDIA_UPLOAD_BYTES') ? (int)MAX_MEDIA_UPLOAD_BYTES : 52428800;
    if ((int)$_FILES['file']['size'] > $maximum) media_fail('Uploaded media is too large.', 413);
    $originalName = basename((string)$_FILES['file']['name']);
    $extension = strtolower(pathinfo($originalName, PATHINFO_EXTENSION));
    if (!in_array($extension, media_extensions($key), true)) media_fail('This media type is not allowed.', 403);
    media_validate_upload($_FILES['file']['tmp_name'], $extension);
    [$destination, $relative, $finalName] = media_unique_upload($key, $directoryRelative, $originalName);
    if (!@move_uploaded_file($_FILES['file']['tmp_name'], $destination)) {
        media_fail('Could not store the uploaded media file.', 500);
    }
    @chmod($destination, 0664);
    media_json(['ok' => true, 'root' => $key, 'path' => $relative, 'name' => $finalName, 'kind' => media_kind($finalName), 'modified' => filemtime($destination)]);
}

if ($action === 'rename') {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') media_fail('POST is required.', 405);
    $key = (string)($_POST['root'] ?? '');
    [$source, $sourceRelative] = media_sandbox($key, (string)($_POST['path'] ?? ''), true);
    if (!is_file($source)) media_fail('Only media files can be renamed.', 400);

    $newName = trim((string)($_POST['newName'] ?? ''));
    if ($newName === '' || basename($newName) !== $newName || str_starts_with($newName, '.')) {
        media_fail('Enter a filename without a folder path.', 400);
    }
    if (!preg_match('/^[A-Za-z0-9][A-Za-z0-9._ -]*$/', $newName)) {
        media_fail('The filename contains unsupported characters.', 400);
    }

    $oldExtension = strtolower(pathinfo($source, PATHINFO_EXTENSION));
    $newExtension = strtolower(pathinfo($newName, PATHINFO_EXTENSION));
    if ($newExtension !== $oldExtension) {
        media_fail('Renaming must preserve the original file extension.', 400);
    }
    if (!in_array($newExtension, media_extensions($key), true)) {
        media_fail('This media type is not allowed.', 403);
    }

    $parentRelative = dirname($sourceRelative);
    if ($parentRelative === '.') $parentRelative = '';
    [$destination, $destinationRelative] = media_sandbox(
        $key,
        trim($parentRelative . '/' . $newName, '/'),
        false
    );
    if (file_exists($destination)) media_fail('A media file with that name already exists.', 409);
    if (!@rename($source, $destination)) media_fail('Could not rename the media file.', 500);
    media_json([
        'ok' => true,
        'root' => $key,
        'path' => $destinationRelative,
        'name' => $newName,
        'kind' => media_kind($newName),
        'modified' => filemtime($destination),
    ]);
}

if ($action === 'delete') {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') media_fail('POST is required.', 405);
    $key = (string)($_POST['root'] ?? '');
    [$file] = media_sandbox($key, (string)($_POST['path'] ?? ''), true);
    if (!is_file($file)) media_fail('Only media files can be deleted.', 400);
    $extension = strtolower(pathinfo($file, PATHINFO_EXTENSION));
    if (!in_array($extension, media_extensions($key), true)) {
        media_fail('This media type is not allowed.', 403);
    }
    if (!@unlink($file)) media_fail('Could not delete the media file.', 500);
    media_json(['ok' => true]);
}

media_fail('Unknown media action.', 404);
