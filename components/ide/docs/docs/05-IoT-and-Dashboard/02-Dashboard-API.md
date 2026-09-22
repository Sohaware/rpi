# Dashboard API

Import the installed local dashboard library:

```python
import Dashboard
```

## `configure()`

```python
Dashboard.configure(
    host="localhost",
    user="codynick",
    password="codynick",
    database="codynick",
    port=3306,
)
```

Changes the database connection used by later calls. The installed database uses the
values shown above. The function returns `None`.

> The function's source-level defaults are intended for a generic installation and do
> not match the CodyNick image. Normally, do not call `configure()` on the Pi.

## Database functions

```python
Dashboard.ensure_database()
Dashboard.ensure_table()
Dashboard.clear()
```

- `ensure_database()` creates the configured database when necessary.
- `ensure_table()` creates or upgrades the `iot_cards` table.
- `clear()` permanently removes every card from the local dashboard.
- All return `None` and can raise a database exception.

`Card()` automatically calls `ensure_table()`, so ordinary scripts need none of these
except an intentional `clear()` at startup.

## `Card()` constructor

```python
card = Dashboard.Card(
    card_type,
    title,
    color="blue",
    min_value=None,
    max_value=None,
    value=None,
    description=None,
    auto_delete=True,
)
```

| Parameter | Meaning |
| --- | --- |
| `card_type` | `led`, `gauge`, `textarea`, `info`, `button`, `switch`, `slider`, `graph`, `table`, `bar`, or `pie` |
| `title` | Heading shown on the card |
| `color` | `red`, `green`, `blue`, or `yellow` are rendered themes |
| `min_value` | Lower gauge/slider limit |
| `max_value` | Upper gauge/slider limit |
| `value` | Initial scalar, boolean, text, list, or dictionary |
| `description` | Optional text below the title |
| `auto_delete` | Delete the database row when the Python object is destroyed |

Construction immediately inserts a database row and sets `card.id` to its integer ID.
Unknown types/colors are stored but may not render usefully.

## Card attributes

`id`, `type`, `title`, `color`, `min_value`, `max_value`, `value`, `description`, and
`auto_delete` are public. Changing an attribute only changes memory until `save()`.

## Card methods

```python
exists = card.sync()
```

Reloads all card fields from the database. Returns `True` if the row exists, otherwise
`False`. Browser-written values become visible to Python after this call. Values read
from the database are strings, including `"true"` and `"false"`.

```python
card.save()
```

Writes every public card field to the database. Returns `None`. It raises
`RuntimeError` after the card has been deleted. Because it writes every field, calling
`save()` with a stale local `value` can overwrite a recent browser action.

```python
card.set(value, save=True)
```

Assigns `card.value`. With the default `save=True`, it immediately calls `save()`.
Lists and dictionaries are JSON encoded; booleans become `"true"` or `"false"`.

```python
data = card.value_json()
```

Returns an existing list/dictionary unchanged or parses a JSON string. Returns `None`
for a null value and raises `json.JSONDecodeError` for invalid JSON.

```python
card.delete()
```

Deletes the row and sets `card.id` to `None`. Repeated calls are harmless.

## Deterministic cleanup

```python
with Dashboard.Card("info", "State", value="Starting") as state:
    state.set("Running")
```

The context manager deletes the card on exit. Python destructors are not guaranteed
after a crash, power loss, or forced termination. Use `delete()` or `Dashboard.clear()`
when cleanup is important. Use `auto_delete=False` only for cards intentionally kept
after the script exits.

