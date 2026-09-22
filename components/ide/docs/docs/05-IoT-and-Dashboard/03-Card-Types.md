# Dashboard Card Types and Values

## Scalar cards

| Type | Value | Browser behavior |
| --- | --- | --- |
| `led` | Boolean or `"true"`/`"false"` | Colored status indicator |
| `gauge` | Number | Read-only gauge using `min_value` and `max_value` |
| `info` | Text | Read-only multiline text |
| `textarea` | Text | Browser-editable multiline text |
| `button` | Boolean | Click writes `true`; button stays disabled until Python resets `false` |
| `switch` | Boolean | Click toggles `true`/`false` |
| `slider` | Number | Browser writes a number between `min_value` and `max_value` |

```python
temperature = Dashboard.Card(
    "gauge", "Temperature", color="green",
    min_value=-10, max_value=50, value=22.5,
    description="Degrees Celsius",
)
```

## Graph

`graph` requires numeric points. Accepted Python values include:

```python
Dashboard.Card("graph", "Samples", value=[12, 14, 13, 18])
```

```python
Dashboard.Card("graph", "Samples", value={0: 12, 5: 14, 10: 18})
```

```python
Dashboard.Card("graph", "Rooms", value={
    "Room A": [[0, 21.0], [1, 21.5], [2, 22.0]],
    "Room B": {0: 19.5, 1: 20.0, 2: 20.2},
})
```

Arrays use their index as `x` unless an item is `[x, y]`. A graph needs at least two
points overall. Nested object keys become series names.

## Bar and pie charts

Both accept a label-to-number dictionary:

```python
chart = Dashboard.Card("bar", "Votes", value={
    "Red": 8,
    "Green": 12,
    "Blue": 5,
})
```

They also accept arrays of `[label, value]`, objects containing `label`/`value`, or a
plain numeric array. Pie charts ignore non-positive values and require a positive total.

## Table

```python
table = Dashboard.Card("table", "Readings", value={
    "Temperature": "23.5 C",
    "Humidity": "41%",
})
```

Objects render as key/value rows. Arrays may contain `[key, value]`, objects with
`key` and `value`, or ordinary items whose array index becomes the key.

## Updating structured cards

```python
history = []
history.append(23.5)
graph.set(history)
```

The complete JSON value is written on every update. Keep histories bounded to avoid a
continually growing database row:

```python
history = (history + [new_value])[-60:]
graph.set(history)
```

