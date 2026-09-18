# Simple PHP IDE — Capabilities and Configuration Guide

## Overview

This app is a lightweight, browser-based PHP IDE designed for editing Python files inside a strictly controlled working directory. It provides a simple web interface for file management, editing, uploading, downloading, and pushing editor content into a separately configured active script file.

The app is intended to be deployed on a local or private server, such as an Ubuntu/Raspberry Pi system running Apache and PHP.

## File Structure

The app is designed around two main PHP files:

```text
index.php
config.php
```

### `index.php`

Contains the full application logic, including:

- User interface
- File browser
- Editor interface
- AJAX endpoints
- File CRUD operations
- Upload/download handling
- Logs modal
- Active script update logic

### `config.php`

Contains the deployment-specific configuration, such as:

- Working directory path
- Active script file path
- Log file path
- App title
- Logo path or URL
- Upload restrictions

## Main Capabilities

## 1. Working Directory File Management

The app allows the user to manage files and folders inside the configured working directory.

Supported operations include:

- View files and folders
- Create new files
- Create new folders
- Rename files and folders
- Delete files and folders
- Edit file contents
- Save edited files
- Download files
- Upload files

The user should not be able to access files outside the configured working directory through normal app operations.

## 2. Strict Path Sandboxing

All server-side file operations are intended to be restricted to the configured working directory.

This means the app checks file paths on the server side before performing actions such as:

- Opening files
- Saving files
- Renaming files
- Deleting files
- Moving files
- Downloading files
- Uploading files

This is important because browser-side restrictions alone are not secure.

## 3. Active Script Handling

The app supports a separately configured active script file.

The active script is defined in `config.php` and is treated differently from normal editable files.

Active script behavior:

- Displayed in the file list with a green filename
- Displayed as read-only
- Cannot be renamed
- Cannot be deleted
- Cannot be moved using drag-and-drop
- Can be downloaded
- Can be updated only through the **Run this File** button

## 4. “Run this File” Button

The **Run this File** button copies the current editor contents into the configured active script file.

Typical use case:

1. The user edits a Python file in the working directory.
2. The user clicks **Run this File**.
3. The contents of the currently open editor file are written into the active script file.
4. A separate background service can detect the active script change and restart/run it.

The app itself does not necessarily execute the Python file directly. It prepares or updates the active script file.

## 5. Code Editor

The app uses a browser-based code editor interface suitable for Python editing.

Expected editor features include:

- Dark theme
- Python syntax highlighting
- Editable code area for normal files
- Read-only mode for the active script
- Save button for editable files

## 6. Dark-Themed Interface

The app uses a dark visual theme suitable for coding environments.

Typical interface sections:

- Header bar with logo/title
- Left file browser/sidebar
- Main editor area
- Action buttons
- Notification/toast area
- Logs modal

## 7. Icon-Based Buttons

Toolbar and action buttons use icon-style controls instead of text labels.

The icons are implemented without external CDNs, so the app can work in local/offline environments.

Recommended behavior:

- Use inline SVG icons
- Include `title` attributes for tooltips
- Include `aria-label` attributes for accessibility

## 8. Toast Notifications

The app provides visual feedback after actions such as:

- Save
- Delete
- Rename
- Create file
- Create folder
- Upload
- Download preparation
- Move file
- Run this file

Notifications should appear temporarily and disappear automatically.

The app should not use JavaScript alert boxes for normal feedback.

## 9. Collapsible Folder Tree

The left sidebar supports a folder tree view.

Capabilities:

- Show nested folders
- Expand folders
- Collapse folders
- Display files inside folders
- Keep navigation compact

This makes the app usable for projects with multiple files and folders.

## 10. Drag-and-Drop File Moving

The app supports moving files between folders using drag-and-drop.

Expected behavior:

- Drag a file from the file tree
- Drop it onto a folder to move it there
- Drop it onto the root/sidebar area to move it back to the working directory root
- Prevent moving the active script
- Prevent moving files outside the configured working directory

The move operation must be validated on the server side.

## 11. Upload Feature

The app supports file upload into the working directory.

Current intended restriction:

- Only `.py` files are allowed for upload

This prevents accidental upload of unrelated file types.

Recommended upload checks:

- Check file extension
- Check destination path
- Prevent overwriting protected files unless explicitly allowed
- Enforce maximum upload size if configured

## 12. Download Feature

The app supports downloading files from the working directory.

It also supports downloading the configured active script file.

Download behavior:

- Normal files can be downloaded from the file browser
- The active script can also be downloaded
- Server-side path checks should be applied before sending files

## 13. Logs Popup

The app includes a **Logs** button beside the **Run this File** button.

When clicked, it opens a popup/modal that displays the contents of the configured log file.

Log modal behavior:

- Opens without leaving the IDE page
- Reads the log file from the path configured in `config.php`
- Refreshes automatically every 10 seconds
- Can be closed by the user

The log file may be outside the working directory because it is explicitly configured separately.

## Configuration

Configuration is stored in `config.php`.

A typical configuration may look like this:

```php
<?php

define('WORKING_DIR', '/home/client/ide_workspace');
define('ACTIVE_SCRIPT_FILE', '/home/client/active_script.py');
define('LOG_FILE', '/home/client/script.log');

define('IDE_TITLE', 'CodyNick Simple IDE');
define('IDE_LOGO_URL', '');

define('MAX_UPLOAD_SIZE', 2 * 1024 * 1024); // 2 MB
```

## Configuration Options

### `WORKING_DIR`

Defines the root directory that the user can manage through the IDE.

Example:

```php
define('WORKING_DIR', '/home/client/ide_workspace');
```

The user should be able to CRUD files and folders only inside this directory.

### `ACTIVE_SCRIPT_FILE`

Defines the file that receives the contents of the editor when the user clicks **Run this File**.

Example:

```php
define('ACTIVE_SCRIPT_FILE', '/home/client/active_script.py');
```

This file is shown as read-only in the IDE and should be visually highlighted in green.

### `LOG_FILE`

Defines the log file displayed in the Logs popup.

Example:

```php
define('LOG_FILE', '/home/client/script.log');
```

This file does not need to be inside the working directory, but Apache/PHP must be able to read it.

### `IDE_TITLE`

Defines the title displayed in the IDE header.

Example:

```php
define('IDE_TITLE', 'CodyNick Simple IDE');
```

### `IDE_LOGO_URL`

Defines the logo shown in the header.

Example:

```php
define('IDE_LOGO_URL', '/assets/logo.png');
```

If left empty, the app may display only the title or a placeholder.

### `MAX_UPLOAD_SIZE`

Defines the maximum upload size.

Example:

```php
define('MAX_UPLOAD_SIZE', 2 * 1024 * 1024); // 2 MB
```

## Required Server Permissions

Apache/PHP must have the required permissions for the configured files and folders.

The web server user, commonly `www-data` on Ubuntu, needs:

- Read access to `index.php` and `config.php`
- Read/write access to `WORKING_DIR`
- Read/write access to `ACTIVE_SCRIPT_FILE`
- Read access to `LOG_FILE`

For local controlled systems, permissions may be relaxed as needed. For production or internet-facing systems, permissions should be tightened carefully.

## Example Ubuntu Permission Commands

Example only:

```bash
sudo chown -R www-data:www-data /home/client/ide_workspace
sudo chmod -R 775 /home/client/ide_workspace

sudo chown www-data:www-data /home/client/active_script.py
sudo chmod 664 /home/client/active_script.py

sudo chmod 644 /home/client/script.log
```

If another service also writes to the active script or log file, group permissions may need adjustment.

## Security Notes

This app is intended for controlled/local/private environments unless additional authentication and hardening are added.

Recommended security practices:

- Do not expose the IDE publicly without authentication
- Keep `config.php` outside public editing access
- Ensure all server actions validate paths
- Disable PHP execution inside the working directory if possible
- Limit upload types to `.py`
- Set a reasonable upload size limit
- Run Apache/PHP with minimal privileges
- Avoid giving the web server unnecessary access to system files

## Suggested Apache Hardening

If the working directory is served by Apache, prevent PHP execution in that folder unless explicitly needed.

Example `.htaccess` idea:

```apache
php_flag engine off
Options -Indexes
```

Actual availability depends on Apache/PHP configuration.

## Typical Workflow

1. Open the IDE in a browser.
2. Create or upload a `.py` file.
3. Edit the file in the browser editor.
4. Save the file.
5. Click **Run this File** to copy the editor contents into the active script.
6. A background watcher/service detects the active script change and restarts the target Python service.
7. Click **Logs** to view the latest output from the configured log file.

## Limitations

Current intended limitations:

- Upload is restricted to `.py` files.
- The app does not directly manage Linux services unless connected to an external watcher/service.
- The active script is updated by copying editor contents, not by executing shell commands.
- Authentication is not described as part of the core two-file setup.
- Multi-user editing/conflict handling is not included.

## Recommended Future Enhancements

Possible future improvements:

- Add password login
- Add user/session timeout
- Add file search
- Add recent files list
- Add backup before overwrite
- Add syntax checking before running
- Add service status indicator
- Add read-only/demo mode
- Add configurable allowed file extensions
- Add configurable hidden/protected file patterns

## Summary

This IDE provides a compact browser-based environment for editing Python project files in a controlled folder, updating a protected active script, and viewing logs. It is especially suitable for local Raspberry Pi or Ubuntu deployments where students or users need a simple browser-based coding interface without full server access.
