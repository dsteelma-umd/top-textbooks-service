from datetime import datetime, timezone
from typing import Any, Optional, Text, TextIO

from core.logging import create_logger
from core.web_errors import blueprint
from flask import Flask, abort, request
from yaml import safe_load

from equipment_availability import __version__
from equipment_availability.processor import AlmaBibProcessor, AlmaGateway, EquipmentAvailabilityProcessor

logger = create_logger(__name__)


def get_config(config_source: Optional[str | TextIO] = None) -> dict[str, Any]:
    if config_source is None:
        raise RuntimeError('Config file not provided')

    if isinstance(config_source, str):
        with open(config_source) as fh:
            return safe_load(fh)

    if config_source:
        return safe_load(config_source)


def app(config: Optional[str | TextIO] = None) -> Flask:
    gateway = AlmaGateway(config=get_config(config))
    bibProcessor = AlmaBibProcessor(gateway)
    equipmentAvailabilityProcessor = EquipmentAvailabilityProcessor(config, gateway, bibProcessor)
    return _create_app(equipmentAvailabilityProcessor)


def _create_app(equipmentAvailabilityProcessor) -> Flask:
    _app = Flask(
        import_name=__name__,
    )

    _app.register_blueprint(blueprint)
    logger.info(f'Starting equipment-availability-service/{__version__}')

    @_app.route('/')
    def root():
        return f"""
        <h1>Service for Equipment Availability</h1>
        <h2>Version: equipment-availability-service/{__version__}</h2>
        <h3>Endpoints</h3>
        <ul>
            <li>/api/equipment-availability</li>
        </ul>
        """

    @_app.route('/api/equipment-availability', methods=['GET', 'POST'])  # type: ignore
    def equipment_availability():
        if not request.is_json:
            abort(400, 'Request was not JSON')

        requestData = request.get_json()
        logger.info(f'{requestData=}')
        now = datetime.now(timezone.utc)
        responseData = equipmentAvailabilityProcessor.process(requestData, now)
        return responseData

    return _app
