<?php
/**
 * Simple PHP Documentation App
 * Categories are folders inside /docs. Pages are .md files inside those folders.
 * Requires Parsedown.php in /vendor/parsedown/Parsedown.php.
 */

$config = require __DIR__ . '/config.php';
require_once __DIR__ . '/vendor/parsedown/Parsedown.php';

$docsDir = realpath($config['docs_dir']);
if (!$docsDir || !is_dir($docsDir)) {
    http_response_code(500);
    exit('Docs directory not found.');
}

$Parsedown = new Parsedown();
if (method_exists($Parsedown, 'setSafeMode')) {
    $Parsedown->setSafeMode(false);
}

function e(string $value): string {
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function textContains(string $haystack, string $needle): bool {
    return stripos($haystack, $needle) !== false;
}

function lowerText(string $value): string {
    return function_exists('mb_strtolower') ? mb_strtolower($value, 'UTF-8') : strtolower($value);
}

function textPos(string $haystack, string $needle) {
    return function_exists('mb_stripos') ? mb_stripos($haystack, $needle, 0, 'UTF-8') : stripos($haystack, $needle);
}

function textLen(string $value): int {
    return function_exists('mb_strlen') ? mb_strlen($value, 'UTF-8') : strlen($value);
}

function textSubstr(string $value, int $start, ?int $length = null): string {
    if (function_exists('mb_substr')) {
        return $length === null ? mb_substr($value, $start, null, 'UTF-8') : mb_substr($value, $start, $length, 'UTF-8');
    }
    return $length === null ? substr($value, $start) : substr($value, $start, $length);
}

function isInsidePath(string $candidate, string $base): bool {
    $candidate = rtrim(str_replace('\\', '/', $candidate), '/') . '/';
    $base = rtrim(str_replace('\\', '/', $base), '/') . '/';
    return strncmp($candidate, $base, strlen($base)) === 0;
}

function titleFromMarkdown(string $markdown, string $fallback): string {
    if (preg_match('/^\s*#\s+(.+)$/m', $markdown, $m)) {
        return trim(strip_tags($m[1]));
    }
    return basename($fallback, '.md');
}

function cleanPageParam(?string $page): string {
    $page = trim((string)$page);
    $page = str_replace('\\', '/', $page);
    $page = preg_replace('#/+#', '/', $page);
    $page = preg_replace('/\.md$/i', '', $page);
    $parts = [];
    foreach (explode('/', $page) as $part) {
        $part = trim($part);
        if ($part === '' || $part === '.' || $part === '..') continue;
        $parts[] = $part;
    }
    return implode('/', $parts);
}

function pageToFile(string $docsDir, string $page): ?string {
    $page = cleanPageParam($page);
    if ($page === '') return null;
    $candidate = realpath($docsDir . '/' . $page . '.md');
    if (!$candidate || !is_file($candidate)) return null;
    return isInsidePath($candidate, $docsDir) ? $candidate : null;
}

function fileToPage(string $docsDir, string $file): string {
    $relative = substr($file, strlen($docsDir) + 1);
    $relative = str_replace(DIRECTORY_SEPARATOR, '/', $relative);
    return preg_replace('/\.md$/i', '', $relative);
}

function displayName(string $name): string {
    $name = preg_replace('/^[0-9]+[-_ ]*/', '', $name);
    $name = str_replace(['-', '_'], ' ', $name);
    return trim($name) ?: $name;
}

function logoUrl(array $config): string {
    $path = trim((string)($config['logo_path'] ?? ''));
    if ($path === '') return '';
    if (preg_match('#^https?://#i', $path) || substr($path, 0, 1) === '/') return $path;
    return $path;
}

function collectMarkdownFiles(string $dir): array {
    $files = [];
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS),
        RecursiveIteratorIterator::SELF_FIRST
    );
    foreach ($iterator as $item) {
        if ($item->isFile() && strtolower($item->getExtension()) === 'md') {
            $files[] = $item->getPathname();
        }
    }
    sort($files, SORT_NATURAL | SORT_FLAG_CASE);
    return $files;
}

