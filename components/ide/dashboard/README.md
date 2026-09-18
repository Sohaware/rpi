# Simple PHP IoT Panel

A small on-device PHP/MySQL dashboard for local IoT panels.

The dashboard is rendered entirely through AJAX. This means changes to card type, title, color, description, min/max values, and current value are all reflected in the browser on the next refresh cycle.

## Files

```text
config.php   Database and dashboard settings
cards.php    AJAX API and database/schema helper logic
index.php    Main dashboard page
README.md    This file
```

## Installation

1. Copy all files to your PHP web directory.
2. Create a MySQL database, for example:

```sql
CREATE DATABASE iot_dashboard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Edit `config.php` and set your database credentials.
4. Open `index.php` in a browser.

The app automatically creates the `iot_cards` table if it does not already exist.

If you are upgrading from the earlier version, it also tries to add missing columns such as `min_value` and `description` automatically.

## Table Structure

The app creates this table automatically:

```sql
CREATE TABLE iot_cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(100) NOT NULL,
    color VARCHAR(20) DEFAULT 'blue',
    min_value FLOAT DEFAULT 0,
    max_value FLOAT DEFAULT 100,
    value TEXT DEFAULT NULL,
    description TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Cards are displayed in this order:

```sql
ORDER BY id ASC
```

So the display order is the database insertion order unless you manually change IDs or later add a custom order column.

## Supported Card Types

| Card type | Requirements | Accepted `value` | Notes |
|---|---|---|---|
| `led` | `title`; optional `color` | ON values: `ON`, `true`, `1`, `yes`; anything else is OFF | Read-only indicator. |
| `gauge` | `title`, numeric `value`; optional `min_value`, `max_value` | Any numeric value | If `min_value`/`max_value` are omitted or invalid, dashboard uses `0` and `100`. |
| `textarea` | `title` | Any text | Editable. User edits are pushed to DB and protected from refresh overwrites while editing. |
| `info` | `title` | Any text | Read-only textarea-style information card. |
| `button` | `title` | Usually `false` or `true` | Clicking writes `true`; button is disabled while value remains `true`. Backend should reset to `false`. |
| `switch` | `title` | ON values: `ON`, `true`, `1`, `yes`; OFF values commonly `false`, `0`, `OFF`, `no` | Rocker switch. Clicking toggles `true`/`false`; it does not become disabled. |
| `slider` | `title`, numeric `value`; optional `min_value`, `max_value` | Any numeric value in range | If `min_value`/`max_value` are omitted or invalid, dashboard uses `0` and `100`. |
| `graph` | `title`; JSON `value` | Single graph: `{"1":21,"2":24}` or `[21,24]`; multi-graph: `{"Temp":{"1":21},"Hum":{"1":55}}` | Multi-graph nested JSON is drawn in one view with generated colors and a legend. |
| `bar` | `title`; JSON `value` with numeric values | `{"A":12}`, `[["A",12]]`, or `[{"key":"A","value":12}]` | Bars are blue. |
| `pie` | `title`; JSON `value` with positive numeric values | `{"A":60,"B":40}`, `[["A",60]]`, or `[{"key":"A","value":60}]` | Slices use generated colors. |
| `table` | `title`; JSON `value` | Any JSON object, array, key/value pairs, or row objects | Values can be text, numbers, booleans, or nested JSON. |

### 1. LED

Type:

```text
led
```

Accepted ON values:

```text
ON, true, 1, yes
```

Example:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('led', 'LED 0', 'red', 'ON', 'Main status LED');
```

### 2. Gauge

Type:

```text
gauge
```

Requires:

```text
value
```

`min_value` and `max_value` are optional. The dashboard uses `0` and `100` when they are omitted.

Example:

```sql
INSERT INTO iot_cards (type, title, color, min_value, max_value, value, description)
VALUES ('gauge', 'Temperature', 'green', 0, 100, '37', 'Current sensor temperature');
```

### 3. Textarea

Type:

```text
textarea
```

This is editable. The browser saves the value using AJAX while the user types. While the user is actively editing, the browser treats the user's text as the source of truth: AJAX refreshes do not overwrite the textarea, and the current browser value is pushed back to the database to avoid conflicts with backend/device updates.

Example:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('textarea', 'Message', 'blue', 'Hello device', 'Editable command/message area');
```

### 4. Info

Type:

```text
info
```

This is a read-only version of `textarea`.

Example:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('info', 'System Info', 'yellow', 'Firmware v1.0\nMode: AUTO', 'Read-only information card');
```

### 5. Button

Type:

```text
button
```

The button text is the card title.

When pressed, the card value becomes:

```text
true
```

If the current value is `true`, the button is disabled. Resetting it to `false` should be handled by your backend/device logic.

Example:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('button', 'Start Motor', 'red', 'false', 'Sends a one-shot start command');
```

### 6. Switch

Type:

```text
switch
```

The switch behaves like a rocker/toggle version of the button. It writes `true` or `false` to the database, but it does **not** become disabled when activated.

