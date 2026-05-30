"""Logging configuration for DAG application"""
import logging
import sys


def setup_logging(
    filename: str = 'artefact_generator_debug.log',
    level: int = logging.DEBUG,
    console_level: int = logging.INFO,
):
    """Configure root logging to both a file and the console.

    The file keeps full DEBUG detail (request/response dumps); the console
    shows INFO and above so ``streamlit run`` surfaces provider, status, and
    error activity in the terminal where you launched it.

    Idempotent: Streamlit re-executes the script on every rerun, so we tag
    our handlers and skip re-adding them to avoid duplicated log lines.
    """
    root = logging.getLogger()
    root.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    installed = {getattr(h, '_dag_handler', None) for h in root.handlers}

    if 'file' not in installed:
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler._dag_handler = 'file'
        root.addHandler(file_handler)

    if 'console' not in installed:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        console_handler._dag_handler = 'console'
        root.addHandler(console_handler)
