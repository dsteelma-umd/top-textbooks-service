
from os import environ

import click
from core.logging import create_logger
from dotenv import load_dotenv
from waitress import serve

from equipment_availability import __version__
from equipment_availability.web import app

logger = create_logger(__name__)


@click.command()
@click.option(
    '--listen',
    default='0.0.0.0:5000',
    help='Address and port to listen on. Default is "0.0.0.0:5000".',
    metavar='[ADDRESS]:PORT',
)
@click.option(
    '--alma_config', 'alma_config_file',
    type=click.File(),
    help='Configuration file for the Alma API.',
)
@click.version_option(__version__, '--version', '-V')
@click.help_option('--help', '-h')
def run(listen, alma_config_file):
    load_dotenv()
    if 'ALMA_API_KEY' not in environ:
        raise RuntimeError('ALMA_API_KEY not set in environment')

    server_identity = f'equipment_availability-service/{__version__}'
    logger.info(f'Starting {server_identity}')
    try:
        serve(
            app=app(config=alma_config_file),
            listen=listen,
            ident=server_identity,
        )
    except (OSError, RuntimeError) as e:
        logger.error(f'Exiting: {e}')
        raise SystemExit(1) from e
