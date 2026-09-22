# CodyNick Blockly PHP IDE

Blockly is bundled under `vendor/blockly`, so the editor works while the Raspberry Pi
hotspot has no internet connection.

This package contains:

- `index.php` — the full-screen Blockly-based IDE and server API in one PHP file.
- `blocks/codynick_core.json` — the default drop-in block package for CodyNick.py (not included; expected in the runtime location) functions.

## Install

Copy the folder to your PHP web directory, for example:

```bash
sudo cp -r codynick_php_blockly_ide /var/www/html/codynick-ide
sudo chown -R www-data:www-data /var/www/html/codynick-ide
```

Make sure the web server can write to the IDE folder because it saves:

- `main.json`
- the configured Python output file, by default `active_script.py`

## Configure output file

At the top of `index.php`, edit:

```php
$PYTHON_OUTPUT_FILE = __DIR__ . '/active_script.py';
```

For example:

```php
$PYTHON_OUTPUT_FILE = '/home/client/active_script.py';
```

## Add more blocks

Drop another JSON package into:

```text
blocks/
```

The IDE loads all `*.json` files in this folder.

## Notes

The browser loads Blockly from a CDN. For a fully offline deployment, download Blockly locally and replace the script URLs in `index.php`.


## Revised UI notes

- Workspace JSON actions are labeled **Upload** and **Download**.
- The interface uses a flatter GitHub/Tailwind-like button style.
- Python preview is hidden by default and opens with **View Python**.
- `CodyNick.py` is intentionally not bundled. The generated Python uses `from CodyNick import *`, so the runtime environment must already include the CodyNick library.
- Color blocks use Blockly's color field when available, with a palette fallback if the bundled Blockly build does not register the color picker.


## Workspace save location

The IDE now saves the hidden server-side workspace file here:

```text
data/main.json
```

The user does not see this file name in the interface.

If the Save API returns a permission error, make the `data/` folder writable by the web server. Example:

```bash
sudo chown -R www-data:www-data /path/to/codynick_php_blockly_ide/data
sudo chmod -R 775 /path/to/codynick_php_blockly_ide/data
```

On some systems the web-server user may be `apache`, `nginx`, or another account instead of `www-data`.

## Creating new blocks

See:

```text
BLOCK_PACKAGE_GUIDE.md
```


## Empty new projects

New projects now start with an empty Blockly workspace. The IDE no longer inserts sample event blocks automatically.
