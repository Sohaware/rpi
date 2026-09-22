<?php
/*
  CodyNick Blockly IDE - single-file PHP application

  Folders/files used by this file:
  - blocks/*.json        Drop-in block packages
  - main.json           Server-side saved Blockly arrangement
  - active_script.py    Generated Python output file by default

  CodyNick.py is intentionally NOT included in this project. The generated code
  is expected to run in another location where CodyNick.py is already available.

  Change this path to the file your runner service executes:
*/
$PYTHON_OUTPUT_FILE = '/home/client/active_script.py';
$DATA_DIR           = __DIR__ . '/data';
$MAIN_JSON_FILE     = $DATA_DIR . '/main.json';
$BLOCKS_DIR         = __DIR__ . '/blocks';
$APP_TITLE          = 'CodyNick Block IDE';
$LOGO_TEXT          = 'CN';

if (!is_dir($BLOCKS_DIR)) {
    mkdir($BLOCKS_DIR, 0775, true);
}

if (!is_dir($DATA_DIR)) {
    mkdir($DATA_DIR, 0777, true);
}
if (is_dir($DATA_DIR) && !is_writable($DATA_DIR)) {
    @chmod($DATA_DIR, 0777);
}

function json_response($data, int $status = 200): void {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}

function read_json_body(): array {
    $raw = file_get_contents('php://input');
    if ($raw === false || trim($raw) === '') {
        return [];
    }

    $data = json_decode($raw, true);
    if (!is_array($data)) {
        json_response(['ok' => false, 'error' => 'Invalid JSON body.'], 400);
    }

    return $data;
}

function safe_write_file(string $path, string $content, ?string &$error = null): bool {
    $error = null;
    $dir = dirname($path);

    if (!is_dir($dir)) {
        if (!mkdir($dir, 0777, true) && !is_dir($dir)) {
            $error = 'Could not create directory: ' . $dir;
            return false;
        }
    }

    if (!is_writable($dir)) {
        @chmod($dir, 0777);
    }

    if (!is_writable($dir)) {
        $error = 'Directory is not writable by the web server: ' . $dir;
        return false;
    }

    $tmp = tempnam($dir, '.tmp_');
    if ($tmp === false) {
        $error = 'Could not create temporary file in: ' . $dir;
        return false;
    }

    $bytes = file_put_contents($tmp, $content, LOCK_EX);
    if ($bytes === false) {
        $last = error_get_last();
        @unlink($tmp);
        $error = 'Could not write temporary file. ' . ($last['message'] ?? '');
        return false;
    }

    @chmod($tmp, 0666);

    if (!@rename($tmp, $path)) {
        // Fallback for environments where rename over an existing file is restricted.
        $bytes = @file_put_contents($path, $content, LOCK_EX);
        @unlink($tmp);

        if ($bytes === false) {
            $last = error_get_last();
            $error = 'Could not replace file: ' . $path . '. ' . ($last['message'] ?? '');
            return false;
        }
    }

    @chmod($path, 0666);
    return true;
}

function load_block_packages(string $blocksDir): array {
    $packages = [];
    $warnings = [];

    foreach (glob($blocksDir . '/*.json') ?: [] as $file) {
        $raw = file_get_contents($file);
        $json = json_decode($raw, true);

        if (!is_array($json)) {
            $warnings[] = basename($file) . ' is not valid JSON.';
            continue;
        }

        if (empty($json['id']) || empty($json['blocks']) || !is_array($json['blocks'])) {
            $warnings[] = basename($file) . ' does not look like a block package.';
            continue;
        }

        $packages[] = $json;
    }

    return [$packages, $warnings];
}

[$BLOCK_PACKAGES, $BLOCK_WARNINGS] = load_block_packages($BLOCKS_DIR);

$api = $_GET['api'] ?? null;

if ($api === 'load') {
    if (is_file($MAIN_JSON_FILE)) {
        $raw = file_get_contents($MAIN_JSON_FILE);
        $json = json_decode($raw, true);
        if (is_array($json)) {
            json_response(['ok' => true, 'workspace' => $json]);
        }
    }

    json_response(['ok' => true, 'workspace' => null]);
}

