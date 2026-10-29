import enum
import logging
from logging import LogRecord, getLogger

from rich.console import Console
from rich.logging import RichHandler

from rich.panel import Panel
from rich.tree import Tree

from harness101.settings import settings

PACKAGE = "harness101"

console = Console(stderr=True)


@enum.unique
class LogLevel(enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _is_rich(value: object) -> bool:
    return not isinstance(value, str) and (
        hasattr(value, "__rich_console__") or hasattr(value, "__rich__")
    )


class RenderableRichHandler(RichHandler):
    """Pass Panel/Tree/Markdown through console.print. Strings stay RichHandler."""

    def emit(self, record: LogRecord) -> None:
        try:
            if _is_rich(record.msg):
                self.console.print(record.msg)
                return
            extras = record.args
            if isinstance(record.msg, str) and extras and not isinstance(extras, dict):
                args = extras if isinstance(extras, tuple) else (extras,)
                if any(_is_rich(arg) for arg in args):
                    if record.msg.strip():
                        self.console.print(record.msg)
                    for arg in args:
                        if _is_rich(arg):
                            self.console.print(arg)
                    return
        except Exception:
            self.handleError(record)
            return
        super().emit(record)


def setup_logging() -> None:
    """Attach one colored handler to the package logger. Call once."""
    package_logger = getLogger(PACKAGE)
    if package_logger.handlers:
        return
    package_logger.setLevel(
        logging.getLevelNamesMapping().get(
            settings.log_level.upper(),
            logging.INFO,
        )
    )
    handler = RenderableRichHandler(
        console=console,
        show_time=True,
        show_path=True,
        markup=True,
        log_time_format=settings.log_datefmt,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    package_logger.addHandler(handler)
    package_logger.propagate = False


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a named logger under the package so script runs inherit the handler.

    `python path/to/chat_in_the_loop_v3.py` sets __name__ to __main__, which
    would otherwise propagate to root (WARNING) and drop DEBUG.
    """
    setup_logging()
    if not name or name == "__main__":
        name = f"{PACKAGE}.__main__"
    return getLogger(name)


def _leaf(value: object, max_len: int = 80) -> str:
    text = str(value)
    if len(text) > max_len:
        return text[:max_len] + "…"
    return text


def _fill_tree(tree: Tree, value: object) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, (dict, list)) or hasattr(child, "model_dump"):
                branch = tree.add(f"[cyan]{key}[/]")
                _fill_tree(branch, child)
            else:
                tree.add(f"[cyan]{key}[/]: {_leaf(child)}")
        return
    if isinstance(value, list):
        for i, item in enumerate(value):
            branch = tree.add(f"[dim][{i}][/]")
            _fill_tree(branch, item)
        return
    tree.add(_leaf(value))


def to_tree(label: str, value: object) -> Tree:
    tree = Tree(f"[bold]{label}[/]")
    _fill_tree(tree, value)
    return tree


def get_response_panel(name: str, response: object):
    """Pretty-print a model as a tree inside a panel."""

    return Panel(
        to_tree(name, response),
        title=f"[cyan bold]{name}[/]",
        border_style="bright_blue",
        padding=(1, 2),
        expand=False,
    )
