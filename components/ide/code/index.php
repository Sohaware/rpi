<?php
require_once __DIR__ . '/config.php';
session_start();

if (!defined('MAX_EDIT_BYTES')) define('MAX_EDIT_BYTES', 1048576);
if (!defined('MAX_UPLOAD_BYTES')) define('MAX_UPLOAD_BYTES', 1048576);
if (!defined('ALLOWED_UPLOAD_EXTENSIONS')) define('ALLOWED_UPLOAD_EXTENSIONS', ['py']);
// Authentication is intentionally not used on this local device IDE.
// The previous time-limited session token/CSRF check is disabled by design.

function j($data, int $status = 200): void {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}
function fail(string $msg, int $status = 400): void { j(['ok'=>false, 'error'=>$msg], $status); }
function csrf(): void { return; }
function ensure_paths(): void {
    if (!is_dir(WORKING_DIR)) @mkdir(WORKING_DIR, 0775, true);
    if (!is_dir(WORKING_DIR)) fail('WORKING_DIR could not be created or is not a directory.', 500);
    if (!file_exists(ACTIVE_SCRIPT_FILE)) {
        $p = dirname(ACTIVE_SCRIPT_FILE);
        if (!is_dir($p)) @mkdir($p, 0775, true);
        @touch(ACTIVE_SCRIPT_FILE);
    }
    if (defined('LOG_FILE') && LOG_FILE !== '') {
        $p = dirname(LOG_FILE);
        if (!is_dir($p)) @mkdir($p, 0775, true);
        if (!file_exists(LOG_FILE)) @touch(LOG_FILE);
    }
}
function base_dir(): string {
    $b = realpath(WORKING_DIR);
    if ($b === false || !is_dir($b)) fail('Invalid WORKING_DIR.', 500);
    return rtrim(str_replace('\\', '/', $b), '/');
}
function active_path(): string { return str_replace('\\', '/', realpath(ACTIVE_SCRIPT_FILE) ?: ACTIVE_SCRIPT_FILE); }
function normalize_rel(string $p): string {
    $p = str_replace('\\', '/', trim($p));
    $p = ltrim($p, '/');
    if ($p === '' || strpos($p, "\0") !== false) return '';
    if (preg_match('~^[A-Za-z]:/~', $p)) fail('Absolute paths are not allowed.', 403);
    $out = [];
    foreach (explode('/', $p) as $part) {
        if ($part === '' || $part === '.') continue;
        if ($part === '..') fail('Parent-directory traversal is not allowed.', 403);
        $out[] = $part;
    }
    return implode('/', $out);
}
function sandbox(string $rel, bool $mustExist = true): array {
    $base = base_dir();
    $rel = normalize_rel($rel);
    $candidate = $rel === '' ? $base : $base . '/' . $rel;
    $candidate = str_replace('\\', '/', $candidate);
    if ($mustExist) {
        $real = realpath($candidate);
        if ($real === false) fail('Path does not exist.', 404);
        $real = str_replace('\\', '/', $real);
        if ($real !== $base && strpos($real, $base . '/') !== 0) fail('Access outside working directory is not allowed.', 403);
        return [$real, $rel];
    }
    $parentRel = dirname($rel);
    if ($parentRel === '.' || $parentRel === '') $parentRel = '';
    [$parent] = sandbox($parentRel, true);
    $name = basename($rel);
    if ($name === '' || $name === '.' || $name === '..') fail('Invalid filename.', 400);
    $full = str_replace('\\', '/', $parent . '/' . $name);
    if ($full !== $base && strpos($full, $base . '/') !== 0) fail('Access outside working directory is not allowed.', 403);
    return [$full, $rel];
}
function is_active(string $p): bool {
    $r = realpath($p);
    $a = realpath(ACTIVE_SCRIPT_FILE);
    if ($r && $a) return str_replace('\\','/',$r) === str_replace('\\','/',$a);
    return str_replace('\\','/',$p) === str_replace('\\','/',ACTIVE_SCRIPT_FILE);
}
function rel_from_base(string $full): string {
    $base = base_dir();
    $full = str_replace('\\','/', $full);
    return ltrim(substr($full, strlen($base)), '/');
}
function list_tree(string $dir): array {
    $items = @scandir($dir);
    if ($items === false) return [];
    $dirs = []; $files = [];
    foreach ($items as $name) {
        if ($name === '.' || $name === '..') continue;
        $full = str_replace('\\','/', $dir . '/' . $name);
        if (is_link($full)) continue;
        if (is_dir($full)) {
            $dirs[] = ['type'=>'dir','name'=>$name,'path'=>rel_from_base($full),'children'=>list_tree($full)];
        } elseif (is_file($full)) {
            $files[] = ['type'=>'file','name'=>$name,'path'=>rel_from_base($full),'size'=>filesize($full),'modified'=>filemtime($full)];
        }
    }
    usort($dirs, fn($a,$b)=>strnatcasecmp($a['name'],$b['name']));
    usort($files, fn($a,$b)=>strnatcasecmp($a['name'],$b['name']));
    return array_merge($dirs, $files);
}
function delete_recursive(string $p): void {
    if (is_file($p)) { if (!@unlink($p)) fail('Could not delete file.', 500); return; }
    if (!is_dir($p)) fail('Invalid delete target.', 400);
    $items = @scandir($p);
    if ($items === false) fail('Could not read folder.', 500);
    foreach ($items as $i) {
        if ($i === '.' || $i === '..') continue;
        $c = $p . '/' . $i;
        if (is_link($c)) fail('Symbolic links are not supported.', 403);
        delete_recursive($c);
    }
    if (!@rmdir($p)) fail('Could not delete folder.', 500);
}
function unique_upload_path(string $dirRel, string $originalName): array {
    $pi = pathinfo($originalName);
    $baseName = $pi['filename'] ?? 'uploaded';
    $ext = isset($pi['extension']) && $pi['extension'] !== '' ? '.' . $pi['extension'] : '';
    $safeBase = preg_replace('/[^A-Za-z0-9._-]+/', '_', $baseName);
    $safeBase = trim($safeBase, '._-');
    if ($safeBase === '') $safeBase = 'uploaded';
    $candidateName = $safeBase . $ext;
    $i = 1;
    while (true) {
        [$candidateFull, $candidateRel] = sandbox(trim($dirRel . '/' . $candidateName, '/'), false);
        if (!file_exists($candidateFull)) return [$candidateFull, $candidateRel, $candidateName];
        $candidateName = $safeBase . '_' . $i . $ext;
        $i++;
    }
}
function read_log_chunk(string $file, int $offset = 0, int $max = 262144): array {
    clearstatcache(true, $file);
    $size = filesize($file);
    if ($size === false) fail('Could not inspect log file.', 500);

    if ($offset < 0 || $offset > $size) {
        $offset = max(0, $size - $max);
    }

    $fh = fopen($file, 'rb');
    if (!$fh) fail('Could not open log file.', 500);
    fseek($fh, $offset, SEEK_SET);
    $data = stream_get_contents($fh, $max);
    $next = ftell($fh);
    fclose($fh);
    return ['content' => $data ?: '', 'offset' => $next ?: $size, 'size' => $size];
}

