import os
from datetime import UTC, datetime

from equipment_availability.processor import AlmaBibProcessor, AlmaGateway, EquipmentAvailabilityProcessor


def create_mock_config(mms_id=None):
    return {
        'host': 'http://test.com',
        'retrieve_bibs_endpoint': '/almaws/v1/bibs',
        'retrieve_bib_loan_endpoint': '/almaws/v1/bibs/{MMS_ID}/loan'.format(MMS_ID=mms_id),
    }


def resource_file_as_string(filepath):
    with open(os.path.normpath(filepath), 'r') as resource_file:
        return resource_file.read()


def test_process_item_available(requests_mock):
    xml_response = resource_file_as_string(
        'tests/resources/equipment_availability/retrieve_bibs_200_response_available.xml'
    )

    mock_config = create_mock_config()
    mock_retrieve_bibs_url = mock_config['host'] + mock_config['retrieve_bibs_endpoint']

    requests_mock.get(mock_retrieve_bibs_url, text=xml_response, status_code=200)
    mock_gateway = AlmaGateway(mock_config)
    bib_processor = AlmaBibProcessor(mock_gateway)
    processor = EquipmentAvailabilityProcessor(mock_gateway, bib_processor)

    now = datetime.fromisoformat('2023-12-14T12:09:23+05:00')
    mock_request = ['990063177290108238']
    expected_result = {'990063177290108238': {'count': 4, 'due': '', 'status': 'available'}}

    processed_result = processor.process(mock_request, now)
    assert processed_result == expected_result


def test_process_item_unavailable_with_due_date(requests_mock):
    mms_id = '990062909040108238'
    bibs_xml_response = resource_file_as_string(
        'tests/resources/equipment_availability/retrieve_bibs_200_response_unavailable_with_due_date.xml'
    )

    loan_xml_response = resource_file_as_string(
        'tests/resources/equipment_availability/retrieve_bib_loan_200_response_with_due_date.xml'
    )

    mock_config = create_mock_config(mms_id)
    mock_retrieve_bibs_url = mock_config['host'] + mock_config['retrieve_bibs_endpoint']
    mock_retrieve_bib_loan_url = mock_config['host'] + mock_config['retrieve_bib_loan_endpoint'].format(MMS_ID=mms_id)

    # Retrieve Bibs response
    requests_mock.get(mock_retrieve_bibs_url, text=bibs_xml_response, status_code=200)
    # Retrieve Bib Loan response
    requests_mock.get(mock_retrieve_bib_loan_url, text=loan_xml_response, status_code=200)

    mock_gateway = AlmaGateway(mock_config)
    bib_processor = AlmaBibProcessor(mock_gateway)
    processor = EquipmentAvailabilityProcessor(mock_gateway, bib_processor)

    now = datetime.fromisoformat('2023-12-14T12:09:23+05:00')
    mock_request = [mms_id]
    expected_result = {mms_id: {'count': 0, 'due': '2023-12-14T23:47:54+00:00', 'status': 'unavailable'}}

    processed_result = processor.process(mock_request, now)
    assert processed_result == expected_result


def test_process_item_unavailable_with_due_date_is_past(requests_mock):
    mms_id = '990062909040108238'
    bibs_xml_response = resource_file_as_string(
        'tests/resources/equipment_availability/retrieve_bibs_200_response_unavailable_with_due_date.xml'
    )

    loan_xml_response = resource_file_as_string(
        'tests/resources/equipment_availability/retrieve_bib_loan_200_response_with_due_date.xml'
    )

    mock_config = create_mock_config(mms_id)
    mock_retrieve_bibs_url = mock_config['host'] + mock_config['retrieve_bibs_endpoint']
    mock_retrieve_bib_loan_url = mock_config['host'] + mock_config['retrieve_bib_loan_endpoint'].format(MMS_ID=mms_id)

    # Retrieve Bibs response
    requests_mock.get(mock_retrieve_bibs_url, text=bibs_xml_response, status_code=200)
    # Retrieve Bib Loan response
    requests_mock.get(mock_retrieve_bib_loan_url, text=loan_xml_response, status_code=200)

    mock_gateway = AlmaGateway(mock_config)
    bib_processor = AlmaBibProcessor(mock_gateway)
    processor = EquipmentAvailabilityProcessor(mock_gateway, bib_processor)

    # Now is later than the due date in the loan response
    now = datetime.fromisoformat('2024-01-01T12:09:23+05:00')
    mock_request = [mms_id]
    expected_result = {mms_id: {'count': 0, 'due': '', 'status': 'unavailable'}}

    processed_result = processor.process(mock_request, now)
    assert processed_result == expected_result
