"""
Join Lines Plus - Sublime Text plugin for joining multiple lines into one.

Features:
- Configurable separator (default ", ")
- Optional quote character around each line
- Optional prefix/suffix (e.g., parentheses for tuples, brackets for lists)
- 14 pre-defined shortcut commands
- Support for both whole-buffer and selection-based joins
"""

import sublime
import sublime_plugin


COMMAND_NAME = "join_lines_plus"


class JoinLinesPlusCommand(sublime_plugin.TextCommand):
    def run(self, edit, separator=", ", quote_char="", prefix="", suffix=""):
        # type: (object, str, str, str, str) -> None
        view = self.view
        selections = [region for region in view.sel() if not region.empty()]

        if not selections:
            region = sublime.Region(0, view.size())
            _, lines = self._collect_lines(region, quote_char)
            if not lines:
                view.window().status_message("Join Lines Plus: nothing to join")
                return
            joined = prefix + separator.join(lines) + suffix
            if self._has_trailing_newline(view):
                joined += "\n"
            if len(lines) > 1 or prefix or suffix:
                view.replace(edit, region, joined)
            elif len(lines) == 1 and not prefix and not suffix:
                view.window().status_message(
                    "Join Lines Plus: single line - no action taken"
                )
            return

        for region in reversed(selections):
            # Process bottom-to-top to preserve region offsets.
            region_lines, lines = self._collect_lines(region, quote_char)
            if lines:
                full_region = sublime.Region(
                    region_lines[0].a,
                    region_lines[-1].b,
                )
                joined = prefix + separator.join(lines) + suffix
                view.replace(edit, full_region, joined)
            elif region and self.view.substr(region).strip():
                # Has content but all blank - still show message
                view.window().status_message("Join Lines Plus: nothing to join")

    def _has_trailing_newline(self, view):
        # type: (object) -> bool
        """Check if the view ends with a newline character."""
        return view.size() > 0 and view.substr(view.size() - 1) == "\n"

    def _collect_lines(self, region, quote_char):
        # type: (object, str) -> tuple
        """Return stripped, optionally-quoted non-blank line strings for region.

        Blank/whitespace-only lines are intentionally skipped.

        Returns:
            tuple: (list of Region objects for lines, list of processed line strings)
        """
        region_lines = self.view.lines(region)
        result = []
        for line in region_lines:
            text = self.view.substr(line).strip()
            if text:
                if quote_char:
                    text = quote_char + text + quote_char
                result.append(text)
        return region_lines, result


def create_command(class_name, *, separator, quote_char, prefix, suffix):
    """Create a Sublime Text command class that delegates to JoinLinesPlusCommand.

    Args:
        class_name: Name for the command class (e.g., "JoinCommaNoSpace")
        separator: String to join lines with
        quote_char: Character to wrap each line with (e.g., "'", '"')
        prefix: String to prepend to joined result
        suffix: String to append to joined result
    """

    def run_command(self, edit, **kwargs):
        self.view.run_command(
            COMMAND_NAME,
            {
                "separator": separator,
                "quote_char": quote_char,
                "prefix": prefix,
                "suffix": suffix,
            },
        )

    cls = type(
        class_name,
        (sublime_plugin.TextCommand,),
        {"run": run_command},
    )
    # Required for Sublime Text command discovery - scans module globals for TextCommand subclasses.
    globals()[class_name] = cls


PRESETS = [
    {
        "class_name": "JoinCommaNoSpace",
        "separator": ",",
        "quote_char": "",
        "prefix": "",
        "suffix": "",
    },
    {
        "class_name": "JoinCommaSpace",
        "separator": ", ",
        "quote_char": "",
        "prefix": "",
        "suffix": "",
    },
    {
        "class_name": "QuoteJoinCommaNoSpace",
        "separator": ",",
        "quote_char": "'",
        "prefix": "",
        "suffix": "",
    },
    {
        "class_name": "QuoteJoinCommaSpace",
        "separator": ", ",
        "quote_char": "'",
        "prefix": "",
        "suffix": "",
    },
    {
        "class_name": "QuoteJoinTupleCommaNoSpace",
        "separator": ",",
        "quote_char": "'",
        "prefix": "(",
        "suffix": ")",
    },
    {
        "class_name": "QuoteJoinTupleCommaSpace",
        "separator": ", ",
        "quote_char": "'",
        "prefix": "(",
        "suffix": ")",
    },
    {
        "class_name": "QuoteJoinListCommaNoSpace",
        "separator": ",",
        "quote_char": "'",
        "prefix": "[",
        "suffix": "]",
    },
    {
        "class_name": "QuoteJoinListCommaSpace",
        "separator": ", ",
        "quote_char": "'",
        "prefix": "[",
        "suffix": "]",
    },
    {
        "class_name": "DoubleQuoteJoinCommaNoSpace",
        "separator": ",",
        "quote_char": '"',
        "prefix": "",
        "suffix": "",
    },
    {
        "class_name": "DoubleQuoteJoinCommaSpace",
        "separator": ", ",
        "quote_char": '"',
        "prefix": "",
        "suffix": "",
    },
    {
        "class_name": "DoubleQuoteJoinTupleCommaNoSpace",
        "separator": ",",
        "quote_char": '"',
        "prefix": "(",
        "suffix": ")",
    },
    {
        "class_name": "DoubleQuoteJoinTupleCommaSpace",
        "separator": ", ",
        "quote_char": '"',
        "prefix": "(",
        "suffix": ")",
    },
    {
        "class_name": "DoubleQuoteJoinListCommaNoSpace",
        "separator": ",",
        "quote_char": '"',
        "prefix": "[",
        "suffix": "]",
    },
    {
        "class_name": "DoubleQuoteJoinListCommaSpace",
        "separator": ", ",
        "quote_char": '"',
        "prefix": "[",
        "suffix": "]",
    },
]

for preset in PRESETS:
    create_command(**preset)