if ($api === 'save') {
    $data = read_json_body();
    if (!isset($data['workspace']) || !is_array($data['workspace'])) {
        json_response(['ok' => false, 'error' => 'Missing workspace JSON.'], 400);
    }

    $pretty = json_encode($data['workspace'], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    $writeError = null;
    if (!safe_write_file($MAIN_JSON_FILE, $pretty . PHP_EOL, $writeError)) {
        json_response([
            'ok' => false,
            'error' => 'Could not save workspace JSON. ' . ($writeError ?: 'Check web-server permissions.'),
            'path' => $MAIN_JSON_FILE
        ], 500);
    }

    json_response(['ok' => true]);
}

if ($api === 'run') {
    $data = read_json_body();

    if (!isset($data['python']) || !is_string($data['python'])) {
        json_response(['ok' => false, 'error' => 'Missing generated Python code.'], 400);
    }

    if (!isset($data['workspace']) || !is_array($data['workspace'])) {
        json_response(['ok' => false, 'error' => 'Missing workspace JSON.'], 400);
    }

    $python = rtrim($data['python']) . PHP_EOL . '# CodyNick run: ' . bin2hex(random_bytes(8)) . PHP_EOL;
    $workspacePretty = json_encode($data['workspace'], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);

    $pythonWriteError = null;
    // The installer grants access to this file, not the entire client home directory.
    if (is_link($PYTHON_OUTPUT_FILE) || !is_file($PYTHON_OUTPUT_FILE)
        || file_put_contents($PYTHON_OUTPUT_FILE, $python, LOCK_EX) === false) {
        json_response([
            'ok' => false,
            'error' => 'Could not write Python output file. ' . ($pythonWriteError ?: 'Check web-server permissions.'),
            'path' => $PYTHON_OUTPUT_FILE
        ], 500);
    }

    $jsonWriteError = null;
    if (!safe_write_file($MAIN_JSON_FILE, $workspacePretty . PHP_EOL, $jsonWriteError)) {
        json_response([
            'ok' => false,
            'error' => 'Python was written, but workspace JSON could not be saved. ' . ($jsonWriteError ?: 'Check web-server permissions.'),
            'path' => $MAIN_JSON_FILE
        ], 500);
    }

    json_response([
        'ok' => true,
        'message' => 'Python generated and saved.',
        'bytes' => strlen($python),
        'outputFile' => basename($PYTHON_OUTPUT_FILE)
    ]);
}
?><!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title><?= htmlspecialchars($APP_TITLE, ENT_QUOTES, 'UTF-8') ?></title>

  <!-- For offline deployment, download Blockly and replace these two script URLs with local files. -->
  <script src="/blocks/vendor/blockly/blockly.min.js"></script>

  <style>
    :root {
      --bg: #f7fafc;
      --panel: #ffffff;
      --panel-soft: #f8fafc;
      --line: #e2e8f0;
      --text: #0f172a;
      --muted: #64748b;
      --blue: #4c97ff;
      --green: #22c55e;
      --green-dark: #16a34a;
      --orange: #ffab19;
      --purple: #9966ff;
      --red: #ff6680;
      --shadow: none;
      --radius: 10px;
      --header-height: 72px;
    }

    * { box-sizing: border-box; }

    html, body {
      width: 100%;
      height: 100%;
      margin: 0;
      overflow: hidden;
      font-family: Inter, Arial, Helvetica, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 10% 0%, rgba(76, 151, 255, 0.18), transparent 32%),
        radial-gradient(circle at 100% 20%, rgba(255, 171, 25, 0.18), transparent 28%),
        linear-gradient(135deg, #eef2ff, #f8fafc 42%, #ecfeff);
    }

    .app {
      width: 100vw;
      height: 100vh;
      display: grid;
      grid-template-rows: var(--header-height) minmax(0, 1fr);
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      height: var(--header-height);
      padding: 10px 16px;
      background: rgba(255, 255, 255, 0.90);
      border-bottom: 1px solid rgba(226, 232, 240, 0.9);
      backdrop-filter: none;
      z-index: 5;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 280px;
    }

    .logo {
      width: 48px;
      height: 48px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      color: #ffffff;
      font-weight: 950;
      letter-spacing: -0.05em;
      background:
        radial-gradient(circle at 30% 20%, rgba(255,255,255,.45), transparent 20%),
        linear-gradient(135deg, var(--blue), var(--purple));
      box-shadow: none;
    }

    .brand-title {
      display: flex;
      flex-direction: column;
      line-height: 1.08;
    }

    .brand-title strong {
      font-size: 20px;
      letter-spacing: -0.03em;
    }

    .brand-title span {
      margin-top: 4px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }

    .toolbar {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
    }

    button, .file-button {
      border: 0;
      border-radius: 6px;
      min-height: 40px;
      padding: 0 15px;
      font-weight: 900;
      cursor: pointer;
      color: #0f172a;
      background: #ffffff;
      border: 1px solid var(--line);
      box-shadow: none;
      transition: background .12s ease, border-color .12s ease;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      font-size: 13px;
    }

    button:hover, .file-button:hover {
      background: #f6f8fa;
      border-color: #d0d7de;
    }

    .run-btn {
      min-width: 112px;
      color: white;
      background: #2da44e;
      border: 1px solid rgba(27, 31, 36, 0.15);
      box-shadow: none;
      font-size: 15px;
    }

    .danger-btn {
      color: #be123c;
    }

    .run-btn:hover {
      background: #2c974b;
      border-color: rgba(27, 31, 36, 0.15);
    }

    #importFile {
      display: none;
    }

    .main {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 12px;
      padding: 12px;
      min-height: 0;
    }

    .workspace-shell {
      min-height: 0;
      border-radius: var(--radius);
      overflow: hidden;
      background: #ffffff;
      border: 1px solid #d0d7de;
      box-shadow: var(--shadow);
      backdrop-filter: none;
    }

    .workspace-shell {
      display: grid;
      grid-template-rows: 42px minmax(0, 1fr);
    }

    .panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      height: 42px;
      padding: 0 14px;
      background: rgba(248,250,252,.92);
      border-bottom: 1px solid var(--line);
      font-size: 13px;
      font-weight: 950;
    }

    .status {
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }

    .status.ok { color: #15803d; }
    .status.err { color: #be123c; }

    #blocklyDiv {
      width: 100%;
      height: 100%;
      min-height: 0;
    }


    .modal-backdrop {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: rgba(15, 23, 42, 0.42);
      z-index: 30;
    }

    .modal-backdrop.open {
      display: flex;
    }

    .modal {
      width: min(920px, 100%);
      height: min(720px, 90vh);
      display: grid;
      grid-template-rows: 52px minmax(0, 1fr);
      background: #ffffff;
      border: 1px solid #d0d7de;
      border-radius: 10px;
      overflow: hidden;
    }

    .modal-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 0 12px 0 16px;
      background: #f6f8fa;
      border-bottom: 1px solid #d0d7de;
      font-weight: 900;
    }

    .modal-actions {
      display: flex;
      gap: 8px;
    }

    #pythonPreview {
      margin: 0;
      width: 100%;
      height: 100%;
      overflow: auto;
      padding: 16px;
      background: #0d1117;
      color: #dbeafe;
      font: 13px/1.55 Consolas, Monaco, "Courier New", monospace;
      white-space: pre;
    }

    .server-note {
      display: flex;
      align-items: center;
      padding: 0 14px;
      color: var(--muted);
      background: var(--panel-soft);
      border-top: 1px solid var(--line);
      font-size: 12px;
      font-weight: 700;
    }

    .toast {
      position: fixed;
      right: 16px;
      bottom: 16px;
      max-width: 440px;
      padding: 12px 14px;
      border-radius: 8px;
      background: #0f172a;
      color: #fff;
      box-shadow: 0 18px 45px rgba(15,23,42,.25);
      font-size: 13px;
      font-weight: 800;
      opacity: 0;
      transform: translateY(10px);
      pointer-events: none;
      transition: opacity .18s ease, transform .18s ease;
      z-index: 20;
    }

    .toast.show {
      opacity: 1;
      transform: translateY(0);
    }

    /* Scratch-like Blockly polish without Scratch code/libraries */
    .blocklyMainBackground {
      stroke-width: 0;
    }

    .blocklyToolboxDiv {
      background: #ffffff !important;
      border-right: 1px solid #e2e8f0;
      box-shadow: 10px 0 22px rgba(15, 23, 42, 0.06);
      padding-top: 8px;
    }

    .blocklyTreeRow {
      height: 44px !important;
      line-height: 44px !important;
      margin: 5px 9px !important;
      border-radius: 14px;
      padding-inline-start: 14px !important;
      transition: background .12s ease, transform .12s ease;
    }

    .blocklyTreeRow:hover {
      background: rgba(76,151,255,.10);
      transform: translateX(1px);
    }

    .blocklyTreeSelected {
      background: rgba(76,151,255,.18) !important;
    }

    .blocklyTreeLabel {
      font-size: 15px !important;
      font-weight: 900 !important;
      color: #334155 !important;
    }

    .blocklyTreeIcon {
      width: 8px !important;
      height: 8px !important;
      border-radius: 6px;
      margin-right: 8px;
      background: currentColor;
      opacity: .75;
    }

    .blocklyFlyoutBackground {
      fill: #f8fafc;
      fill-opacity: .985;
    }

    .blocklyFlyout {
      filter: drop-shadow(6px 0 12px rgba(15, 23, 42, 0.10));
    }

    .blocklyScrollbarHandle {
      rx: 8;
      ry: 8;
    }

    .blocklyZoom > image,
    .blocklyTrash > image {
      opacity: .9;
    }

    @media (max-width: 980px) {
      .main {
        grid-template-columns: 1fr;
        grid-template-rows: minmax(0, 1fr) 300px;
      }

      .brand {
        min-width: 0;
      }

      .brand-title span {
        display: none;
      }

      .toolbar button:not(.run-btn),
      .file-button {
        padding: 0 11px;
      }
    }
  </style>
