<?php
$guidesDir = realpath(__DIR__ . '/guides');
require_once __DIR__ . '/../docs/vendor/parsedown/Parsedown.php';

function e(string $value): string {
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function guideFiles(string $directory): array {
    $files = glob($directory . '/*.md') ?: [];
    sort($files, SORT_NATURAL | SORT_FLAG_CASE);
    return $files;
}

function guideTitle(string $path): string {
    $markdown = file_get_contents($path) ?: '';
    return preg_match('/^\s*#\s+(.+)$/m', $markdown, $match)
        ? trim(strip_tags($match[1]))
        : str_replace(['-', '_'], ' ', pathinfo($path, PATHINFO_FILENAME));
}

$files = $guidesDir ? guideFiles($guidesDir) : [];
$requested = basename((string)($_GET['guide'] ?? ''));
$selected = null;
foreach ($files as $file) {
    if ($requested === basename($file, '.md')) {
        $selected = $file;
        break;
    }
}
if (!$selected && $files) $selected = $files[0];

$parser = new Parsedown();
if (method_exists($parser, 'setSafeMode')) $parser->setSafeMode(true);
$markdown = $selected ? (file_get_contents($selected) ?: '') : '# No teacher guides installed';
$title = $selected ? guideTitle($selected) : 'Teacher Guides';
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= e($title) ?> | CodyNick Teachers</title>
    <style>
        :root { --bg:#f4f6f8; --panel:#fff; --text:#172033; --muted:#667085; --line:#d8dee8; --accent:#176b57; }
        * { box-sizing:border-box; }
        body { margin:0; color:var(--text); background:var(--bg); font:16px/1.6 system-ui,sans-serif; }
        header { height:64px; display:flex; align-items:center; gap:18px; padding:0 24px; background:#172033; color:#fff; }
        header strong { font-size:20px; } header a { color:#d9f4ec; margin-left:auto; }
        .layout { min-height:calc(100vh - 64px); display:grid; grid-template-columns:280px minmax(0,1fr); }
        nav { padding:22px; background:var(--panel); border-right:1px solid var(--line); }
        nav h2 { margin:0 0 14px; font-size:15px; text-transform:uppercase; color:var(--muted); }
        nav a { display:block; padding:10px 12px; margin:4px 0; border-radius:6px; color:var(--text); text-decoration:none; }
        nav a.active, nav a:hover { color:#fff; background:var(--accent); }
        main { min-width:0; padding:32px clamp(20px,5vw,72px); }
        article { max-width:920px; margin:auto; padding:34px 42px; background:var(--panel); border:1px solid var(--line); border-radius:8px; }
        h1,h2,h3 { line-height:1.25; } h1 { margin-top:0; }
        pre { overflow:auto; padding:16px; background:#111827; color:#f8fafc; border-radius:6px; }
        code { font-family:ui-monospace,monospace; } :not(pre)>code { padding:2px 5px; background:#edf1f5; border-radius:4px; }
        blockquote { margin-left:0; padding-left:16px; border-left:4px solid var(--accent); color:#405065; }
        @media(max-width:760px){ .layout{grid-template-columns:1fr} nav{border-right:0;border-bottom:1px solid var(--line)} article{padding:24px 20px} }
    </style>
</head>
<body>
<header><strong>CodyNick Teacher Guides</strong><span>Protected presenter material</span><a href="/">Main panel</a></header>
<div class="layout">
    <nav><h2>Guides</h2><?php foreach ($files as $file): $slug = basename($file, '.md'); ?>
        <a class="<?= $selected === $file ? 'active' : '' ?>" href="?guide=<?= rawurlencode($slug) ?>"><?= e(guideTitle($file)) ?></a>
    <?php endforeach; ?></nav>
    <main><article><?= $parser->text($markdown) ?></article></main>
</div>
</body>
</html>
