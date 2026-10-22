<?php
header('Content-Type: application/json');
header('Cache-Control: no-store');
if (($_SERVER['HTTP_SEC_FETCH_SITE'] ?? '') === 'cross-site') {
    http_response_code(403); exit('{"ok":false,"error":"Local requests only"}');
}
$method = $_SERVER['REQUEST_METHOD'];
$path = $method === 'GET' ? '/state' : '/command';
if (!in_array($method, ['GET', 'POST'], true)) {
    http_response_code(405); exit('{"ok":false}');
}
$body = $method === 'POST' ? file_get_contents('php://input', false, null, 0, 4097) : '';
if (strlen($body) > 4096) { http_response_code(413); exit('{"ok":false}'); }
$context = stream_context_create(['http' => ['method' => $method, 'timeout' => 3,
    'header' => "Content-Type: application/json\r\nConnection: close\r\n",
    'content' => $body, 'ignore_errors' => true]]);
$reply = @file_get_contents('http://127.0.0.1:8092' . $path, false, $context);
if ($reply === false) {
    http_response_code(503); exit('{"ok":false,"error":"Sprite stage service is unavailable"}');
}
$data = json_decode($reply, true);
if (!is_array($data)) { http_response_code(502); exit('{"ok":false}'); }
if (empty($data['ok'])) http_response_code(400);
echo json_encode($data);