</head>
<body>
<div class="app">
  <header class="topbar">
    <div class="brand">
      <div class="logo"><?= htmlspecialchars($LOGO_TEXT, ENT_QUOTES, 'UTF-8') ?></div>
      <div class="brand-title">
        <strong><?= htmlspecialchars($APP_TITLE, ENT_QUOTES, 'UTF-8') ?></strong>
        <span>Scratch-like Blockly workspace · Python generator</span>
      </div>
    </div>

    <nav class="toolbar">
      <button onclick="newWorkspace()" title="Clear the workspace">New</button>
      <label class="file-button" for="importFile" title="Upload a workspace JSON file">Upload</label>
      <input id="importFile" type="file" accept="application/json,.json" />
      <button onclick="downloadWorkspace()" title="Download the current workspace JSON">Download</button>
      <button onclick="saveWorkspaceNow()" title="Save block arrangement on server">Save</button>
      <button onclick="viewPython()" title="Preview generated Python in a pop-up">View Python</button>
      <button class="run-btn" onclick="runProgram()" title="Generate Python and replace the configured file">▶ Run</button>
    </nav>
  </header>

  <main class="main">
    <section class="workspace-shell">
      <div class="panel-head">
        <span>Blocks</span>
        <span id="workspaceStatus" class="status">Loading…</span>
      </div>
      <div id="blocklyDiv"></div>
    </section>

  </main>
