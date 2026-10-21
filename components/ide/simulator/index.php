<?php
// CODY NICK MANAGED SIMULATOR LAUNCHER. No user-supplied redirect host.
$state = json_decode(@file_get_contents('/var/lib/codynick/application-state.json'), true);
if (!isset($state['components']['simulator'])) {
    http_response_code(410);
    exit('Simulator is not installed in the selected CodyNick release.');
}
$token = trim((string) @file_get_contents('/opt/codynick-simulator/token'));
$address = $_SERVER['SERVER_ADDR'] ?? '';
if (strlen($token) < 32 || !filter_var($address, FILTER_VALIDATE_IP)) {
    http_response_code(503);
    exit('Simulator is not ready. Check codynick-install-status.');
}
if (strpos($address, ':') !== false) $address = '[' . $address . ']';
header('Cache-Control: no-store');
header('Referrer-Policy: no-referrer');
header('Location: http://' . $address . ':8091/?token=' . rawurlencode($token), true, 302);
exit;
