<?php
/* ============================================================
   SIMPLE PHP IOT PANEL - API + DATABASE HELPERS
   ============================================================ */

require_once __DIR__ . '/config.php';

function json_response($payload, int $status = 200): void {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function db(): PDO {
    global $db_host, $db_name, $db_user, $db_pass;

    static $pdo = null;

    if ($pdo instanceof PDO) {
        return $pdo;
    }

    try {
        $pdo = new PDO(
            "mysql:host={$db_host};dbname={$db_name};charset=utf8mb4",
            $db_user,
            $db_pass,
            [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ]
        );
    } catch (Throwable $e) {
        json_response([
            'ok' => false,
            'error' => 'Database connection failed',
            'detail' => $e->getMessage(),
        ], 500);
    }

    ensure_schema($pdo);
    return $pdo;
}

function table_exists(PDO $pdo, string $table): bool {
    $stmt = $pdo->prepare("SHOW TABLES LIKE :table_name");
    $stmt->execute([':table_name' => $table]);
    return (bool)$stmt->fetchColumn();
}

function column_exists(PDO $pdo, string $table, string $column): bool {
    $stmt = $pdo->prepare("SHOW COLUMNS FROM `{$table}` LIKE :column_name");
    $stmt->execute([':column_name' => $column]);
    return (bool)$stmt->fetchColumn();
}

function ensure_schema(PDO $pdo): void {
    global $cards_table;

    // Create the cards table automatically if it does not exist.
    if (!table_exists($pdo, $cards_table)) {
        $pdo->exec("CREATE TABLE `{$cards_table}` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `type` VARCHAR(50) NOT NULL,
            `title` VARCHAR(100) NOT NULL,
            `color` VARCHAR(20) DEFAULT 'blue',
            `min_value` FLOAT DEFAULT 0,
            `max_value` FLOAT DEFAULT 100,
            `value` TEXT DEFAULT NULL,
            `description` TEXT DEFAULT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
        return;
    }

    // Lightweight migrations for older versions of this app.
    if (!column_exists($pdo, $cards_table, 'min_value')) {
        $pdo->exec("ALTER TABLE `{$cards_table}` ADD COLUMN `min_value` FLOAT DEFAULT 0 AFTER `color`");
    }

    if (!column_exists($pdo, $cards_table, 'max_value')) {
        $pdo->exec("ALTER TABLE `{$cards_table}` ADD COLUMN `max_value` FLOAT DEFAULT 100 AFTER `min_value`");
    }

    if (!column_exists($pdo, $cards_table, 'description')) {
        $pdo->exec("ALTER TABLE `{$cards_table}` ADD COLUMN `description` TEXT DEFAULT NULL AFTER `value`");
    }

    // If the old table used ENUM color values, convert to VARCHAR so yellow and future colors work.
    try {
        $pdo->exec("ALTER TABLE `{$cards_table}` MODIFY COLUMN `color` VARCHAR(20) DEFAULT 'blue'");
    } catch (Throwable $e) {
        // Ignore if the database engine/version does not need or allow this conversion.
    }
}


function is_list_array(array $array): bool {
    if (function_exists('array_is_list')) {
        return array_is_list($array);
    }

    $expected = 0;
    foreach ($array as $key => $_) {
        if ($key !== $expected++) {
            return false;
        }
    }
    return true;
}

function normalize_type(?string $type): string {
    $type = strtolower(trim((string)$type));
    return $type === 'guage' ? 'gauge' : $type;
}

function normalize_color(?string $color): string {
    $color = strtolower(trim((string)$color));
    $allowed = ['red', 'green', 'blue', 'yellow'];
    return in_array($color, $allowed, true) ? $color : 'blue';
}

function validate_card(array $card): array {
    $valid_types = ['led', 'gauge', 'textarea', 'info', 'button', 'switch', 'slider', 'graph', 'table', 'bar', 'pie'];
    $type = normalize_type($card['type'] ?? '');
    $errors = [];

    if (!in_array($type, $valid_types, true)) {
        $errors[] = "Unknown card type: " . ($card['type'] ?? '');
    }

    if (trim((string)($card['title'] ?? '')) === '') {
        $errors[] = "Missing title";
    }

    if (in_array($type, ['gauge', 'slider'], true)) {
        // min_value and max_value are optional for range-based cards.
        // Missing or non-numeric values default to 0 and 100 in the frontend.
        $min = is_numeric($card['min_value'] ?? null) ? (float)$card['min_value'] : 0.0;
        $max = is_numeric($card['max_value'] ?? null) ? (float)$card['max_value'] : 100.0;

        if ($max <= $min) {
            $errors[] = "max_value must be greater than min_value";
        }
    }

    if ($type === 'graph') {
        $raw = trim((string)($card['value'] ?? ''));
        $decoded = json_decode($raw, true);

        if ($raw === '' || !is_array($decoded)) {
            $errors[] = "Graph value must be JSON: either one numeric series or a nested object of named numeric series";
        } else {
            $isNested = false;
            foreach ($decoded as $k => $v) {
                if (!is_numeric($k) && is_array($v)) {
                    $isNested = true;
                    break;
                }
            }

            if ($isNested) {
                foreach ($decoded as $seriesName => $seriesData) {
                    if (!is_array($seriesData)) {
                        $errors[] = "Nested graph series must be arrays or objects";
                        break;
                    }
                    foreach ($seriesData as $k => $v) {
                        if (is_array($v)) {
                            $x = $v['x'] ?? ($v[0] ?? null);
                            $y = $v['y'] ?? ($v[1] ?? null);
                            if (!is_numeric($x) || !is_numeric($y)) {
                                $errors[] = "Nested graph point arrays require numeric x/y values";
                                break 2;
                            }
                        } elseif (!is_numeric($k) || !is_numeric($v)) {
                            $errors[] = "Nested graph keys and values must be numeric";
                            break 2;
                        }
                    }
                }
            } else {
                foreach ($decoded as $k => $v) {
                    if (is_array($v)) {
                        $x = $v['x'] ?? ($v[0] ?? null);
                        $y = $v['y'] ?? ($v[1] ?? null);
                        if (!is_numeric($x) || !is_numeric($y)) {
                            $errors[] = "Graph point arrays require numeric x/y values";
                            break;
                        }
                    } elseif (!is_numeric($k) || !is_numeric($v)) {
                        $errors[] = "Graph keys and values must both be numeric";
                        break;
                    }
                }
            }
        }
    }

    if ($type === 'table') {
        $raw = trim((string)($card['value'] ?? ''));
        $decoded = json_decode($raw, true);

        if ($raw === '' || !is_array($decoded)) {
            $errors[] = "Table value must be a JSON object or array";
        }
    }

    if (in_array($type, ['bar', 'pie'], true)) {
        $raw = trim((string)($card['value'] ?? ''));
        $decoded = json_decode($raw, true);

        if ($raw === '' || !is_array($decoded)) {
            $errors[] = ucfirst($type) . " chart value must be a JSON object or array";
        } else {
            $items = [];

            if (is_list_array($decoded)) {
                foreach ($decoded as $index => $item) {
                    if (is_array($item) && is_list_array($item) && count($item) >= 2) {
                        $items[] = $item[1];
                    } elseif (is_array($item) && (array_key_exists('value', $item) || array_key_exists('y', $item))) {
                        $items[] = $item['value'] ?? $item['y'];
                    } else {
                        $items[] = $item;
                    }
                }
            } else {
                foreach ($decoded as $value) {
                    $items[] = $value;
                }
            }

            foreach ($items as $value) {
                if (!is_numeric($value)) {
                    $errors[] = ucfirst($type) . " chart values must be numeric";
                    break;
                }
            }
        }
    }

    return [
        'valid' => count($errors) === 0,
        'errors' => $errors,
    ];
}

function get_cards(): array {
    global $cards_table;
    $pdo = db();

    $stmt = $pdo->query("SELECT id, type, title, color, min_value, max_value, value, description FROM `{$cards_table}` ORDER BY id ASC");
    $cards = $stmt->fetchAll();

    foreach ($cards as &$card) {
        $validation = validate_card($card);
        $card['type'] = normalize_type($card['type']);
        $card['color'] = normalize_color($card['color']);
        $card['valid'] = $validation['valid'];
        $card['errors'] = $validation['errors'];
    }

    return $cards;
}

function set_card_value(int $id, string $value): void {
    global $cards_table;
    $pdo = db();

    $stmt = $pdo->prepare("UPDATE `{$cards_table}` SET `value` = :value WHERE `id` = :id");
    $stmt->execute([
        ':value' => $value,
        ':id' => $id,
    ]);
}

$action = $_GET['action'] ?? '';

if ($action === 'state') {
    try {
        json_response([
            'ok' => true,
            'cards' => get_cards(),
        ]);
    } catch (Throwable $e) {
        json_response([
            'ok' => false,
            'error' => 'Unable to load cards',
            'detail' => $e->getMessage(),
        ], 500);
    }
}

if ($action === 'set') {
    try {
        $id = (int)($_POST['id'] ?? 0);
        $value = (string)($_POST['value'] ?? '');

        if ($id <= 0) {
            json_response(['ok' => false, 'error' => 'Invalid card ID'], 400);
        }

        set_card_value($id, $value);
        json_response(['ok' => true]);
    } catch (Throwable $e) {
        json_response([
            'ok' => false,
            'error' => 'Unable to update card',
            'detail' => $e->getMessage(),
        ], 500);
    }
}

json_response(['ok' => false, 'error' => 'Unknown API action'], 404);
