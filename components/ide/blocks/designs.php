<?php
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
function design_reply(array $data, int $status = 200): void {
    http_response_code($status); echo json_encode($data, JSON_UNESCAPED_UNICODE); exit;
}
if (($_SERVER['HTTP_SEC_FETCH_SITE'] ?? '') === 'cross-site') design_reply(['ok'=>false,'error'=>'Local requests only.'],403);
$directory = __DIR__ . '/data/designs';
if (is_link($directory)) design_reply(['ok'=>false,'error'=>'Invalid design directory.'],500);
if (!is_dir($directory) && !@mkdir($directory,0750,true)) design_reply(['ok'=>false,'error'=>'Cannot create design directory.'],500);
$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';
if ($method === 'GET' && $action === 'list') {
    $items = [];
    foreach (array_slice(glob($directory . '/*.json') ?: [],0,500) as $path) {
        if (is_link($path)) continue;
        $data = json_decode(@file_get_contents($path),true);
        if (is_array($data) && is_string($data['name'] ?? null)) $items[]=['name'=>$data['name'],'updated_at'=>$data['updated_at'] ?? ''];
    }
    usort($items,fn($a,$b)=>strnatcasecmp($a['name'],$b['name']));
    design_reply(['ok'=>true,'designs'=>$items]);
}
$request = [];
if ($method === 'POST' && in_array($action,['save','delete'],true)) {
    if (strpos($_SERVER['CONTENT_TYPE'] ?? '', 'application/json') !== 0) design_reply(['ok'=>false,'error'=>'JSON required.'],415);
    $raw = file_get_contents('php://input',false,null,0,2097153);
    if ($raw === false || strlen($raw)>2097152) design_reply(['ok'=>false,'error'=>'Design is too large.'],413);
    $request = json_decode($raw,true);
    if (!is_array($request)) design_reply(['ok'=>false,'error'=>'Invalid JSON.'],400);
} elseif ($method !== 'GET' || $action !== 'load') {
    design_reply(['ok'=>false,'error'=>'Unsupported request.'],405);
}
$name = $method === 'GET' ? ($_GET['name'] ?? '') : ($request['name'] ?? '');
if (!is_string($name)) design_reply(['ok'=>false,'error'=>'Invalid design name.'],400);
$name = trim($name);
if ($name === '' || strlen($name)>120 || !preg_match('//u',$name) || preg_match('~[\x00-\x1f\x7f/\\\\]~',$name)) {
    design_reply(['ok'=>false,'error'=>'Use a name of 1-120 bytes without slashes or control characters.'],400);
}
$path = $directory . '/' . hash('sha256',$name) . '.json';
if (is_link($path)) design_reply(['ok'=>false,'error'=>'Invalid design path.'],400);
if ($method === 'GET') {
    $saved = json_decode(@file_get_contents($path),true);
    if (!is_array($saved) || !is_array($saved['workspace'] ?? null)) design_reply(['ok'=>false,'error'=>'Design not found.'],404);
    design_reply(['ok'=>true,'name'=>$saved['name'],'workspace'=>$saved['workspace']]);
}
if ($action === 'save' && !is_array($request['workspace'] ?? null)) design_reply(['ok'=>false,'error'=>'Workspace required.'],400);
$lock = @fopen($directory . '/.save.lock','c');
if (!$lock || !flock($lock,LOCK_EX)) design_reply(['ok'=>false,'error'=>'Cannot lock designs.'],500);
if ($action === 'delete') {
    if (($request['confirmed'] ?? false) !== true) design_reply(['ok'=>false,'error'=>'Delete confirmation required.'],400);
    if (!is_file($path)) design_reply(['ok'=>false,'error'=>'Design not found.'],404);
    if (!unlink($path)) design_reply(['ok'=>false,'error'=>'Could not delete design.'],500);
    flock($lock,LOCK_UN); fclose($lock);
    design_reply(['ok'=>true,'name'=>$name]);
}
if (is_file($path) && ($request['overwrite'] ?? false) !== true) design_reply(['ok'=>false,'exists'=>true,'error'=>'A design with this name already exists.'],409);
if (!is_file($path) && count(glob($directory . '/*.json') ?: [])>=500) design_reply(['ok'=>false,'error'=>'Design limit reached.'],400);
$saved = ['name'=>$name,'workspace'=>$request['workspace'],'updated_at'=>gmdate('c')];
$json = json_encode($saved,JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT);
$temporary = tempnam($directory,'.design-');
if ($json === false || $temporary === false || file_put_contents($temporary,$json,LOCK_EX)!==strlen($json)) {
    if (is_string($temporary)) @unlink($temporary);
    design_reply(['ok'=>false,'error'=>'Could not save design.'],500);
}
chmod($temporary,0640);
if (!rename($temporary,$path)) { @unlink($temporary); design_reply(['ok'=>false,'error'=>'Could not replace design.'],500); }
flock($lock,LOCK_UN); fclose($lock);
design_reply(['ok'=>true,'name'=>$name,'updated_at'=>$saved['updated_at']]);