ensure_paths();
$action = $_GET['action'] ?? $_POST['action'] ?? '';
if ($action !== '') {
    switch ($action) {
        case 'tree': j(['ok'=>true, 'tree'=>list_tree(base_dir())]);
        case 'read':
            $path = $_GET['path'] ?? '';
            if ($path === '__ACTIVE__') {
                $full = active_path();
                if (!is_file($full) || !is_readable($full)) fail('Active script is not readable.', 500);
                if (filesize($full) > MAX_EDIT_BYTES) fail('Active script is too large to open.', 413);
                j(['ok'=>true,'content'=>file_get_contents($full),'readOnly'=>true,'active'=>true,'path'=>'__ACTIVE__','name'=>basename($full),'modified'=>filemtime($full)]);
            }
            [$full, $rel] = sandbox($path, true);
            if (!is_file($full)) fail('Only files can be opened.', 400);
            if (filesize($full) > MAX_EDIT_BYTES) fail('File is too large to open.', 413);
            j(['ok'=>true,'content'=>file_get_contents($full),'readOnly'=>false,'active'=>false,'path'=>$rel,'name'=>basename($full),'modified'=>filemtime($full)]);
        case 'save':
            csrf();
            [$full] = sandbox($_POST['path'] ?? '', true);
            if (!is_file($full)) fail('Only files can be saved.', 400);
            if (is_active($full)) fail('The active script is read-only.', 403);
            if (file_put_contents($full, $_POST['content'] ?? '', LOCK_EX) === false) fail('Could not save file.', 500);
            clearstatcache(true, $full);
            j(['ok'=>true,'modified'=>filemtime($full)]);
        case 'run':
            csrf();
            $active = ACTIVE_SCRIPT_FILE;
            $parent = dirname($active);
            if (!is_dir($parent)) @mkdir($parent, 0775, true);
            $studentContent = (string)($_POST['content'] ?? '');
            $runId = bin2hex(random_bytes(8));
            $separator = ($studentContent === '' || str_ends_with($studentContent, "\n"))
                ? ''
                : PHP_EOL;
            $activeContent = $studentContent
                . $separator
                . '# CODYNICK_RUN_ID: '
                . $runId
                . PHP_EOL;
            if (file_put_contents($active, $activeContent, LOCK_EX) === false) {
                fail('Could not write to active script. Check permissions.', 500);
            }
            j(['ok'=>true, 'runId'=>$runId]);
        case 'create':
            csrf();
            [$full] = sandbox($_POST['path'] ?? '', false);
            if (file_exists($full)) fail('File or folder already exists.', 409);
            if (($_POST['type'] ?? 'file') === 'dir') { if (!@mkdir($full, 0775, true)) fail('Could not create folder.', 500); }
            else { if (file_put_contents($full, '') === false) fail('Could not create file.', 500); }
            j(['ok'=>true]);
        case 'rename':
            csrf();
            [$old] = sandbox($_POST['oldPath'] ?? '', true);
            [$new] = sandbox($_POST['newPath'] ?? '', false);
            if (is_active($old)) fail('The active script cannot be renamed.', 403);
            if (file_exists($new)) fail('Destination already exists.', 409);
            if (!@rename($old, $new)) fail('Could not rename item.', 500);
            j(['ok'=>true]);
        case 'move':
            csrf();
            [$src, $srcRel] = sandbox($_POST['sourcePath'] ?? '', true);
            [$dstDir, $dstRel] = sandbox($_POST['targetDir'] ?? '', true);
            if (!is_file($src)) fail('Only files can be moved by drag-and-drop.', 400);
            if (!is_dir($dstDir)) fail('Drop target must be a folder.', 400);
            if (is_active($src)) fail('The active script cannot be moved.', 403);
            if (dirname($src) === $dstDir) fail('File is already in that folder.', 409);
            $dst = str_replace('\\','/', $dstDir . '/' . basename($src));
            if (file_exists($dst)) fail('A file with the same name already exists there.', 409);
            if (!@rename($src, $dst)) fail('Could not move file.', 500);
            j(['ok'=>true, 'newPath'=>trim($dstRel . '/' . basename($src), '/')]);
        case 'delete':
            csrf();
            [$full] = sandbox($_POST['path'] ?? '', true);
            if (is_active($full)) fail('The active script cannot be deleted.', 403);
            delete_recursive($full);
            j(['ok'=>true]);
        case 'upload':
            csrf();
            [$dir, $dirRel] = sandbox($_POST['dir'] ?? '', true);
            if (!is_dir($dir)) fail('Upload destination must be a folder.', 400);
            if (!isset($_FILES['file']) || !is_uploaded_file($_FILES['file']['tmp_name'])) fail('No uploaded file received.', 400);
            if ($_FILES['file']['size'] > MAX_UPLOAD_BYTES) fail('Uploaded file is too large.', 413);
            $name = basename($_FILES['file']['name']);
            $ext = strtolower(pathinfo($name, PATHINFO_EXTENSION));
            $allowed = array_map('strtolower', ALLOWED_UPLOAD_EXTENSIONS);
            if (!in_array($ext, $allowed, true)) fail('This file type is not allowed.', 403);
            [$dest, $rel, $finalName] = unique_upload_path($dirRel, $name);
            if (!@move_uploaded_file($_FILES['file']['tmp_name'], $dest)) fail('Could not store uploaded file.', 500);
            j(['ok'=>true, 'path'=>$rel, 'name'=>$finalName]);
        case 'logs':
            $logPath = defined('LOG_FILE') ? LOG_FILE : '';
            if ($logPath === '') fail('LOG_FILE is not defined in config.php.', 500);
            $real = realpath($logPath);
            if ($real === false || !is_file($real) || !is_readable($real)) fail('Log file is not readable: ' . $logPath, 404);
            $offset = isset($_GET['offset']) ? (int)$_GET['offset'] : -1;
            $max = defined('LOG_TAIL_BYTES') ? (int)LOG_TAIL_BYTES : 262144;
            $chunk = read_log_chunk($real, $offset, $max);
            j(['ok'=>true, 'content'=>$chunk['content'], 'offset'=>$chunk['offset'], 'size'=>$chunk['size'], 'name'=>basename($real), 'time'=>date('Y-m-d H:i:s')]);
        case 'clear_logs':
            csrf();
            $logPath = defined('LOG_FILE') ? LOG_FILE : '';
            if ($logPath === '') fail('LOG_FILE is not defined in config.php.', 500);
            $real = realpath($logPath);
            if ($real === false || !is_file($real) || !is_writable($real)) fail('Log file is not writable: ' . $logPath, 404);
            if (file_put_contents($real, '') === false) fail('Could not clear log file.', 500);
            j(['ok'=>true, 'offset'=>0, 'size'=>0, 'time'=>date('Y-m-d H:i:s')]);
        case 'download':
            $path = $_GET['path'] ?? '';
            if ($path === '__ACTIVE__') {
                $full = active_path();
                if (!is_file($full) || !is_readable($full)) { http_response_code(500); exit('Active script is not readable.'); }
            } else {
                [$full] = sandbox($path, true);
                if (!is_file($full)) { http_response_code(400); exit('Only files can be downloaded.'); }
            }
            header('Content-Type: application/octet-stream');
            header('Content-Disposition: attachment; filename="' . basename($full) . '"');
            header('Content-Length: ' . filesize($full));
            readfile($full); exit;
    }
    fail('Unknown action.', 404);
}
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= htmlspecialchars(IDE_TITLE) ?></title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.32.6/ace.js" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.32.6/mode-python.min.js" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/ace/1.32.6/theme-monokai.min.js" crossorigin="anonymous"></script>
<style>
:root{--bg:#0b1120;--panel:#111827;--panel2:#0f172a;--line:#253142;--text:#e5e7eb;--muted:#94a3b8;--blue:#3b82f6;--green:#22c55e;--red:#ef4444;--hover:#1f2937;--drop:#164e63}
*{box-sizing:border-box}html,body{height:100%;overflow:hidden}body{margin:0;background:var(--bg);color:var(--text);font-family:Arial,Helvetica,sans-serif}header{height:64px;display:flex;align-items:center;gap:12px;padding:10px 16px;background:#0f172a;border-bottom:1px solid var(--line)}.logo{width:40px;height:40px;border:1px solid #1d4ed8;border-radius:10px;background:#172554;display:flex;align-items:center;justify-content:center;font-weight:700;color:#bfdbfe;overflow:hidden}.logo img{width:100%;height:100%;object-fit:contain}.title{font-size:20px;font-weight:700;flex:1}.app{height:calc(100vh - 64px);display:grid;grid-template-columns:330px 1fr;min-height:0}.sidebar{background:#0f172a;border-right:1px solid var(--line);display:flex;flex-direction:column;min-width:0;min-height:0}.sidebar-head{display:flex;gap:8px;padding:10px;border-bottom:1px solid var(--line);flex-wrap:wrap}.sidebar-head .spacer{flex:1 1 auto;min-width:8px}.tree{padding:8px;overflow:auto;flex:1;min-height:0}.tree.root-drop{outline:2px dashed #38bdf8;outline-offset:-6px;background:#082f49}.tree ul{list-style:none;margin:0;padding-left:18px}.tree>ul{padding-left:0}.row{height:32px;display:flex;align-items:center;gap:7px;border-radius:8px;padding:4px 6px;user-select:none}.row:hover{background:var(--hover)}.row.selected{background:#12315f}.row.active-file{color:#86efac;font-weight:700}.row.last-run{outline:1px solid #22c55e;color:#bbf7d0}.row.last-run .name::after{content:"  ▶ last run";font-size:11px;color:#86efac;font-weight:700}.row.dragging{opacity:.45}.row.drop-target{background:var(--drop);outline:1px dashed #67e8f9}.name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.children.collapsed{display:none}button{display:inline-flex;align-items:center;justify-content:center;gap:7px;background:#111827;color:var(--text);border:1px solid var(--line);border-radius:8px;min-width:34px;min-height:34px;padding:8px;cursor:pointer;font-weight:700}button:hover:not(:disabled){background:var(--hover)}button:disabled{opacity:.45;cursor:not-allowed}.run{background:#15803d;border-color:#16a34a;color:white}.logs{background:#334155;border-color:#475569;color:#e2e8f0}.danger{color:#fecaca;border-color:#7f1d1d}.main{display:grid;grid-template-rows:auto auto minmax(0,1fr) 220px auto;min-width:0;min-height:0}.tabs{display:flex;align-items:flex-end;gap:4px;padding:6px 8px 0;background:#0b1120;border-bottom:1px solid var(--line);overflow-x:auto;min-height:43px}.tab{display:flex;align-items:center;gap:8px;max-width:240px;padding:8px 8px 7px;background:#111827;border:1px solid var(--line);border-bottom:0;border-radius:10px 10px 0 0;color:var(--muted);cursor:pointer;white-space:nowrap}.tab.active{background:#1f2937;color:var(--text)}.tab.dirty .tab-title::before{content:"● ";color:#fbbf24}.tab.last-run{box-shadow:inset 0 2px 0 #22c55e}.tab.last-run .tab-title::after{content:"  ▶";color:#86efac;font-weight:700}.tab-title{overflow:hidden;text-overflow:ellipsis}.tab-close{border:0;background:transparent;min-width:22px;min-height:22px;padding:0;color:var(--muted)}.tab-close:hover{background:#334155;color:#fff}.toolbar{display:flex;align-items:center;gap:8px;padding:10px;border-bottom:1px solid var(--line);background:#111827}.current{flex:1;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.current .flag{margin-left:8px;color:#fbbf24}.current .runflag{margin-left:8px;color:#86efac;font-weight:700}.editor-wrap{position:relative;min-height:0;overflow:hidden}#editor{position:absolute;inset:0}#fallback{display:none;position:absolute;inset:0;width:100%;height:100%;background:#111827;color:#e5e7eb;border:0;padding:12px;font-family:Consolas,monospace}.status{height:28px;padding:6px 10px;color:var(--muted);border-top:1px solid var(--line);font-size:13px}.icon{width:16px;height:16px;flex:0 0 16px}.twisty{width:20px;min-width:20px;height:24px;padding:0;border:0;background:transparent}.twisty:hover{background:#1e293b}.toastbox{position:fixed;right:16px;bottom:16px;display:flex;flex-direction:column;gap:8px;z-index:20}.toast{background:#111827;border:1px solid #334155;color:#e5e7eb;padding:10px 12px;border-radius:10px;box-shadow:0 12px 30px rgba(0,0,0,.35)}.toast.ok{border-color:#15803d}.toast.err{border-color:#b91c1c}.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.62);z-index:30;align-items:center;justify-content:center;padding:22px}.modal.show{display:flex}.modal-card{width:min(960px,96vw);height:min(720px,88vh);background:#0f172a;border:1px solid #334155;border-radius:14px;display:flex;flex-direction:column;box-shadow:0 24px 80px rgba(0,0,0,.55)}.modal-head{display:flex;align-items:center;gap:10px;padding:12px;border-bottom:1px solid #334155}.modal-title{font-weight:700;flex:1}.terminal-panel{display:flex;flex-direction:column;min-height:0;background:#020617;border-top:1px solid var(--line)}.terminal-head{height:38px;display:flex;align-items:center;gap:8px;padding:6px 10px;background:#0f172a;border-bottom:1px solid var(--line)}.terminal-title{font-weight:700;color:#dbeafe}.terminal-path{font-size:12px;color:var(--muted);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.terminal-btn{min-height:28px;min-width:70px;padding:5px 8px;font-size:12px}.terminal-body{margin:0;flex:1;min-height:0;overflow:auto;padding:10px 12px;white-space:pre-wrap;font-family:Consolas,Menlo,monospace;font-size:13px;line-height:1.35;background:#020617;color:#d1d5db}.small{font-size:12px;color:var(--muted)}input[type=file]{display:none}
.row.media-root{color:#bfdbfe;font-weight:700}.row.media-file{color:#dbeafe}.media-glyph{width:16px;text-align:center;flex:0 0 16px}.modal{background:rgba(0,0,0,.72)}.modal-card{width:min(1040px,96vw);height:min(780px,90vh)}.modal-title{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.media-view{flex:1;min-height:0;overflow:auto;padding:18px;display:flex;align-items:center;justify-content:center}.media-view img{display:block;max-width:100%;max-height:100%;object-fit:contain;border-radius:8px;background:#020617}.media-view audio{width:min(720px,90%)}.media-json{width:100%;align-self:stretch}.media-summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:14px}.media-stat{background:#111827;border:1px solid #334155;border-radius:9px;padding:10px}.media-stat strong{display:block;font-size:20px;color:#86efac}.media-table{width:100%;border-collapse:collapse;background:#111827}.media-table th,.media-table td{padding:9px;border:1px solid #334155;text-align:left}.media-table th{color:#bfdbfe}.media-raw{white-space:pre-wrap;font-family:Consolas,monospace;background:#020617;border:1px solid #334155;border-radius:8px;padding:12px;color:#d1d5db}.media-download{display:inline-flex;align-items:center;text-decoration:none;background:#1d4ed8;color:white;border:1px solid #3b82f6;border-radius:8px;padding:8px 12px;font-weight:700}
.tree{font-size:14px}.file-time,.modal-file-time{margin-left:10px;color:var(--muted);font-size:12px;font-weight:400}.modal-heading{min-width:0;flex:1}.modal-heading .modal-title{display:block}.modal-file-time{margin:3px 0 0}
</style>
</head>
<body>
<header>
  <div class="logo"><?php if (defined('IDE_LOGO_URL') && IDE_LOGO_URL): ?><img src="<?= htmlspecialchars(IDE_LOGO_URL) ?>" alt="Logo"><?php else: ?>IDE<?php endif; ?></div>
  <div class="title"><?= htmlspecialchars(IDE_TITLE) ?></div>
</header>
<div class="app">
  <aside class="sidebar">
    <div class="sidebar-head">
      <button id="newFile" title="New file" aria-label="New file"></button>
      <button id="newFolder" title="New folder" aria-label="New folder"></button>
      <button id="uploadBtn" title="Upload .py" aria-label="Upload .py"></button>
      <button id="refreshBtn" title="Refresh" aria-label="Refresh"></button>
      <span class="spacer"></span>
      <button id="menuRenameBtn" title="Rename selected file/folder" aria-label="Rename selected file/folder"></button>
      <button id="menuDeleteBtn" class="danger" title="Delete selected file/folder" aria-label="Delete selected file/folder"></button>
      <input type="file" id="uploadInput" accept=".py">
    </div>
    <div id="tree" class="tree"></div>
  </aside>
  <main class="main">
    <div id="tabs" class="tabs"></div>
    <div class="toolbar">
      <div class="current" id="current">No file selected</div>
      <button id="saveBtn" title="Save" aria-label="Save"></button>
      <button id="downloadBtn" title="Download" aria-label="Download"></button>
      <button id="runBtn" class="run" title="Run this file" aria-label="Run this file"></button>
      <button id="logsBtn" class="logs" title="Terminal" aria-label="Terminal"></button>
    </div>
    <div class="editor-wrap"><div id="editor"></div><textarea id="fallback"></textarea></div>
    <section class="terminal-panel" id="terminalPanel" aria-label="Live terminal">
      <div class="terminal-head">
        <div class="terminal-title">Live Terminal</div>
        <div class="terminal-path" id="terminalPath"><?= htmlspecialchars(defined('LOG_FILE') ? LOG_FILE : '') ?></div>
        <button id="terminalPauseBtn" class="terminal-btn" title="Pause live terminal" aria-label="Pause live terminal">Pause</button>
        <button id="terminalClearBtn" class="terminal-btn danger" title="Clear terminal log" aria-label="Clear terminal log">Clear</button>
      </div>
      <pre class="terminal-body" id="terminalBody">Waiting for output...</pre>
    </section>
    <div class="status" id="status">Ready.</div>
  </main>
</div>
<div class="modal" id="mediaModal" role="dialog" aria-modal="true" aria-labelledby="mediaTitle">
  <div class="modal-card">
    <div class="modal-head">
      <div class="modal-heading"><div class="modal-title" id="mediaTitle">Media preview</div><div class="modal-file-time" id="mediaModified"></div></div>
      <button id="mediaRename" title="Rename this media file">Rename</button>
      <button id="mediaDelete" class="danger" title="Delete this media file">Delete</button>
      <a class="media-download" id="mediaDownload" href="#">Download</a>
      <button id="mediaClose" title="Close preview" aria-label="Close preview">Close</button>
    </div>
    <div class="media-view" id="mediaView"></div>
  </div>
</div>
<div class="toastbox" id="toastbox"></div>
<script>
const CSRF = '';
const ACTIVE_NAME = <?= json_encode(basename(ACTIVE_SCRIPT_FILE)) ?>;
const SVG={file:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>',folder:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>',chev:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>',plus:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>',folderPlus:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M12 10v6M9 13h6"/></svg>',upload:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5M12 3v12"/></svg>',refresh:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 0 1-15.5 6.3L3 16"/><path d="M3 12A9 9 0 0 1 18.5 5.7L21 8"/></svg>',save:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/></svg>',download:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5M12 15V3"/></svg>',edit:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>',trash:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>',play:'<svg class="icon" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>',logs:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8"/></svg>',x:'<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>'};
function setIcon(id, icon, labelText=''){const b=document.getElementById(id); if(b) b.innerHTML=SVG[icon]+labelText;}
setIcon('newFile','plus');setIcon('newFolder','folderPlus');setIcon('uploadBtn','upload');setIcon('refreshBtn','refresh');setIcon('menuRenameBtn','edit');setIcon('menuDeleteBtn','trash');setIcon('saveBtn','save');setIcon('downloadBtn','download');setIcon('runBtn','play','<span>Run this File</span>');setIcon('logsBtn','logs','<span>Terminal</span>');
let editor, usingAce=false;
let tabs=[], activeTab=-1;
let lastRanPath='', suppressEditorChange=false;
let collapsed=new Set(JSON.parse(localStorage.getItem('ideCollapsedFolders')||'[]'));
let selectedPath='', selectedType='', selectedDir='';
let selectedScope='code', selectedMediaRoot='', selectedMediaDir='', selectedMediaPath='';
let currentMediaNode=null;
try{editor=ace.edit('editor');editor.setTheme('ace/theme/monokai');editor.session.setMode('ace/mode/python');editor.setOptions({fontSize:'14px',showPrintMargin:false});usingAce=true;}catch(e){document.getElementById('editor').style.display='none';document.getElementById('fallback').style.display='block';editor={getValue:()=>document.getElementById('fallback').value,setValue:v=>{document.getElementById('fallback').value=v},setReadOnly:r=>{document.getElementById('fallback').readOnly=r}};}
function content(){return usingAce?editor.getValue():document.getElementById('fallback').value}
function setContent(v){suppressEditorChange=true;if(usingAce)editor.setValue(v||'',-1);else editor.setValue(v||'');suppressEditorChange=false}
function toast(msg, ok=true){const t=document.createElement('div');t.className='toast '+(ok?'ok':'err');t.textContent=msg;document.getElementById('toastbox').appendChild(t);setTimeout(()=>t.remove(),3500)}
function status(s){document.getElementById('status').textContent=s}
async function api(action, data=null, method='POST'){let opt={method,headers:{}};let url='?action='+encodeURIComponent(action);if(method==='GET'){if(data) url+='&'+new URLSearchParams(data).toString();}else{let fd=new FormData();fd.append('csrf',CSRF);if(data) for(const [k,v] of Object.entries(data)) fd.append(k,v);opt.body=fd;}let r=await fetch(url,opt);let j=await r.json().catch(()=>({ok:false,error:'Invalid server response'}));if(!r.ok||!j.ok)throw new Error(j.error||'Request failed');return j;}
async function mediaApi(action,data=null,method='GET'){let opt={method};let url='media.php?action='+encodeURIComponent(action);if(method==='GET'){if(data)url+='&'+new URLSearchParams(data).toString();}else{const fd=data instanceof FormData?data:new FormData();opt.body=fd;}const r=await fetch(url,opt);const out=await r.json().catch(()=>({ok:false,error:'Invalid media response'}));if(!r.ok||!out.ok)throw new Error(out.error||'Media request failed');return out;}
function mediaUrl(action,root,path){return 'media.php?'+new URLSearchParams({action,root,path}).toString();}
function active(){return activeTab>=0?tabs[activeTab]:null}
function updateDirty(t){if(!t||t.readOnly)return;t.dirty=(t.content||'')!==(t.savedContent||'');}
function captureActive(){const t=active(); if(t){t.content=content();updateDirty(t);}}
function anyDirty(){captureActive();return tabs.some(t=>t.dirty);}
function tabIsUnderPath(t,path,type){return t.path===path||(type==='dir'&&t.path.startsWith(path+'/'));}
function confirmCloseTab(t){return !t.dirty||confirm('Close \"'+t.name+'\" without saving changes?');}
function updateButtons(){const t=active();const media=selectedScope==='media';const mediaFile=media&&selectedType==='file'&&!!selectedMediaPath;document.getElementById('saveBtn').disabled=!t||t.readOnly||!t.dirty;document.getElementById('downloadBtn').disabled=!t;document.getElementById('runBtn').disabled=!t;document.getElementById('newFile').disabled=media;document.getElementById('newFolder').disabled=media;document.getElementById('menuRenameBtn').disabled=media?!mediaFile:(!selectedPath||selectedPath==='__ACTIVE__');document.getElementById('menuDeleteBtn').disabled=media?!mediaFile:(!selectedPath||selectedPath==='__ACTIVE__');document.getElementById('uploadBtn').title=media?'Upload media to selected folder':'Upload .py';}
function updateCurrentLabel(){const t=active();const el=document.getElementById('current');if(!t){el.textContent='No file open';return;}el.textContent=(t.readOnly?'Read-only: ':'Editing: ')+t.path;if(t.dirty){const f=document.createElement('span');f.className='flag';f.textContent='● unsaved';el.appendChild(f);}if(lastRanPath&&t.path===lastRanPath){const r=document.createElement('span');r.className='runflag';r.textContent='▶ last run';el.appendChild(r);}}
function renderTabs(){const box=document.getElementById('tabs');box.innerHTML='';tabs.forEach((t,i)=>{const cls='tab'+(i===activeTab?' active':'')+(t.dirty?' dirty':'')+(lastRanPath&&t.path===lastRanPath?' last-run':'');const el=document.createElement('div');el.className=cls;el.title=t.path+(t.dirty?' — unsaved':'')+(lastRanPath&&t.path===lastRanPath?' — last run':'');el.innerHTML='<span class="tab-title"></span><button class="tab-close" title="Close" aria-label="Close">'+SVG.x+'</button>';el.querySelector('.tab-title').textContent=t.name;el.onclick=()=>focusTab(i);el.querySelector('.tab-close').onclick=e=>{e.stopPropagation();closeTab(i)};box.appendChild(el)});updateButtons();updateCurrentLabel();}
function focusTab(i){if(i<0||i>=tabs.length)return;captureActive();activeTab=i;selectedScope='code';selectedMediaRoot='';selectedMediaDir='';selectedMediaPath='';const t=tabs[i];setContent(t.content||'');editor.setReadOnly(!!t.readOnly);renderTabs();highlightPath(t.path);status('Opened '+t.name)}
function closeTab(i){captureActive();const closing=tabs[i];if(!closing||!confirmCloseTab(closing))return;tabs.splice(i,1);if(!tabs.length){activeTab=-1;setContent('');editor.setReadOnly(true);renderTabs();status('No file open.');return;}if(activeTab>=tabs.length)activeTab=tabs.length-1;else if(i<activeTab)activeTab--;focusTab(activeTab);}
function closeTabsUnderPath(path,type){captureActive();const closing=tabs.filter(t=>tabIsUnderPath(t,path,type));if(closing.some(t=>t.dirty)&&!confirm('There are unsaved open files inside this selection. Close them without saving?'))return false;tabs=tabs.filter(t=>!tabIsUnderPath(t,path,type));if(lastRanPath&&(lastRanPath===path||(type==='dir'&&lastRanPath.startsWith(path+'/'))))lastRanPath='';if(activeTab>=tabs.length)activeTab=tabs.length-1;if(activeTab>=0)focusTab(activeTab);else{setContent('');editor.setReadOnly(true);renderTabs();}return true;}
function pathAfterRename(p,oldp,newp,type){if(p===oldp)return newp;if(type==='dir'&&p.startsWith(oldp+'/'))return newp+p.slice(oldp.length);return p;}
function updateTabsAfterRename(oldp,newp,type){tabs.forEach(t=>{const np=pathAfterRename(t.path,oldp,newp,type);if(np!==t.path){t.path=np;t.name=np.split('/').pop()||np;}});if(lastRanPath)lastRanPath=pathAfterRename(lastRanPath,oldp,newp,type);renderTabs();}
function saveCollapsed(){localStorage.setItem('ideCollapsedFolders',JSON.stringify([...collapsed]));}
function markSelected(row){document.querySelectorAll('.row').forEach(r=>r.classList.remove('selected'));if(row)row.classList.add('selected');updateButtons();}
function highlightPath(path){const row=document.querySelector('.row[data-path="'+CSS.escape(path)+'"]');if(row)markSelected(row);}
function selectItem(path,type,row,options={}){selectedScope=options.scope||'code';selectedPath=path;selectedType=type;if(selectedScope==='media'){selectedMediaRoot=options.root||'';selectedMediaDir=options.dir||'';selectedMediaPath=options.path||'';}else{selectedMediaRoot='';selectedMediaDir='';selectedMediaPath='';selectedDir=type==='dir'?path:(path.includes('/')?path.split('/').slice(0,-1).join('/'):'');}markSelected(row);}
function nodeKey(node){return node.scope==='media'?'__MEDIA__:'+node.root+':'+(node.path||''):node.path;}
function rowBase(node){const key=nodeKey(node);const media=node.scope==='media';const r=document.createElement('div');r.className='row '+node.type+(media?' media-'+node.type:'')+(lastRanPath&&node.path===lastRanPath?' last-run':'');if(media&&node.path==='')r.classList.add('media-root');if(node.active)r.classList.add('active-file');r.dataset.path=key;r.title=media?(node.name+' — media'):(node.path||node.name);return r;}
function renderNode(node){const li=document.createElement('li');const media=node.scope==='media';const section=node.scope==='section';const key=nodeKey(node);if(node.type==='dir'){const row=rowBase(node);row.classList.add('folder-row');const twist=document.createElement('button');twist.type='button';twist.className='twisty';twist.innerHTML=SVG.chev;row.append(twist);row.insertAdjacentHTML('beforeend',SVG.folder);const name=document.createElement('span');name.className='name';name.textContent=node.name;row.append(name);const children=document.createElement('ul');children.className='children';if(collapsed.has(key))children.classList.add('collapsed');twist.style.transform=collapsed.has(key)?'rotate(0deg)':'rotate(90deg)';function toggle(){if(collapsed.has(key))collapsed.delete(key);else collapsed.add(key);children.classList.toggle('collapsed');twist.style.transform=collapsed.has(key)?'rotate(0deg)':'rotate(90deg)';saveCollapsed();}twist.onclick=e=>{e.stopPropagation();toggle()};row.ondblclick=e=>{e.stopPropagation();toggle()};row.onclick=()=>selectItem(media?key:(section?'':node.path),'dir',row,{scope:media?'media':'code',root:node.root||'',dir:media?(node.path||''):'',path:''});if(!media){row.ondragover=e=>{e.preventDefault();e.stopPropagation();row.classList.add('drop-target');e.dataTransfer.dropEffect='move'};row.ondragleave=()=>row.classList.remove('drop-target');row.ondrop=async e=>{e.preventDefault();e.stopPropagation();row.classList.remove('drop-target');const src=e.dataTransfer.getData('text/plain');if(src)await moveFile(src,section?'':node.path)}};(node.children||[]).forEach(ch=>children.appendChild(renderNode(ch)));li.append(row,children);}else{const row=rowBase(node);if(media){const glyph=document.createElement('span');glyph.className='media-glyph';glyph.textContent=node.kind==='image'?'▧':node.kind==='audio'?'♪':node.kind==='json'?'{}':'↓';const name=document.createElement('span');name.className='name';name.textContent=node.name;row.append(glyph,name);row.onclick=()=>{selectItem(key,'file',row,{scope:'media',root:node.root,dir:node.path.includes('/')?node.path.split('/').slice(0,-1).join('/'):'',path:node.path});openMedia(node)}}else{row.draggable=!node.active;row.innerHTML=SVG.file+'<span class="name"></span>';row.querySelector('.name').textContent=node.name;row.onclick=()=>{selectItem(node.path,'file',row);openFile(node.path,node.name)};if(!node.active){row.ondragstart=e=>{e.dataTransfer.setData('text/plain',node.path);e.dataTransfer.effectAllowed='move';row.classList.add('dragging')};row.ondragend=()=>row.classList.remove('dragging')}}li.appendChild(row)}return li;}
async function loadTree(){try{const out=await api('tree',null,'GET');let mediaRoots=[];try{const media=await mediaApi('tree');mediaRoots=media.roots||[]}catch(mediaError){toast(mediaError.message,false)}const tree=document.getElementById('tree');tree.innerHTML='';const root=document.createElement('ul');const codeRoot={type:'dir',name:'Python Programs',path:'__PYTHON_ROOT__',scope:'section',children:[{type:'file',name:ACTIVE_NAME,path:'__ACTIVE__',active:true},...(out.tree||[])]};root.appendChild(renderNode(codeRoot));mediaRoots.forEach(node=>root.appendChild(renderNode(node)));tree.appendChild(root);tree.ondragover=e=>{if(e.target.closest('.folder-row'))return;e.preventDefault();tree.classList.add('root-drop');e.dataTransfer.dropEffect='move'};tree.ondragleave=e=>{if(!tree.contains(e.relatedTarget))tree.classList.remove('root-drop')};tree.ondrop=async e=>{if(e.target.closest('.folder-row'))return;e.preventDefault();tree.classList.remove('root-drop');const src=e.dataTransfer.getData('text/plain');if(src)await moveFile(src,'')};if(selectedPath)highlightPath(selectedPath)}catch(e){toast(e.message,false);status(e.message)}}
function closeMedia(){const modal=document.getElementById('mediaModal');modal.classList.remove('show');const audio=modal.querySelector('audio');if(audio)audio.pause();document.getElementById('mediaView').innerHTML='';currentMediaNode=null;}
function mediaStat(container,label,value){const item=document.createElement('div');item.className='media-stat';const strong=document.createElement('strong');strong.textContent=value;const text=document.createElement('span');text.textContent=label;item.append(strong,text);container.appendChild(item);}
function renderJsonMedia(data){const wrap=document.createElement('div');wrap.className='media-json';if(data&&Array.isArray(data.detections)){const summary=document.createElement('div');summary.className='media-summary';mediaStat(summary,'Objects',String(data.num_detections??data.detections.length));mediaStat(summary,'Inference',data.elapsed_sec===undefined?'—':Number(data.elapsed_sec).toFixed(3)+' s');mediaStat(summary,'Image',String(data.image||'—').split('/').pop());wrap.appendChild(summary);const table=document.createElement('table');table.className='media-table';const head=document.createElement('thead');const header=document.createElement('tr');['Object','Confidence','Bounding box'].forEach(label=>{const th=document.createElement('th');th.textContent=label;header.appendChild(th)});head.appendChild(header);table.appendChild(head);const body=document.createElement('tbody');data.detections.forEach(item=>{const row=document.createElement('tr');const object=document.createElement('td');object.textContent=item.class_name??item.class_id??'Unknown';const confidence=document.createElement('td');confidence.textContent=item.confidence===undefined?'—':Math.round(Number(item.confidence)*100)+'%';const box=document.createElement('td');box.textContent=Array.isArray(item.bbox_xyxy)?item.bbox_xyxy.map(value=>Math.round(Number(value))).join(', '):'—';row.append(object,confidence,box);body.appendChild(row)});table.appendChild(body);wrap.appendChild(table)}else{const pre=document.createElement('pre');pre.className='media-raw';pre.textContent=JSON.stringify(data,null,2);wrap.appendChild(pre)}return wrap;}
async function openMedia(node){currentMediaNode={scope:'media',root:node.root,path:node.path,name:node.name,kind:node.kind};const modal=document.getElementById('mediaModal');const view=document.getElementById('mediaView');document.getElementById('mediaTitle').textContent=node.name+' — '+node.root+'/'+node.path;document.getElementById('mediaDownload').href=mediaUrl('download',node.root,node.path);view.innerHTML='';modal.classList.add('show');const url=mediaUrl('file',node.root,node.path);try{if(node.kind==='image'){const image=document.createElement('img');image.alt=node.name;image.src=url;view.appendChild(image)}else if(node.kind==='audio'){const audio=document.createElement('audio');audio.controls=true;audio.preload='metadata';audio.src=url;view.appendChild(audio)}else if(node.kind==='json'){const response=await fetch(url);if(!response.ok)throw new Error('Could not open JSON result');view.appendChild(renderJsonMedia(await response.json()))}else{const message=document.createElement('p');message.textContent='Preview is unavailable. Use Download to open this file.';view.appendChild(message)}status('Previewing '+node.name)}catch(error){view.textContent=error.message;toast(error.message,false)}}
async function renamePreviewMedia(){const node=currentMediaNode;if(!node)return;const newName=prompt('New media filename (keep the same extension):',node.name);if(!newName||newName===node.name)return;try{const form=new FormData();form.append('root',node.root);form.append('path',node.path);form.append('newName',newName);const out=await mediaApi('rename',form,'POST');closeMedia();selectedScope='media';selectedType='file';selectedMediaRoot=out.root;selectedMediaPath=out.path;selectedMediaDir=out.path.includes('/')?out.path.split('/').slice(0,-1).join('/'):'';selectedPath='__MEDIA__:'+out.root+':'+out.path;toast('Media file renamed.');await loadTree();highlightPath(selectedPath);await openMedia({scope:'media',root:out.root,path:out.path,name:out.name,kind:out.kind})}catch(error){toast(error.message,false)}}
async function deletePreviewMedia(){const node=currentMediaNode;if(!node)return;if(!confirm('Delete media file '+node.name+'?'))return;try{const form=new FormData();form.append('root',node.root);form.append('path',node.path);await mediaApi('delete',form,'POST');closeMedia();toast('Media file deleted.');selectedPath='';selectedType='';selectedMediaPath='';await loadTree()}catch(error){toast(error.message,false)}}
document.getElementById('mediaRename').onclick=renamePreviewMedia;document.getElementById('mediaDelete').onclick=deletePreviewMedia;document.getElementById('mediaClose').onclick=closeMedia;document.getElementById('mediaModal').onclick=e=>{if(e.target.id==='mediaModal')closeMedia()};document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMedia()});
async function openFile(path,name){try{captureActive();let idx=tabs.findIndex(t=>t.path===path);if(idx>=0){focusTab(idx);return;}const out=await api('read',{path},'GET');tabs.push({path:path,name:out.name||name,content:out.content||'',savedContent:out.content||'',dirty:false,readOnly:!!out.readOnly});focusTab(tabs.length-1);}catch(e){toast(e.message,false);status(e.message)}}
async function moveFile(src,target){try{const out=await api('move',{sourcePath:src,targetDir:target});if(out.newPath)updateTabsAfterRename(src,out.newPath,'file');toast('File moved.');status('File moved.');await loadTree();}catch(e){toast(e.message,false);status(e.message)}}
document.getElementById('saveBtn').onclick=async()=>{const t=active();if(!t||t.readOnly)return;captureActive();try{await api('save',{path:t.path,content:t.content});t.savedContent=t.content;t.dirty=false;if(lastRanPath===t.path)lastRanPath='';renderTabs();await loadTree();toast('File saved.');status('Saved '+t.name)}catch(e){toast(e.message,false)}};
document.getElementById('runBtn').onclick=async()=>{const t=active();if(!t)return;captureActive();try{if(!t.readOnly){await api('save',{path:t.path,content:t.content});t.savedContent=t.content;t.dirty=false;}await api('run',{content:t.content});lastRanPath=t.path;const activeIdx=tabs.findIndex(tab=>tab.path==='__ACTIVE__');if(activeIdx>=0){tabs[activeIdx].content=t.content;tabs[activeIdx].savedContent=t.content;tabs[activeIdx].dirty=false;if(activeTab===activeIdx)setContent(t.content);}renderTabs();await loadTree();toast('Saved and updated active script from '+t.name+'.');status('Saved and updated active script from '+t.name+' by explicit Run command.')}catch(e){toast(e.message,false)}};
document.getElementById('downloadBtn').onclick=()=>{const t=active();if(t)location.href='?action=download&path='+encodeURIComponent(t.path)};
document.getElementById('menuRenameBtn').onclick=async()=>{if(selectedScope==='media'){if(selectedType!=='file'||!selectedMediaPath)return;const oldName=selectedMediaPath.split('/').pop();const newName=prompt('New media filename (keep the same extension):',oldName);if(!newName||newName===oldName)return;try{const form=new FormData();form.append('root',selectedMediaRoot);form.append('path',selectedMediaPath);form.append('newName',newName);const out=await mediaApi('rename',form,'POST');closeMedia();selectedMediaPath=out.path;selectedPath='__MEDIA__:'+out.root+':'+out.path;selectedMediaDir=out.path.includes('/')?out.path.split('/').slice(0,-1).join('/'):'';toast('Media file renamed.');await loadTree();highlightPath(selectedPath);await openMedia({scope:'media',root:out.root,path:out.path,name:out.name,kind:out.kind})}catch(error){toast(error.message,false)}return}if(!selectedPath||selectedPath==='__ACTIVE__')return;const nn=prompt('New name/path inside working directory:',selectedPath);if(!nn||nn===selectedPath)return;try{const old=selectedPath,type=selectedType;await api('rename',{oldPath:old,newPath:nn});selectedPath=nn;selectedDir=type==='dir'?nn:(nn.includes('/')?nn.split('/').slice(0,-1).join('/'):'');updateTabsAfterRename(old,nn,type);toast('Renamed.');await loadTree();highlightPath(nn)}catch(e){toast(e.message,false)}};
document.getElementById('menuDeleteBtn').onclick=async()=>{if(selectedScope==='media'){if(selectedType!=='file'||!selectedMediaPath)return;const name=selectedMediaPath.split('/').pop();if(!confirm('Delete media file '+name+'?'))return;try{const form=new FormData();form.append('root',selectedMediaRoot);form.append('path',selectedMediaPath);await mediaApi('delete',form,'POST');closeMedia();toast('Media file deleted.');selectedPath='';selectedType='';selectedMediaPath='';await loadTree()}catch(error){toast(error.message,false)}return}if(!selectedPath||selectedPath==='__ACTIVE__')return;if(!confirm('Delete '+selectedPath+'?'))return;try{const p=selectedPath,type=selectedType;if(!closeTabsUnderPath(p,type))return;await api('delete',{path:p});toast(type==='dir'?'Folder deleted.':'File deleted.');selectedPath='';selectedType='';selectedDir='';await loadTree()}catch(e){toast(e.message,false)}};
document.getElementById('newFile').onclick=async()=>{const p=prompt('New file path:',selectedDir?selectedDir+'/new.py':'new.py');if(!p)return;try{await api('create',{path:p,type:'file'});toast('File created.');await loadTree();await openFile(p,p.split('/').pop()||p);}catch(e){toast(e.message,false)}};
document.getElementById('newFolder').onclick=async()=>{const p=prompt('New folder path:',selectedDir?selectedDir+'/new_folder':'new_folder');if(!p)return;try{await api('create',{path:p,type:'dir'});toast('Folder created.');await loadTree()}catch(e){toast(e.message,false)}};
document.getElementById('refreshBtn').onclick=loadTree;
function mediaKindFromName(name){const ext=(name.split('.').pop()||'').toLowerCase();if(['jpg','jpeg','png','webp'].includes(ext))return'image';if(['wav','mp3','ogg','flac'].includes(ext))return'audio';if(ext==='json')return'json';return'download';}
document.getElementById('uploadBtn').onclick=()=>{const input=document.getElementById('uploadInput');input.accept=selectedScope==='media'?(selectedMediaRoot==='images'?'.jpg,.jpeg,.png,.webp,.json':'.wav,.mp3,.ogg,.flac,.json'):'.py';input.click()};
document.getElementById('uploadInput').onchange=async e=>{const file=e.target.files[0];if(!file)return;const form=new FormData();form.append('file',file);try{if(selectedScope==='media'){if(!selectedMediaRoot)throw new Error('Select Images, Audio, or one of their folders first.');form.append('root',selectedMediaRoot);form.append('dir',selectedMediaDir||'');const out=await mediaApi('upload',form,'POST');toast('Uploaded as '+out.name+'.');await loadTree();await openMedia({scope:'media',root:out.root,path:out.path,name:out.name,kind:mediaKindFromName(out.name)})}else{form.append('csrf',CSRF);form.append('dir',selectedDir||'');const response=await fetch('?action=upload',{method:'POST',body:form});const out=await response.json();if(!response.ok||!out.ok)throw new Error(out.error||'Upload failed');toast('Uploaded as '+(out.name||file.name)+'.');await loadTree();if(out.path)await openFile(out.path,out.name||file.name)}}catch(error){toast(error.message,false)}finally{e.target.value=''}};
let terminalOffset=-1, terminalTimer=null, terminalPaused=false;
const TERMINAL_POLL_MS = <?= (int)(defined('LOG_POLL_MS') ? LOG_POLL_MS : 1000) ?>;
function terminalAtBottom(el){return el.scrollTop + el.clientHeight >= el.scrollHeight - 24;}
async function pollTerminal(){if(terminalPaused)return;const body=document.getElementById('terminalBody');const shouldStick=terminalAtBottom(body);try{const out=await api('logs',{offset:terminalOffset},'GET');if(terminalOffset<0){body.textContent=out.content||'';}else if(out.content){body.textContent+=out.content;}terminalOffset=Number.isFinite(Number(out.offset))?Number(out.offset):terminalOffset;if(!body.textContent)body.textContent='Waiting for output...';if(shouldStick)body.scrollTop=body.scrollHeight;}catch(e){body.textContent=e.message;toast(e.message,false);}}
function startTerminal(){clearInterval(terminalTimer);pollTerminal();terminalTimer=setInterval(pollTerminal,TERMINAL_POLL_MS);}
document.getElementById('logsBtn').onclick=()=>{terminalPaused=false;document.getElementById('terminalPauseBtn').textContent='Pause';pollTerminal();document.getElementById('terminalBody').focus();};
document.getElementById('terminalPauseBtn').onclick=()=>{terminalPaused=!terminalPaused;document.getElementById('terminalPauseBtn').textContent=terminalPaused?'Resume':'Pause';if(!terminalPaused)pollTerminal();};
document.getElementById('terminalClearBtn').onclick=async()=>{if(!confirm('Clear terminal log?'))return;try{await api('clear_logs');terminalOffset=0;document.getElementById('terminalBody').textContent='';toast('Terminal log cleared.');}catch(e){toast(e.message,false)}};
if(usingAce){editor.session.on('change',()=>{if(suppressEditorChange)return;const t=active();if(!t||t.readOnly)return;t.content=content();updateDirty(t);renderTabs();});}else{document.getElementById('fallback').addEventListener('input',()=>{if(suppressEditorChange)return;const t=active();if(!t||t.readOnly)return;t.content=content();updateDirty(t);renderTabs();});}
function formatModified(value){if(!value)return'Modified time unavailable';const d=new Date(Number(value)*1000);const pad=n=>String(n).padStart(2,'0');return'Modified: '+d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())+' '+pad(d.getHours())+':'+pad(d.getMinutes())+':'+pad(d.getSeconds())}
const updateCurrentLabelBase=updateCurrentLabel;
updateCurrentLabel=function(){updateCurrentLabelBase();const t=active();const el=document.getElementById('current');if(!t||!el)return;const tm=document.createElement('span');tm.className='file-time';tm.textContent=formatModified(t.modified);el.appendChild(tm);};
const openFileBase=openFile;
openFile=async function(path,name){await openFileBase(path,name);const t=active();if(!t||t.path!==path)return;try{const out=await api('read',{path},'GET');t.modified=out.modified;updateCurrentLabel();}catch(_error){}};
const openMediaBase=openMedia;
openMedia=async function(node){await openMediaBase(node);let modified=node.modified;try{const info=await mediaApi('info',{root:node.root,path:node.path});modified=info.modified;}catch(_error){}document.getElementById('mediaModified').textContent=formatModified(modified);};
const saveHandlerBase=document.getElementById('saveBtn').onclick;
document.getElementById('saveBtn').onclick=async function(){await saveHandlerBase();const t=active();if(!t||t.dirty)return;try{const out=await api('read',{path:t.path},'GET');t.modified=out.modified;updateCurrentLabel();}catch(_error){}};
const runHandlerBase=document.getElementById('runBtn').onclick;
document.getElementById('runBtn').onclick=async function(){await runHandlerBase();const t=active();if(!t||t.readOnly||t.dirty)return;try{const out=await api('read',{path:t.path},'GET');t.modified=out.modified;updateCurrentLabel();}catch(_error){}};
window.addEventListener('beforeunload',e=>{if(anyDirty()){e.preventDefault();e.returnValue='';}});
editor.setReadOnly(true);updateButtons();renderTabs();loadTree();startTerminal();
</script>
</body>
</html>