Accepted ON values:

```text
ON, true, 1, yes
```

Example:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('switch', 'Fan Mode', 'blue', 'false', 'Toggle fan mode');
```

### 7. Slider

Type:

```text
slider
```

Requires:

```text
value
```

`min_value` and `max_value` are optional. The dashboard uses `0` and `100` when they are omitted.

Example:

```sql
INSERT INTO iot_cards (type, title, color, min_value, max_value, value, description)
VALUES ('slider', 'Brightness', 'blue', 0, 255, '120', 'LED brightness control');
```

### 8. Graph

Type:

```text
graph
```

The `value` field must contain JSON. It may be either a single graph series or nested JSON containing multiple named graph series.

The graph is displayed in the ordered sequence of the numeric keys. For nested JSON, all series are displayed in one view with generated colors and a legend showing the nested graph keys.

Example using a JSON object:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('graph', 'Temperature History', 'green', '{"1":21,"2":24,"3":23,"4":27}', 'Simple line graph');
```

The browser sorts points by key numerically before drawing them.

Example using nested JSON for multiple graph lines:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('graph', 'Environment History', 'green', '{"Temperature":{"1":21,"2":24,"3":23},"Humidity":{"1":45,"2":48,"3":46}}', 'Multiple line graph');
```

### 9. Bar Chart

Type:

```text
bar
```

The `value` field must contain JSON. The accepted input formats match the table-style key/value format while requiring numeric values.

Accepted examples:

```json
{"Red":12,"Green":8,"Blue":15}
```

```json
[["Red",12],["Green",8],["Blue",15]]
```

```json
[{"key":"Red","value":12},{"key":"Green","value":8}]
```

Example:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('bar', 'Color Counts', 'blue', '{"Red":12,"Green":8,"Blue":15}', 'Simple bar chart');
```

### 10. Pie Chart

Type:

```text
pie
```

The `value` field uses the same JSON formats as the bar chart. Values must be numeric, and positive values are shown as pie slices.

Example:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('pie', 'Mode Share', 'green', '{"Auto":60,"Manual":25,"Idle":15}', 'Simple pie chart');
```

### 11. Table

Type:

```text
table
```

The `value` field must contain JSON. Unlike the graph card, table keys and values can be non-numerical. The card displays a scrollable two-column table.

Example using a JSON object:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('table', 'Device Status', 'yellow', '{"LED0":"ON","Mode":"AUTO","IP":"192.168.1.50"}', 'Scrollable key/value table');
```

Example using an array of key/value pairs, which is useful when you need strict row order:

```sql
INSERT INTO iot_cards (type, title, color, value, description)
VALUES ('table', 'Ordered Values', 'blue', '[["First","A"],["Second","B"],["Third","C"]]', 'Rows shown in array order');
```

## Colors

Supported colors:

```text
red
green
blue
yellow
```

Invalid colors fall back to `blue`.

## Updating Card Values from Backend Code

Your Python, PHP, or device bridge can update a card by writing to the `value` column.

Example:

```sql
UPDATE iot_cards SET value = 'ON' WHERE title = 'LED 0';
UPDATE iot_cards SET value = '78' WHERE title = 'Battery';
UPDATE iot_cards SET value = 'false' WHERE title = 'Start Motor';
UPDATE iot_cards SET value = 'true' WHERE title = 'Fan Mode';
UPDATE iot_cards SET value = '{"1":10,"2":20,"3":15}' WHERE title = 'Temperature History';
UPDATE iot_cards SET value = '{"Temperature":{"1":21,"2":24},"Humidity":{"1":45,"2":48}}' WHERE title = 'Environment History';
UPDATE iot_cards SET value = '{"Auto":60,"Manual":25,"Idle":15}' WHERE title = 'Mode Share';
UPDATE iot_cards SET value = '{"LED0":"ON","Mode":"AUTO"}' WHERE title = 'Device Status';
```

The dashboard refreshes every 2 seconds by default. Refreshes preserve the page scroll position and keep chart canvas aspect ratios fixed.

You can change this in `config.php`:

```php
$poll_interval_ms = 2000;
```

## Invalid Cards

The app validates cards before sending them to the frontend.

Invalid cards do not crash the dashboard. They are shown as red error cards.

Examples of invalid cards:

- Unknown `type`
- Missing title
- Graph with invalid JSON
- Graph with non-numeric keys/values or invalid nested graph series
- Table with invalid JSON
- Bar/pie chart with invalid JSON or non-numeric values

## Adding New Card Types

To add a new card type:

1. Add the type name to `$valid_types` in `cards.php`.
2. Add validation rules in `validate_card()` if needed.
3. Add a new rendering block in `renderCardBody()` in `index.php`.
4. Add live update behavior in `updateCardValues()` in `index.php`.
5. Add drawing/parsing helpers if the card renders a canvas-based visualization.
6. Add event handling in `attachEvents()` if the card sends values back to the server.

This structure keeps the backend and frontend simple while allowing future expansion.