function buildTree(string $dir, string $docsDir, string $activePage): string {
    $items = array_values(array_filter(scandir($dir) ?: [], fn($x) => $x !== '.' && $x !== '..'));
    usort($items, function($a, $b) use ($dir) {
        $aDir = is_dir($dir . '/' . $a);
        $bDir = is_dir($dir . '/' . $b);
        if ($aDir !== $bDir) return $aDir ? -1 : 1;
        return strnatcasecmp($a, $b);
    });

    $html = '<ul class="nav-list">';
    foreach ($items as $item) {
        $path = $dir . '/' . $item;
        if (is_dir($path)) {
            $relativeFolder = trim(str_replace(DIRECTORY_SEPARATOR, '/', substr(realpath($path), strlen($docsDir) + 1)), '/');
            $open = $activePage === $relativeFolder || strpos($activePage . '/', $relativeFolder . '/') === 0 ? ' open' : '';
            $html .= '<li><details' . $open . '><summary><span class="folder-icon">▸</span>' . e(displayName($item)) . '</summary>';
            $html .= buildTree($path, $docsDir, $activePage);
            $html .= '</details></li>';
        } elseif (strtolower(pathinfo($path, PATHINFO_EXTENSION)) === 'md') {
            $page = fileToPage($docsDir, realpath($path));
            $title = titleFromMarkdown(file_get_contents($path) ?: '', $item);
            $active = $page === $activePage ? ' active' : '';
            $html .= '<li><a class="nav-link' . $active . '" href="?p=' . rawurlencode($page) . '">' . e($title) . '</a></li>';
        }
    }
    $html .= '</ul>';
    return $html;
}

function makeSnippet(string $text, string $query): string {
    $plain = trim(preg_replace('/\s+/', ' ', strip_tags($text)) ?? '');
    $pos = textPos($plain, $query);
    if ($pos === false) {
        return e(textSubstr($plain, 0, 220)) . (textLen($plain) > 220 ? '…' : '');
    }
    $start = max(0, (int)$pos - 80);
    $snippet = textSubstr($plain, $start, 260);
    if ($start > 0) $snippet = '…' . $snippet;
    if ($start + 260 < textLen($plain)) $snippet .= '…';
    return preg_replace('/(' . preg_quote($query, '/') . ')/iu', '<mark>$1</mark>', e($snippet)) ?? e($snippet);
}

function searchDocs(string $docsDir, string $query, int $limit): array {
    $query = trim($query);
    if ($query === '') return [];

    $results = [];
    foreach (collectMarkdownFiles($docsDir) as $file) {
        $markdown = file_get_contents($file) ?: '';
        $plain = strip_tags(preg_replace('/[`*_>#\[\]()!-]+/', ' ', $markdown));
        $title = titleFromMarkdown($markdown, basename($file));
        $haystack = lowerText($title . ' ' . $plain);
        $needle = lowerText($query);
        if ($needle !== '' && strpos($haystack, $needle) !== false) {
            $score = 0;
            if (strpos(lowerText($title), $needle) !== false) $score += 10;
            $score += substr_count($haystack, $needle);
            $results[] = [
                'title' => $title,
                'page' => fileToPage($docsDir, realpath($file)),
                'snippet' => makeSnippet($plain, $query),
                'score' => $score,
            ];
        }
    }
    usort($results, fn($a, $b) => $b['score'] <=> $a['score'] ?: strnatcasecmp($a['title'], $b['title']));
    return array_slice($results, 0, $limit);
}

$requestedPage = cleanPageParam($_GET['p'] ?? $config['default_page']);
$pageFile = pageToFile($docsDir, $requestedPage);
if (!$pageFile) {
    $allFiles = collectMarkdownFiles($docsDir);
    $pageFile = $allFiles[0] ?? null;
    $requestedPage = $pageFile ? fileToPage($docsDir, realpath($pageFile)) : '';
}

$query = trim((string)($_GET['q'] ?? ''));
$isSearch = $query !== '';
$searchResults = $isSearch ? searchDocs($docsDir, $query, (int)$config['max_search_results']) : [];

