<?php
$testsDir = realpath('/home/client/CodyNick Gadget Tests');
require_once __DIR__ . '/../docs/vendor/parsedown/Parsedown.php';

function e(string $value): string { return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function testFiles(string $directory): array {
    $files = glob($directory . '/*.md') ?: [];
    sort($files, SORT_NATURAL | SORT_FLAG_CASE);
    return $files;
}
function testTitle(string $path): string {
    $markdown = file_get_contents($path) ?: '';
    return preg_match('/^\s*#\s+(.+)$/m', $markdown, $match)
        ? trim(strip_tags($match[1]))
        : str_replace(['-', '_'], ' ', pathinfo($path, PATHINFO_FILENAME));
}

$files = $testsDir ? testFiles($testsDir) : [];
$requested = basename((string)($_GET['test'] ?? ''));
$selected = null;
foreach ($files as $file) {
    if ($requested === basename($file, '.md')) { $selected = $file; break; }
}
if (!$selected && $files) $selected = $files[0];

$parser = new Parsedown();
if (method_exists($parser, 'setSafeMode')) $parser->setSafeMode(true);
$markdown = $selected ? (file_get_contents($selected) ?: '') : '# No gadget tests installed';
$title = $selected ? testTitle($selected) : 'Gadget Tests';
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= e($title) ?> | CodyNick Gadget Tests</title>
    <style>
        :root { --bg:#f4f6f8; --panel:#fff; --text:#172033; --muted:#667085; --line:#d8dee8; --accent:#176b57; --code:#111827; }
        * { box-sizing:border-box; } body { margin:0; color:var(--text); background:var(--bg); font:16px/1.6 system-ui,sans-serif; }
        header { min-height:64px; display:flex; align-items:center; gap:18px; padding:12px 24px; background:#172033; color:#fff; }
        header strong { font-size:20px; } header a { color:#d9f4ec; margin-left:auto; }
        .layout { min-height:calc(100vh - 64px); display:grid; grid-template-columns:290px minmax(0,1fr); }
        nav { padding:22px; background:var(--panel); border-right:1px solid var(--line); }
        nav h2 { margin:0 0 14px; font-size:15px; text-transform:uppercase; color:var(--muted); }
        nav a { display:block; padding:10px 12px; margin:4px 0; border-radius:6px; color:var(--text); text-decoration:none; }
        nav a.active, nav a:hover { color:#fff; background:var(--accent); }
        main { min-width:0; padding:32px clamp(20px,5vw,72px); }
        article { max-width:920px; margin:auto; padding:34px 42px; background:var(--panel); border:1px solid var(--line); border-radius:8px; }
        h1,h2,h3 { line-height:1.25; } h1 { margin-top:0; } pre { overflow:auto; padding:46px 16px 16px; background:var(--code); color:#f8fafc; border-radius:6px; }
        code { font-family:ui-monospace,monospace; } :not(pre)>code { padding:2px 5px; background:#edf1f5; border-radius:4px; }
        blockquote { margin-left:0; padding-left:16px; border-left:4px solid var(--accent); color:#405065; }
        .managed-notice { max-width:920px; margin:0 auto 16px; padding:12px 16px; border:1px solid #e7bd69; border-radius:6px; background:#fff7e6; color:#59420f; }
        .code-wrap { position:relative; margin:1.25em 0; } .code-wrap pre { margin:0; }
        .copy-code { position:absolute; top:9px; right:9px; border:1px solid #475569; background:#1f2937; color:#fff; border-radius:5px; padding:6px 10px; cursor:pointer; }
        @media(max-width:760px){ .layout{grid-template-columns:1fr} nav{border-right:0;border-bottom:1px solid var(--line)} article{padding:24px 20px} header span{display:none} }
    </style>
</head>
<body>
<header><strong>CodyNick Gadget Tests</strong><span>Public hardware checks</span><a href="/">Main panel</a></header>
<div class="layout">
    <nav><h2>Gadgets</h2><?php foreach ($files as $file): $slug = basename($file, '.md'); ?>
        <a class="<?= $selected === $file ? 'active' : '' ?>" href="?test=<?= rawurlencode($slug) ?>"><?= e(testTitle($file)) ?></a>
    <?php endforeach; ?></nav>
    <main>
        <p class="managed-notice"><strong>System-managed tests:</strong> setup replaces this folder with the latest official tests. Save personal work in another folder.</p>
        <article><?= $parser->text($markdown) ?></article>
    </main>
</div>
<script>
document.querySelectorAll('article pre').forEach(function(pre) {
    const wrap = document.createElement('div'); wrap.className = 'code-wrap';
    pre.parentNode.insertBefore(wrap, pre); wrap.appendChild(pre);
    const button = document.createElement('button'); button.className = 'copy-code'; button.type = 'button'; button.textContent = 'Copy'; wrap.appendChild(button);
    button.addEventListener('click', async function() {
        const text = pre.textContent || '';
        try { await navigator.clipboard.writeText(text); button.textContent = 'Copied'; }
        catch (_) { const area=document.createElement('textarea'); area.value=text; document.body.appendChild(area); area.select(); document.execCommand('copy'); area.remove(); button.textContent='Copied'; }
        setTimeout(function(){ button.textContent='Copy'; }, 1400);
    });
});
</script>
</body>
</html>