</div>

<div id="pythonModal" class="modal-backdrop" onclick="closePythonModal(event)">
  <section class="modal" role="dialog" aria-modal="true" aria-label="Generated Python">
    <div class="modal-head">
      <span>Generated Python</span>
      <div class="modal-actions">
        <button onclick="copyPythonPreview(event)">Copy</button>
        <button onclick="closePythonModal(event)">Close</button>
      </div>
    </div>
    <pre id="pythonPreview"># Click “View Python” to generate a preview.</pre>
  </section>
</div>

<div id="toast" class="toast"></div>

<script>
const BLOCK_PACKAGES = <?= json_encode($BLOCK_PACKAGES, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) ?>;
const BLOCK_WARNINGS = <?= json_encode($BLOCK_WARNINGS, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) ?>;

let workspace = null;
let saveTimer = null;
const dynamicBlockSpecs = new Map();

function ensureColourFieldSupport() {
  // Version-safe Blockly color support.
  // Some Blockly builds expose Blockly.FieldColour, some expose only fieldRegistry,
  // and some do not include the color picker at all.
  try {
    if (Blockly.FieldColour && Blockly.fieldRegistry && typeof Blockly.fieldRegistry.register === 'function') {
      try {
        Blockly.fieldRegistry.register('field_colour', Blockly.FieldColour);
      } catch (alreadyRegisteredOrUnsupported) {
        // Safe to ignore: the field may already be registered.
      }
    }
  } catch (e) {
    console.warn('Colour field setup warning:', e);
  }
}


function toast(message, isError = false) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.style.background = isError ? '#be123c' : '#0f172a';
  el.classList.add('show');
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove('show'), 2600);
}

function setStatus(id, text, mode = '') {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.className = 'status ' + mode;
}

function quotePython(value) {
  return JSON.stringify(String(value ?? ''));
}

function safeName(name) {
  return String(name || 'variable')
    .replace(/[^A-Za-z0-9_]/g, '_')
    .replace(/^[^A-Za-z_]+/, '') || 'variable';
}

function variableName(block, fieldName) {
  const id = block.getFieldValue(fieldName);
  const variable = block.workspace.getVariableById(id);
  return safeName(variable ? variable.name : id);
}

function fieldPythonValue(arg, value) {
  if (arg.kind === 'number') {
    const n = Number(value);
    return Number.isFinite(n) ? String(n) : '0';
  }

  if (arg.kind === 'dropdown') {
    return String(value);
  }

  if (arg.kind === 'colour') {
    return quotePython(value);
  }

  return quotePython(value);
}

function blockFieldValue(block, arg) {
  return block.getFieldValue(arg.name);
}

