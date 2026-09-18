# Simple PHP Documentation App

A lightweight Docusaurus-style documentation application using Parsedown.

## Structure

```text
index.php
config.php
vendor/parsedown/Parsedown.php
docs/
  Category/
    Page.md
```

## Features

- Folder-based categories
- Markdown pages rendered with Parsedown
- Auto-generated sidebar
- Server-side full-text search
- Responsive professional UI
- No database required
- Safe page loading to prevent path traversal

## Installation

1. Upload this folder to your PHP server.
2. Edit `config.php`.
3. Add your `.md` files to the `docs` folder.
4. Open `index.php` in your browser.

## Notes

- Use a first-level Markdown heading (`# Page Title`) to set the sidebar title.
- Folder and file names are sorted naturally.
- Numeric prefixes such as `01-Introduction.md` are hidden from category display names but kept in page paths.


## Logo

To use a logo, place your image in the app folder, for example:

```text
/assets/logo.png
```

Then update `config.php`:

```php
'logo_path' => '/assets/logo.png',
```

If `logo_path` is empty, the app shows the configured text badge instead.

## Code Block Copy Buttons

All Markdown code blocks automatically receive a copy button in the browser. No extra Markdown syntax is required.
