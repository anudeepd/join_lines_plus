"""
Tests for Join Lines Plus plugin logic.

Mocks sublime API — no Sublime Text install needed.
Run: uv run pytest tests/

Mocked API: sublime.Region, sublime_plugin.TextCommand,
FakeView (size, sel, substr, window, lines, replace, run_command)
Not mocked: file_name(), rowcol(), buffer_id(), etc.
"""

import sys
import types
import unittest

# ---------------------------------------------------------------------------
# Minimal sublime API mock
# ---------------------------------------------------------------------------

sublime_mod = types.ModuleType("sublime")
sublime_plugin_mod = types.ModuleType("sublime_plugin")


class Region:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def empty(self):
        return self.a == self.b

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b

    def __repr__(self):
        return f"Region({self.a}, {self.b})"


sublime_mod.Region = Region


class TextCommand:
    def __init__(self, view):
        self.view = view


sublime_plugin_mod.TextCommand = TextCommand

sys.modules["sublime"] = sublime_mod
sys.modules["sublime_plugin"] = sublime_plugin_mod

# ---------------------------------------------------------------------------
# Import plugin after mocks are in place
# ---------------------------------------------------------------------------

from pathlib import Path  # noqa: E402

plugin_path = Path(__file__).parent.parent
sys.path.insert(0, str(plugin_path))
import join_lines_plus as plugin  # noqa: E402


# ---------------------------------------------------------------------------
# Fake view helpers
# ---------------------------------------------------------------------------


class FakeEdit:
    pass


class FakeView:
    def __init__(self, content):
        self._content = content

    def size(self):
        return len(self._content)

    def sel(self):
        return []

    def substr(self, region):
        if isinstance(region, int):
            return self._content[region] if 0 <= region < len(self._content) else ""
        return self._content[region.a : region.b]

    def window(self):
        class FakeWindow:
            def status_message(self, msg):
                pass

        return FakeWindow()

    def lines(self, region):
        text = self._content[region.a : region.b]
        result = []
        pos = region.a
        for raw_line in text.splitlines(keepends=True):
            end = pos + len(raw_line)
            line_end = end - 1 if raw_line.endswith("\n") else end
            result.append(Region(pos, line_end))
            pos = end
        return result

    def replace(self, edit, region, text):
        self._content = self._content[: region.a] + text + self._content[region.b :]

    def run_command(self, name, args=None):
        """Dispatch to JoinLinesPlusCommand (used by shortcut commands)."""
        if name == "join_lines_plus":
            plugin.JoinLinesPlusCommand(self).run(FakeEdit(), **(args or {}))
            return
        class_name = "".join(w.capitalize() for w in name.split("_")) + "Command"
        cls = getattr(plugin, class_name)
        cls(self).run(FakeEdit())


def run_join(content, selections=None, **kwargs):
    """Run JoinLinesPlusCommand directly with given kwargs."""
    view = FakeView(content)
    if selections is not None:
        view.sel = lambda: [Region(a, b) for a, b in selections]
    plugin.JoinLinesPlusCommand(view).run(FakeEdit(), **kwargs)
    return view._content


def run_shortcut(content, cls_name):
    """Run a named shortcut command class against content."""
    view = FakeView(content)
    cls = getattr(plugin, cls_name)
    cls(view).run(FakeEdit())
    return view._content


INPUT = "foo\nbar\nbaz\n"

# ---------------------------------------------------------------------------
# Tests: base JoinLinesPlusCommand
# ---------------------------------------------------------------------------