function buildDynamicBlockJson(spec) {
  const args0 = [];
  for (const arg of (spec.args || [])) {
    if (arg.kind === 'number') {
      args0.push({
        type: 'field_number',
        name: arg.name,
        value: Number(arg.default ?? 0)
      });
    } else if (arg.kind === 'dropdown') {
      args0.push({
        type: 'field_dropdown',
        name: arg.name,
        options: arg.options || [['value', String(arg.default ?? '')]]
      });
    } else if (arg.kind === 'colour') {
      // Use Blockly's color picker only when FieldColour exists.
      // Otherwise use a normal dropdown so older/newer Blockly bundles do not crash.
      if (Blockly.FieldColour) {
        args0.push({
          type: 'field_colour',
          name: arg.name,
          colour: arg.default || '#4c97ff'
        });
      } else {
        args0.push({
          type: 'field_dropdown',
          name: arg.name,
          options: [
            ['red', '#FF0000'],
            ['cyan', '#00FFFF'],
            ['blue', '#0000FF'],
            ['yellow', '#FFFF00'],
            ['magenta', '#FF00FF'],
            ['green', '#00FF00'],
            ['orange', '#FF8000'],
            ['white', '#FFFFFF']
          ]
        });
      }
    } else {
      args0.push({
        type: 'field_input',
        name: arg.name,
        text: String(arg.default ?? '')
      });
    }
  }

  const json = {
    type: spec.type,
    message0: spec.label,
    args0,
    colour: spec.colour || '#4c97ff',
    tooltip: spec.tooltip || '',
    helpUrl: ''
  };

  if (spec.output) {
    json.output = spec.output;
  } else {
    json.previousStatement = null;
    json.nextStatement = null;
  }

  return json;
}

function defineEventBlocks() {
  Blockly.Blocks['cn_event_start'] = {
    init: function() {
      this.appendDummyInput().appendField('when CodyNick starts');
      this.appendStatementInput('DO');
      this.setColour('#ffbf00');
      this.setTooltip('Runs once when the generated Python program starts.');
      this.setDeletable(true);
    }
  };

  Blockly.Blocks['cn_event_loop'] = {
    init: function() {
      this.appendDummyInput().appendField('main loop');
      this.appendStatementInput('DO');
      this.setColour('#ffab19');
      this.setTooltip('Blocks here are generated inside while True.');
      this.setDeletable(true);
    }
  };
}

function definePackageBlocks() {
  const jsonBlocks = [];

  for (const pkg of BLOCK_PACKAGES) {
    for (const spec of (pkg.blocks || [])) {
      dynamicBlockSpecs.set(spec.type, spec);
      jsonBlocks.push(buildDynamicBlockJson(spec));
    }
  }

  if (jsonBlocks.length) {
    Blockly.common.defineBlocksWithJsonArray(jsonBlocks);
  }
}

function makeBlock(type) {
  return { kind: 'block', type };
}

function buildToolbox() {
  const dynamicCategories = new Map();

  for (const pkg of BLOCK_PACKAGES) {
    for (const cat of (pkg.categories || [])) {
      if (!dynamicCategories.has(cat.name)) {
        dynamicCategories.set(cat.name, {
          kind: 'category',
          name: cat.name,
          colour: cat.colour || '#4c97ff',
          contents: []
        });
      }
    }

    for (const block of (pkg.blocks || [])) {
      if (!dynamicCategories.has(block.category)) {
        dynamicCategories.set(block.category, {
          kind: 'category',
          name: block.category,
          colour: block.colour || '#4c97ff',
          contents: []
        });
      }
      dynamicCategories.get(block.category).contents.push(makeBlock(block.type));
    }
  }

  return {
    kind: 'categoryToolbox',
    contents: [
      {
        kind: 'category',
        name: 'Events',
        colour: '#ffbf00',
        contents: [makeBlock('cn_event_start'), makeBlock('cn_event_loop')]
      },
      {
        kind: 'category',
        name: 'Logic',
        colour: '#59c059',
        contents: [
          makeBlock('controls_if'),
          makeBlock('logic_compare'),
          makeBlock('logic_operation'),
          makeBlock('logic_negate'),
          makeBlock('logic_boolean')
        ]
      },
      {
        kind: 'category',
        name: 'Loops',
        colour: '#ffab19',
        contents: [
          {
            kind: 'block',
            type: 'controls_repeat_ext',
            inputs: {
              TIMES: { shadow: { type: 'math_number', fields: { NUM: 10 } } }
            }
          },
          makeBlock('controls_whileUntil'),
          makeBlock('controls_flow_statements')
        ]
      },
      {
        kind: 'category',
        name: 'Math',
        colour: '#4c97ff',
        contents: [
          { kind: 'block', type: 'math_number', fields: { NUM: 0 } },
          makeBlock('math_arithmetic'),
          makeBlock('math_single'),
          makeBlock('math_round'),
          makeBlock('math_random_int')
        ]
      },
      {
        kind: 'category',
        name: 'Text',
        colour: '#9966ff',
        contents: [
          { kind: 'block', type: 'text', fields: { TEXT: 'hello' } },
          makeBlock('text_join'),
          makeBlock('text_print')
        ]
      },
      {
        kind: 'category',
        name: 'Variables',
        colour: '#ff8c1a',
        custom: 'VARIABLE'
      },
      ...Array.from(dynamicCategories.values())
    ]
  };
}

