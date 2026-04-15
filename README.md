# Join Lines Plus

Sublime Text plugin. Joins lines into a single line with configurable separator, optional quoting, and optional wrapper (prefix/suffix).

## Usage

1. **Optional:** select the lines you want to join. Skip this to process the entire file.
2. Open Command Palette — `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac).
3. Type `Join Lines Plus` and pick a command.

**With selection** — only selected lines are joined; rest of file untouched. Multiple selections work independently.  
**Without selection** — entire buffer replaced with joined result.

## Commands (Command Palette)

| Caption | Output example |
|---|---|
| Join Lines Plus: Comma, No Space | `foo,bar,baz` |
| Join Lines Plus: Comma, Space | `foo, bar, baz` |
| Join Lines Plus: Quote, Comma, No Space | `'foo','bar','baz'` |
| Join Lines Plus: Quote, Comma, Space | `'foo', 'bar', 'baz'` |
| Join Lines Plus: Quote, Tuple, No Space | `('foo','bar','baz')` |
| Join Lines Plus: Quote, Tuple, Space | `('foo', 'bar', 'baz')` |
| Join Lines Plus: Quote, List, No Space | `['foo','bar','baz']` |
| Join Lines Plus: Quote, List, Space | `['foo', 'bar', 'baz']` |
| Join Lines Plus: Double Quote, Comma, No Space | `"foo","bar","baz"` |
| Join Lines Plus: Double Quote, Comma, Space | `"foo", "bar", "baz"` |
| Join Lines Plus: Double Quote, Tuple, No Space | `("foo","bar","baz")` |
| Join Lines Plus: Double Quote, Tuple, Space | `("foo", "bar", "baz")` |
| Join Lines Plus: Double Quote, List, No Space | `["foo","bar","baz"]` |
| Join Lines Plus: Double Quote, List, Space | `["foo", "bar", "baz"]` |

## Behaviour

- **No selection** — processes entire buffer, replaces in-place.
- **Selection(s)** — processes each selection independently, replaces only selected region.
- Blank/whitespace-only lines are silently skipped.
- Lines stripped of leading/trailing whitespace before joining.

## Base Command

```json
{
    "command": "join_lines_plus",
    "args": {
        "separator": ", ",
        "quote_char": "'",
        "prefix": "(",
        "suffix": ")"
    }
}
```

All args optional. Defaults: `separator=", "`, `quote_char=""`, `prefix=""`, `suffix=""`.

## Installation

Copy `join_lines_plus/` into your Sublime Text `Packages/` directory.

## Running Tests

```bash
uv run pytest tests/
```

Or with a plain venv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pytest
pytest tests/
```
