import sys


def configure_console_output():
    """
    Evita errores por emojis en consolas Windows con cp1252.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass


def _emit(message):
    print(message)


def log_info(message):
    _emit(message)


def log_warning(message):
    _emit(message)


def log_error(message):
    _emit(message)


def log_success(message):
    _emit(message)