const CodyNickTheme = Blockly.Theme.defineTheme('codynickScratchLike', {
  base: Blockly.Themes.Classic,
  componentStyles: {
    workspaceBackgroundColour: '#f7fbff',
    toolboxBackgroundColour: '#ffffff',
    toolboxForegroundColour: '#334155',
    flyoutBackgroundColour: '#f8fafc',
    flyoutForegroundColour: '#334155',
    flyoutOpacity: 0.98,
    scrollbarColour: '#cbd5e1',
    scrollbarOpacity: 0.95,
    insertionMarkerColour: '#22c55e',
    insertionMarkerOpacity: 0.35,
    markerColour: '#ff6680',
    cursorColour: '#4c97ff'
  },
  fontStyle: {
    family: 'Inter, Arial, Helvetica, sans-serif',
    weight: '700',
    size: 13
  }
});


function viewPython() {
  const code = updatePythonPreview(true);
  document.getElementById('pythonPreview').textContent = code;
  document.getElementById('pythonModal').classList.add('open');
}

function closePythonModal(event) {
  if (event) {
    event.stopPropagation();
    const modal = document.querySelector('#pythonModal .modal');
    const clickedBackdrop = event.target && event.target.id === 'pythonModal';
    const clickedButton = event.target && event.target.closest('button');
    if (modal && modal.contains(event.target) && !clickedButton) return;
    if (!clickedBackdrop && !clickedButton) return;
  }
  document.getElementById('pythonModal').classList.remove('open');
}

async function copyPythonPreview(event) {
  if (event) event.stopPropagation();
  const code = document.getElementById('pythonPreview').textContent;
  await navigator.clipboard.writeText(code);
  toast('Python copied.');
}

function initBlockly() {
  ensureColourFieldSupport();
  defineEventBlocks();
  definePackageBlocks();

  workspace = Blockly.inject('blocklyDiv', {
    toolbox: buildToolbox(),
    media: '/blocks/vendor/blockly/media/',
    renderer: 'zelos',
    theme: CodyNickTheme,
    trashcan: true,
    move: {
      scrollbars: true,
      drag: true,
      wheel: true
    },
    grid: {
      spacing: 32,
      length: 3,
      colour: '#dbeafe',
      snap: true
    },
    zoom: {
      controls: true,
      wheel: true,
      startScale: 0.72,
      maxScale: 2.2,
      minScale: 0.35,
      scaleSpeed: 1.12
    }
  });

  workspace.addChangeListener((event) => {
    if (event.isUiEvent) return;
    updatePythonPreview(false);
    scheduleSave();
  });

  window.addEventListener('resize', () => Blockly.svgResize(workspace));

  if (BLOCK_WARNINGS.length) {
    toast('Some block package files were skipped: ' + BLOCK_WARNINGS.join(' | '), true);
  }
}

function indent(code, spaces = 4) {
  const pad = ' '.repeat(spaces);
  const lines = String(code || '').split('\n');
  const out = lines
    .filter(line => line.length > 0)
    .map(line => pad + line)
    .join('\n');
  return out ? out + '\n' : '';
}

function statementToCode(block, inputName) {
  const target = block.getInputTargetBlock(inputName);
  return stackToCode(target);
}

function valueToCode(block, inputName, fallback = 'None') {
  const target = block.getInputTargetBlock(inputName);
  if (!target) return fallback;
  return blockToPythonValue(target);
}

function stackToCode(block) {
  let code = '';
  let cursor = block;

  while (cursor) {
    code += blockToPythonStatement(cursor);
    cursor = cursor.getNextBlock();
  }

  return code;
}

