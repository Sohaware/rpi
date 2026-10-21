<?php
// CODY NICK MANAGED SIMULATOR LAUNCHER. Retain the browser's validated local host.
$state = json_decode(@file_get_contents('/var/lib/codynick/application-state.json'), true);
if (!isset($state['components']['simulator'])) {
    http_response_code(410);
    exit('Simulator is not installed in the selected CodyNick release.');
}
$token = trim((string) @file_get_contents('/opt/codynick-simulator/token'));
$host = parse_url('http://' . ($_SERVER['HTTP_HOST'] ?? ''), PHP_URL_HOST);
$address = trim((string) $host, '[]');
$validHost = filter_var($address, FILTER_VALIDATE_IP)
    || (strlen($address) <= 253 && preg_match('/\A[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\z/D', $address));
if (strlen($token) < 32 || !$validHost) {
    http_response_code(503);
    exit('Simulator is not ready. Check codynick-install-status.');
}
if (strpos($address, ':') !== false) $address = '[' . $address . ']';
header('Cache-Control: no-store');
header('Referrer-Policy: no-referrer');
header('Location: http://' . $address . ':8091/?token=' . rawurlencode($token), true, 302);
exit;