$markdown = $pageFile ? (file_get_contents($pageFile) ?: '') : '# No documentation found\n\nCreate Markdown files inside the `/docs` folder.';
$pageTitle = $isSearch ? 'Search' : titleFromMarkdown($markdown, basename($pageFile ?: 'Documentation'));
$contentHtml = $Parsedown->text($markdown);
$navHtml = buildTree($docsDir, $docsDir, $requestedPage);
$logoUrl = logoUrl($config);
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= e($pageTitle) ?> · <?= e($config['site_title']) ?></title>
    <style>
        :root {
            --bg: #f6f7fb;
            --panel: #ffffff;
            --panel-2: #f0f3f8;
            --text: #172033;
            --muted: #667085;
            --border: #d9e0ea;
            --primary: #2563eb;
            --primary-2: #1d4ed8;
            --code-bg: #111827;
            --code-text: #e5e7eb;
            --shadow: 0 18px 45px rgba(15, 23, 42, .08);
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            background: var(--bg);
            color: var(--text);
            font: 15px/1.65 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
        }
        a { color: var(--primary); text-decoration: none; }
        a:hover { color: var(--primary-2); }
        .topbar {
            position: sticky;
            top: 0;
            z-index: 10;
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 14px 24px;
            background: rgba(255,255,255,.86);
            border-bottom: 1px solid var(--border);
            backdrop-filter: blur(14px);
        }
        .brand { display: flex; align-items: center; gap: 12px; min-width: 255px; color: inherit; }
        .brand-logo, .badge {
            flex: 0 0 auto;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(37, 99, 235, .18);
        }
        .brand-logo { object-fit: contain; background: #fff; border: 1px solid var(--border); padding: 4px; }
        .badge {
            display: inline-grid;
            place-items: center;
            background: linear-gradient(135deg, var(--primary), #7c3aed);
            color: #fff;
            font-weight: 800;
            letter-spacing: .02em;
        }
        .brand-title { font-weight: 800; line-height: 1.1; }
        .brand-subtitle { color: var(--muted); font-size: 12px; line-height: 1.2; margin-top: 2px; }
        .search {
            flex: 1;
            max-width: 760px;
            display: grid;
            grid-template-columns: minmax(0, 1fr) 44px;
            align-items: center;
            gap: 8px;
        }
        .search input {
            min-width: 0;
            width: 100%;
            height: 44px;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0 16px;
            background: var(--panel);
            color: var(--text);
            outline: none;
            box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
            line-height: 44px;
        }
        .search input:focus { border-color: rgba(37, 99, 235, .55); box-shadow: 0 0 0 4px rgba(37, 99, 235, .10); }
        .search button {
            width: 44px;
            height: 44px;
            border: 0;
            background: var(--primary);
            color: white;
            border-radius: 14px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }
        .search button svg { width: 19px; height: 19px; display: block; }
        .layout { display: grid; grid-template-columns: 300px minmax(0, 1fr); min-height: calc(100vh - 67px); }
        .sidebar {
            position: sticky;
            top: 67px;
            height: calc(100vh - 67px);
            overflow: auto;
            padding: 22px 18px;
            border-right: 1px solid var(--border);
            background: #fbfcff;
        }
        .sidebar-heading { margin: 0 0 12px; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; font-weight: 800; }
        .nav-list { list-style: none; margin: 0; padding: 0; }
        .nav-list .nav-list { padding-left: 14px; margin-top: 4px; border-left: 1px solid var(--border); }
        .nav-list li { margin: 2px 0; }
        details summary {
            cursor: pointer;
            user-select: none;
            color: #344054;
            font-weight: 700;
            padding: 8px 8px;
            border-radius: 10px;
            list-style: none;
        }
        details summary::-webkit-details-marker { display: none; }
        details[open] > summary .folder-icon { transform: rotate(90deg); }
        .folder-icon { display: inline-block; margin-right: 8px; color: var(--muted); transition: transform .15s ease; }
        .nav-link {
            display: block;
            padding: 8px 10px;
            border-radius: 10px;
            color: #475467;
        }
        .nav-link:hover, details summary:hover { background: var(--panel-2); color: var(--text); }
        .nav-link.active { background: #e8f0ff; color: var(--primary-2); font-weight: 800; }
        main { min-width: 0; padding: 32px; }
        .content-shell { max-width: 980px; margin: 0 auto; }
        .breadcrumbs { color: var(--muted); font-size: 13px; margin-bottom: 14px; }
        .card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 22px;
            box-shadow: var(--shadow);
            overflow: hidden;
        }
        .doc-content { padding: 38px 44px; }
        .doc-content h1 { margin-top: 0; font-size: 38px; line-height: 1.15; letter-spacing: -0.03em; }
        .doc-content h2 { margin-top: 2.1em; padding-top: .4em; border-top: 1px solid var(--border); font-size: 26px; letter-spacing: -0.02em; }
        .doc-content h3 { margin-top: 1.8em; font-size: 20px; }
        .doc-content p, .doc-content li { color: #344054; }
        .doc-content code {
            padding: 2px 6px;
            border-radius: 7px;
            background: #eef2f7;
            color: #1f2937;
            font-size: .92em;
        }
        .doc-content pre {
            overflow: auto;
            padding: 18px;
            border-radius: 16px;
            background: var(--code-bg);
            color: var(--code-text);
        }
        .doc-content pre code { background: transparent; color: inherit; padding: 0; }
        .code-wrap { position: relative; margin: 1.25em 0; }
        .code-wrap pre { margin: 0; padding-top: 46px; }
        .copy-code-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            border: 1px solid rgba(255,255,255,.14);
            background: rgba(255,255,255,.08);
            color: var(--code-text);
            border-radius: 10px;
            padding: 6px 10px;
            font-size: 12px;
            cursor: pointer;
        }
        .copy-code-btn:hover { background: rgba(255,255,255,.16); }
        .copy-code-btn.copied { background: rgba(34,197,94,.22); border-color: rgba(34,197,94,.35); }
        .doc-content blockquote {
            margin: 1.5em 0;
            padding: 1px 18px;
            border-left: 4px solid var(--primary);
            background: #f8fafc;
            border-radius: 0 12px 12px 0;
        }
        .doc-content table { width: 100%; border-collapse: collapse; margin: 1.5em 0; }
        .doc-content th, .doc-content td { border: 1px solid var(--border); padding: 10px 12px; text-align: left; }
        .doc-content th { background: #f8fafc; }
        .search-title { margin: 0 0 8px; font-size: 34px; letter-spacing: -0.03em; }
        .search-meta { color: var(--muted); margin-bottom: 24px; }
        .result { padding: 20px 0; border-top: 1px solid var(--border); }
        .result:first-of-type { border-top: 0; }
        .result a { font-size: 19px; font-weight: 800; color: var(--text); }
        .result a:hover { color: var(--primary); }
        .result-path { color: var(--muted); font-size: 12px; margin-top: 3px; }
        .result-snippet { margin: 8px 0 0; color: #475467; }
        mark { background: #fef3c7; color: #92400e; padding: 0 3px; border-radius: 4px; }
        .empty { padding: 24px; border: 1px dashed var(--border); border-radius: 16px; color: var(--muted); background: #fbfcff; }
        .footer { color: var(--muted); font-size: 13px; text-align: center; margin-top: 22px; }
        .mobile-menu { display: none; }
        @media (max-width: 860px) {
            .topbar { align-items: stretch; flex-wrap: wrap; padding: 12px 14px; }
            .brand { min-width: 0; flex: 1; }
            .search { order: 3; max-width: none; width: 100%; flex-basis: 100%; }
            .mobile-menu { display: inline-flex; align-items: center; border: 1px solid var(--border); background: var(--panel); border-radius: 10px; padding: 0 12px; }
            .layout { grid-template-columns: 1fr; }
            .sidebar { display: none; position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--border); }
            body.nav-open .sidebar { display: block; }
            main { padding: 18px; }
            .doc-content { padding: 26px 22px; }
            .doc-content h1 { font-size: 30px; }
        }
    </style>
</head>
<body>
    <header class="topbar">
        <button class="mobile-menu" type="button" onclick="document.body.classList.toggle('nav-open')">Menu</button>
        <a class="brand" href="?p=<?= rawurlencode($config['default_page']) ?>">
            <?php if ($logoUrl !== ''): ?>
                <img class="brand-logo" src="<?= e($logoUrl) ?>" alt="<?= e($config['site_title']) ?> logo">
            <?php else: ?>
                <span class="badge"><?= e(substr($config['brand_badge'], 0, 2)) ?></span>
            <?php endif; ?>
            <span>
                <span class="brand-title"><?= e($config['site_title']) ?></span><br>
                <span class="brand-subtitle"><?= e($config['site_subtitle']) ?></span>
            </span>
        </a>
        <form class="search" method="get" action="">
            <input name="q" value="<?= e($query) ?>" placeholder="Search documentation…" aria-label="Search documentation">
            <button type="submit" title="Search" aria-label="Search"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M10.75 4a6.75 6.75 0 0 1 5.34 10.88l3.52 3.51a.86.86 0 0 1-1.22 1.22l-3.51-3.52A6.75 6.75 0 1 1 10.75 4Zm0 1.75a5 5 0 1 0 0 10 5 5 0 0 0 0-10Z" fill="currentColor"/></svg></button>
        </form>
    </header>

    <div class="layout">
        <aside class="sidebar">
            <p class="sidebar-heading">Documentation</p>
            <?= $navHtml ?>
        </aside>
        <main>
            <div class="content-shell">
                <div class="breadcrumbs">
                    <?= $isSearch ? 'Search results' : e(str_replace('/', ' / ', $requestedPage)) ?>
                </div>
                <section class="card doc-content">
                    <?php if ($isSearch): ?>
                        <h1 class="search-title">Search results</h1>
                        <div class="search-meta"><?= count($searchResults) ?> result<?= count($searchResults) === 1 ? '' : 's' ?> for “<?= e($query) ?>”</div>
                        <?php if (!$searchResults): ?>
                            <div class="empty">No matching pages found. Try a shorter keyword or create more Markdown pages in the docs folder.</div>
                        <?php else: ?>
                            <?php foreach ($searchResults as $result): ?>
                                <article class="result">
                                    <a href="?p=<?= rawurlencode($result['page']) ?>"><?= e($result['title']) ?></a>
                                    <div class="result-path"><?= e($result['page']) ?>.md</div>
                                    <p class="result-snippet"><?= $result['snippet'] ?></p>
                                </article>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    <?php else: ?>
                        <?= $contentHtml ?>
                    <?php endif; ?>
                </section>
                <div class="footer"><?= e($config['footer_text']) ?></div>
            </div>
        </main>
    </div>
    <script>
        document.addEventListener('keydown', function (event) {
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
                event.preventDefault();
                const input = document.querySelector('.search input');
                if (input) input.focus();
            }
        });

        document.querySelectorAll('.doc-content pre').forEach(function (pre) {
            if (pre.closest('.code-wrap')) return;

            const wrapper = document.createElement('div');
            wrapper.className = 'code-wrap';
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(pre);

            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'copy-code-btn';
            button.textContent = 'Copy';
            wrapper.appendChild(button);

            function showCopied() {
                button.textContent = 'Copied';
                button.classList.add('copied');
                setTimeout(function () {
                    button.textContent = 'Copy';
                    button.classList.remove('copied');
                }, 1400);
            }

            function fallbackCopy(text) {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.setAttribute('readonly', '');
                textarea.style.position = 'fixed';
                textarea.style.top = '-9999px';
                textarea.style.left = '-9999px';
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                let copied = false;
                try { copied = document.execCommand('copy'); } catch (error) { copied = false; }
                document.body.removeChild(textarea);
                return copied;
            }

            button.addEventListener('click', async function () {
                const code = pre.textContent || '';
                try {
                    if (navigator.clipboard && window.isSecureContext) {
                        await navigator.clipboard.writeText(code);
                        showCopied();
                        return;
                    }
                    if (fallbackCopy(code)) {
                        showCopied();
                        return;
                    }
                    button.textContent = 'Copy failed';
                    setTimeout(function () { button.textContent = 'Copy'; }, 1600);
                } catch (error) {
                    if (fallbackCopy(code)) {
                        showCopied();
                    } else {
                        button.textContent = 'Copy failed';
                        setTimeout(function () { button.textContent = 'Copy'; }, 1600);
                    }
                }
            });
        });
    </script>
</body>
</html>
