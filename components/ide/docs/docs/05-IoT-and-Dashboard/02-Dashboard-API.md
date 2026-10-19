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
    font_size=None,
    font_name=None,
    horizontal_alignment=None,
    vertical_alignment=None,
    column_span=1,
    height_multiplier=1,
    y_padding_percent=0,
    x_axis_label=None,
    y_axis_label=None,
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
| `font_size` | Optional widget text size from `12` to `96` pixels |
| `font_name` | `Arial`, `Verdana`, `Tahoma`, `Georgia`, `Courier New`, or `monospace` |
| `horizontal_alignment` | `left`, `center`, or `right` |
| `vertical_alignment` | `top`, `center`, or `bottom` |
| `column_span` | Card width from `1` to `4` dashboard columns; responsive screens reduce it automatically |
| `height_multiplier` | Card height from `1` to `3` dashboard rows |
| `y_padding_percent` | Graph Y-axis padding added above and below as a percentage of its data range |
| `x_axis_label` | Optional graph X-axis title, up to 50 characters |
| `y_axis_label` | Optional graph Y-axis title, up to 50 characters |
| `auto_delete` | Delete the database row when the Python object is destroyed |

Construction immediately inserts a database row and sets `card.id` to its integer ID.
Unknown types/colors are stored but may not render usefully.

## Card attributes

`id`, `type`, `title`, `color`, `min_value`, `max_value`, `value`, `description`,
`font_size`, `font_name`, `horizontal_alignment`, `vertical_alignment`, `column_span`,
`height_multiplier`, `y_padding_percent`, `x_axis_label`, `y_axis_label`, and
`auto_delete` are public. Changing an attribute only changes memory until `save()`.

## Widget typography and alignment

All card types accept the four optional style settings. Existing cards keep their
original appearance because omitted settings remain `None`. Chart label sizes are
limited to 18 pixels so labels continue to fit inside their fixed canvas.

Use `column_span=2`, `3`, or `4` for wide graphs and tables. On narrower screens,
the dashboard automatically reduces the span so the page never needs horizontal scrolling.
Use `height_multiplier=2` or `3` to give a graph more vertical plotting space.
For example, values from `0` to `10` with `y_padding_percent=20` produce a
Y-axis from `-2` to `12`. List-based graph samples are numbered from `1`, and
graphs draw five horizontal Y-grid lines.

```python
counter = Dashboard.Card(
    "info",
    "Counter",
    color="green",
    value=0,
    font_size=64,
    font_name="Arial",
    horizontal_alignment="center",
    vertical_alignment="center"
)
```

The dashboard rejects unsupported fonts and alignments and constrains font sizes to
the supported range. All listed fonts are available without an Internet connection.

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

## Temperature history with elapsed time

Run `CodyNick examples/dashboard/temperature_on_dashboard.py` to show a live
temperature gauge and graph. The example checks for `None` before rounding and
accepts readings only when they are non-zero and below 120 C. Negative readings
are accepted by this demo filter. Rejected readings do not update either card.

The graph keeps the latest 20 accepted readings as `[elapsed_seconds, temperature]`
pairs, timed with `time.monotonic()`. Its `Time (s)` axis shows elapsed time since
the script started, including gaps caused by rejected readings. It attempts a new
reading every 2.5 seconds plus the time spent reading and updating the dashboard.

## Deterministic cleanup

```python
with Dashboard.Card("info", "State", value="Starting") as state:
    state.set("Running")
```

The context manager deletes the card on exit. Python destructors are not guaranteed
after a crash, power loss, or forced termination. Use `delete()` or `Dashboard.clear()`
when cleanup is important. Use `auto_delete=False` only for cards intentionally kept
after the script exits.