class TestJoinLinesBase(unittest.TestCase):
    def test_basic_join(self):
        self.assertEqual(run_join(INPUT), "foo, bar, baz\n")

    def test_custom_separator(self):
        self.assertEqual(run_join(INPUT, separator=" | "), "foo | bar | baz\n")

    def test_single_quote(self):
        self.assertEqual(run_join("foo\nbar\n", quote_char="'"), "'foo', 'bar'\n")

    def test_double_quote(self):
        self.assertEqual(run_join("foo\nbar\n", quote_char='"'), '"foo", "bar"\n')

    def test_prefix_suffix_tuple(self):
        self.assertEqual(
            run_join("foo\nbar\n", quote_char="'", prefix="(", suffix=")"),
            "('foo', 'bar')\n",
        )

    def test_prefix_suffix_list(self):
        self.assertEqual(
            run_join("foo\nbar\n", quote_char="'", prefix="[", suffix="]"),
            "['foo', 'bar']\n",
        )

    def test_blank_lines_skipped(self):
        self.assertEqual(run_join("foo\n\nbar\n\nbaz\n"), "foo, bar, baz\n")

    def test_whitespace_stripped(self):
        self.assertEqual(run_join("  foo  \n  bar  \n"), "foo, bar\n")

    def test_single_line(self):
        self.assertEqual(run_join("foo\n"), "foo\n")

    def test_all_blank_lines_noop(self):
        original = "\n\n\n"
        self.assertEqual(run_join(original), original)

    def test_empty_buffer_noop(self):
        self.assertEqual(run_join(""), "")

    def test_no_separator(self):
        self.assertEqual(run_join("foo\nbar\n", separator=""), "foobar\n")

    def test_selection_join(self):
        result = run_join("foo\nbar\nbaz\n", selections=[(0, 7)])
        self.assertEqual(result, "foo, bar\nbaz\n")

    def test_selection_with_quote(self):
        result = run_join("foo\nbar\nbaz\n", selections=[(0, 7)], quote_char="'")
        self.assertEqual(result, "'foo', 'bar'\nbaz\n")

    def test_multiple_selections(self):
        # Each region joined independently, bottom-to-top replacement preserves offsets.
        result = run_join("foo\nbar\nbaz\nqux\n", selections=[(0, 7), (8, 15)])
        self.assertEqual(result, "foo, bar\nbaz, qux\n")

    def test_embedded_separator(self):
        # Existing separator chars in lines are preserved as-is.
        result = run_join("a,b\nc,d\n", separator="|")
        self.assertEqual(result, "a,b|c,d\n")

    def test_existing_quote_char_no_escaping(self):
        # Plugin wraps without escaping — caller is responsible for safe input.
        result = run_join("it's\nfine\n", quote_char="'")
        self.assertEqual(result, "'it's', 'fine'\n")

    def test_unicode(self):
        result = run_join("föo\nbàr\n")
        self.assertEqual(result, "föo, bàr\n")

    def test_no_trailing_newline(self):
        result = run_join("foo\nbar")
        self.assertEqual(result, "foo, bar")

    def test_trailing_newline_preserved(self):
        result = run_join("foo\nbar\n")
        self.assertEqual(result, "foo, bar\n")

    def test_single_line_with_prefix_suffix(self):
        result = run_join("foo\n", prefix="(", suffix=")")
        self.assertEqual(result, "(foo)\n")

    def test_all_blank_selection_noop(self):
        result = run_join("foo\nbar\n", selections=[(4, 8)])
        self.assertEqual(result, "foo\nbar\n")


# ---------------------------------------------------------------------------
# Tests: all 14 shortcut commands
# ---------------------------------------------------------------------------


class TestShortcutCommands(unittest.TestCase):
    # 1
    def test_join_comma_no_space(self):
        self.assertEqual(run_shortcut(INPUT, "JoinCommaNoSpace"), "foo,bar,baz\n")

    # 2
    def test_join_comma_space(self):
        self.assertEqual(run_shortcut(INPUT, "JoinCommaSpace"), "foo, bar, baz\n")

    # 3
    def test_quote_join_comma_no_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "QuoteJoinCommaNoSpace"), "'foo','bar','baz'\n"
        )

    # 4
    def test_quote_join_comma_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "QuoteJoinCommaSpace"), "'foo', 'bar', 'baz'\n"
        )

    # 5
    def test_quote_join_tuple_no_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "QuoteJoinTupleCommaNoSpace"), "('foo','bar','baz')\n"
        )

    # 6
    def test_quote_join_tuple_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "QuoteJoinTupleCommaSpace"), "('foo', 'bar', 'baz')\n"
        )

    # 7
    def test_quote_join_list_no_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "QuoteJoinListCommaNoSpace"), "['foo','bar','baz']\n"
        )

    # 8
    def test_quote_join_list_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "QuoteJoinListCommaSpace"), "['foo', 'bar', 'baz']\n"
        )

    # 9
    def test_double_quote_join_comma_no_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "DoubleQuoteJoinCommaNoSpace"), '"foo","bar","baz"\n'
        )

    # 10
    def test_double_quote_join_comma_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "DoubleQuoteJoinCommaSpace"), '"foo", "bar", "baz"\n'
        )

    # 11
    def test_double_quote_join_tuple_no_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "DoubleQuoteJoinTupleCommaNoSpace"),
            '("foo","bar","baz")\n',
        )

    # 12
    def test_double_quote_join_tuple_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "DoubleQuoteJoinTupleCommaSpace"),
            '("foo", "bar", "baz")\n',
        )

    # 13
    def test_double_quote_join_list_no_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "DoubleQuoteJoinListCommaNoSpace"),
            '["foo","bar","baz"]\n',
        )

    # 14
    def test_double_quote_join_list_space(self):
        self.assertEqual(
            run_shortcut(INPUT, "DoubleQuoteJoinListCommaSpace"),
            '["foo", "bar", "baz"]\n',
        )


if __name__ == "__main__":
    unittest.main()