function blockToPythonValue(block) {
  if (!block) return 'None';

  if (dynamicBlockSpecs.has(block.type)) {
    return renderDynamicBlock(block);
  }

  switch (block.type) {
    case 'math_number':
      return String(Number(block.getFieldValue('NUM') || 0));

    case 'text':
      return quotePython(block.getFieldValue('TEXT') || '');

    case 'logic_boolean':
      return block.getFieldValue('BOOL') === 'TRUE' ? 'True' : 'False';

    case 'logic_negate':
      return '(not ' + valueToCode(block, 'BOOL', 'False') + ')';

    case 'logic_operation': {
      const op = block.getFieldValue('OP') === 'AND' ? 'and' : 'or';
      return '(' + valueToCode(block, 'A', 'False') + ' ' + op + ' ' + valueToCode(block, 'B', 'False') + ')';
    }

    case 'logic_compare': {
      const opMap = { EQ: '==', NEQ: '!=', LT: '<', LTE: '<=', GT: '>', GTE: '>=' };
      const op = opMap[block.getFieldValue('OP')] || '==';
      return '(' + valueToCode(block, 'A', '0') + ' ' + op + ' ' + valueToCode(block, 'B', '0') + ')';
    }

    case 'math_arithmetic': {
      const opMap = { ADD: '+', MINUS: '-', MULTIPLY: '*', DIVIDE: '/', POWER: '**' };
      const op = opMap[block.getFieldValue('OP')] || '+';
      return '(' + valueToCode(block, 'A', '0') + ' ' + op + ' ' + valueToCode(block, 'B', '0') + ')';
    }

    case 'math_single': {
      const op = block.getFieldValue('OP');
      const n = valueToCode(block, 'NUM', '0');
      if (op === 'NEG') return '(-' + n + ')';
      if (op === 'ABS') return 'abs(' + n + ')';
      if (op === 'ROOT') return '(' + n + ' ** 0.5)';
      return n;
    }

    case 'math_round': {
      const op = block.getFieldValue('OP');
      const n = valueToCode(block, 'NUM', '0');
      if (op === 'ROUND') return 'round(' + n + ')';
      if (op === 'ROUNDUP') return '__import__("math").ceil(' + n + ')';
      if (op === 'ROUNDDOWN') return '__import__("math").floor(' + n + ')';
      return 'round(' + n + ')';
    }

    case 'math_random_int':
      return '__import__("random").randint(int(' + valueToCode(block, 'FROM', '1') + '), int(' + valueToCode(block, 'TO', '10') + '))';

    case 'variables_get':
      return variableName(block, 'VAR');

    case 'text_join': {
      const itemCount = block.itemCount_ || 2;
      const parts = [];
      for (let i = 0; i < itemCount; i++) {
        parts.push('str(' + valueToCode(block, 'ADD' + i, "''") + ')');
      }
      return '(' + parts.join(' + ') + ')';
    }

    default:
      return 'None';
  }
}

function blockToPythonStatement(block) {
  if (!block) return '';

  if (dynamicBlockSpecs.has(block.type)) {
    const spec = dynamicBlockSpecs.get(block.type);
    const expr = renderDynamicBlock(block);
    if (spec.output) {
      return expr + '\n';
    }
    return expr + '\n';
  }

  switch (block.type) {
    case 'text_print':
      return 'print(' + valueToCode(block, 'TEXT', "''") + ')\n';

    case 'variables_set':
      return variableName(block, 'VAR') + ' = ' + valueToCode(block, 'VALUE', 'None') + '\n';

    case 'controls_if': {
      let code = '';
      const ifCount = 1 + (block.elseifCount_ || 0);
      for (let i = 0; i < ifCount; i++) {
        const keyword = i === 0 ? 'if' : 'elif';
        const condition = valueToCode(block, 'IF' + i, 'False');
        const body = statementToCode(block, 'DO' + i) || 'pass\n';
        code += keyword + ' ' + condition + ':\n' + indent(body);
      }
      if (block.elseCount_) {
        const body = statementToCode(block, 'ELSE') || 'pass\n';
        code += 'else:\n' + indent(body);
      }
      return code;
    }

    case 'controls_repeat_ext': {
      const times = valueToCode(block, 'TIMES', '10');
      const body = statementToCode(block, 'DO') || 'pass\n';
      return 'for _ in range(int(' + times + ')):\n' + indent(body);
    }

    case 'controls_whileUntil': {
      const until = block.getFieldValue('MODE') === 'UNTIL';
      const cond = valueToCode(block, 'BOOL', 'False');
      const body = statementToCode(block, 'DO') || 'pass\n';
      return 'while ' + (until ? '(not ' + cond + ')' : cond) + ':\n' + indent(body);
    }

    case 'controls_flow_statements':
      return block.getFieldValue('FLOW') === 'BREAK' ? 'break\n' : 'continue\n';

    case 'cn_event_start':
    case 'cn_event_loop':
      return statementToCode(block, 'DO');

    default:
      return '# Unsupported statement block: ' + block.type + '\n';
  }
}

function renderDynamicBlock(block) {
  const spec = dynamicBlockSpecs.get(block.type);
  let code = String(spec.python || '');

  for (const arg of (spec.args || [])) {
    const raw = blockFieldValue(block, arg);
    const value = fieldPythonValue(arg, raw);
    code = code.replaceAll('{' + arg.name + '}', value);
  }

  return code;
}

