"""Logging configuration for DAG application"""
import os
import logging
import sys
from logging.handlers import RotatingFileHandler

DEFAULT_LOG_FILE = 'artefact_generator_debug.log'


def setup_logging(
    filename: str = None,
    level: int = logging.DEBUG,
    console_level: int = logging.INFO,
):
    """Configure root logging to a rotating file and the console.

    The file keeps full DEBUG detail (request/response dumps); the console
    shows INFO and above so ``streamlit run`` surfaces provider, status, and
    error activity in the terminal where you launched it.

    ``DAG_LOG_FILE`` overrides the file path; set it empty to disable the
    file entirely (a server install logs to the journal via the console).

    Idempotent: Streamlit re-executes the script on every rerun, so we tag
    our handlers and skip re-adding them to avoid duplicated log lines.
    """
    if filename is None:
        filename = os.getenv("DAG_LOG_FILE", DEFAULT_LOG_FILE)

    root = logging.getLogger()
    root.setLevel(level if filename else console_level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    installed = {getattr(h, '_dag_handler', None) for h in root.handlers}

    if filename and 'file' not in installed:
        file_handler = RotatingFileHandler(
            filename, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
        )
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
