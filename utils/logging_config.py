"""Logging configuration for DAG application"""
import logging


def setup_logging(filename: str = 'artefact_generator_debug.log', level: int = logging.DEBUG):
    """Set up logging configuration"""
    logging.basicConfig(
        filename=filename,
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