function generatePython() {
  const topBlocks = workspace.getTopBlocks(true);
  const startBlocks = topBlocks.filter(b => b.type === 'cn_event_start');
  const loopBlocks = topBlocks.filter(b => b.type === 'cn_event_loop');

  let startCode = '';
  for (const b of startBlocks) {
    startCode += statementToCode(b, 'DO');
  }

  let loopCode = '';
  for (const b of loopBlocks) {
    loopCode += statementToCode(b, 'DO');
  }

  if (!startCode.trim()) startCode = 'pass\n';
  if (!loopCode.trim()) loopCode = 'time.sleep(0.05)\n';
  else loopCode += 'time.sleep(0.05)\n';

  return [
    '# Auto-generated by CodyNick Blockly IDE',
    '# Do not edit manually if you plan to regenerate it from blocks.',
    '',
    'import time',
    'from CodyNick import *',
    '',
    'cody = CN()',
    '',
    'try:',
    indent('# When CodyNick starts'),
    indent(startCode),
    indent('# Main Loop'),
    indent('while True:\n' + indent(loopCode)),
    'finally:',
    '    try:',
    '        cody.close()',
    '    except Exception:',
    '        pass',
    ''
  ].join('\n');
}

function updatePythonPreview(markFresh = true) {
  const code = generatePython();
  document.getElementById('pythonPreview').textContent = code;
  return code;
}

function currentWorkspaceJson() {
  return Blockly.serialization.workspaces.save(workspace);
}

async function postJson(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  const data = await res.json().catch(() => ({ ok: false, error: 'Invalid server response.' }));
  if (!res.ok || !data.ok) {
    throw new Error(data.error || 'Request failed.');
  }

  return data;
}

function scheduleSave() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => saveWorkspaceNow(true), 1200);
}

async function saveWorkspaceNow(silent = false) {
  try {
    setStatus('workspaceStatus', 'Saving…');
    await postJson('?api=save', { workspace: currentWorkspaceJson() });
    setStatus('workspaceStatus', 'Saved', 'ok');
    if (!silent) toast('Workspace saved on the server.');
  } catch (err) {
    setStatus('workspaceStatus', 'Save failed', 'err');
    toast(err.message, true);
  }
}

async function runProgram() {
  try {
    const python = updatePythonPreview(true);
    const data = await postJson('?api=run', {
      python,
      workspace: currentWorkspaceJson()
    });
    setStatus('workspaceStatus', 'Saved', 'ok');
    toast(data.message || 'Python generated and saved.');
  } catch (err) {
    toast(err.message, true);
  }
}

function downloadWorkspace() {
  const json = JSON.stringify(currentWorkspaceJson(), null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  a.href = url;
  a.download = 'codynick-workspace-' + timestamp + '.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  toast('Workspace downloaded.');
}

document.getElementById('importFile').addEventListener('change', async (ev) => {
  const file = ev.target.files[0];
  ev.target.value = '';
  if (!file) return;

  try {
    const text = await file.text();
    const json = JSON.parse(text);
    workspace.clear();
    Blockly.serialization.workspaces.load(json, workspace);
    updatePythonPreview(true);
    await saveWorkspaceNow(true);
    toast('Workspace uploaded and saved.');
  } catch (err) {
    toast('Could not upload JSON: ' + err.message, true);
  }
});

function newWorkspace() {
  if (!confirm('Clear the current workspace?')) return;
  workspace.clear();
  addDefaultWorkspace();
  updatePythonPreview(true);
  saveWorkspaceNow(true);
}

function addDefaultWorkspace() {
  const xmlText = `
    <xml xmlns="https://developers.google.com/blockly/xml">
      <block type="cn_event_start" x="45" y="45">
        <statement name="DO">
          <block type="cn_log">
            <field name="message">Program started</field>
          </block>
        </statement>
      </block>
      <block type="cn_event_loop" x="45" y="210">
        <statement name="DO">
          <block type="cn_led_matrix_display_text">
            <field name="text">HELLO</field>
            <field name="speed">'medium'</field>
          </block>
        </statement>
      </block>
    </xml>`;
  const xml = Blockly.utils.xml.textToDom(xmlText);
  Blockly.Xml.domToWorkspace(xml, workspace);
  workspace.zoomToFit();
  workspace.setScale(0.72);
  workspace.scrollCenter();
}

async function loadServerWorkspace() {
  try {
    const res = await fetch('?api=load');
    const data = await res.json();
    if (data.ok && data.workspace) {
      Blockly.serialization.workspaces.load(data.workspace, workspace);
      workspace.setScale(0.72);
      workspace.scrollCenter();
      setStatus('workspaceStatus', 'Loaded', 'ok');
    } else {
      addDefaultWorkspace();
      setStatus('workspaceStatus', 'New workspace', '');
      saveWorkspaceNow(true);
    }
    updatePythonPreview(true);
  } catch (err) {
    addDefaultWorkspace();
    setStatus('workspaceStatus', 'Load failed', 'err');
    updatePythonPreview(true);
    toast('Could not load saved workspace: ' + err.message, true);
  }
}

initBlockly();
loadServerWorkspace();
</script>
</body>
</html>
