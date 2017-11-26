from tests.util import utils

import plaza_routing.integration.search_ch_service as search_ch_service
import plaza_routing.integration.overpass_service as overpass_service
import plaza_routing.integration.util.search_ch_parser as search_ch_parser


def mock_test_get_public_transport_route(monkeypatch):
    monkeypatch.setattr(search_ch_service, 'get_connection',
                        lambda start, destination, departure:
                        _mock_test_get_public_transport_route_get_connection(start, destination))
    monkeypatch.setattr(overpass_service, 'get_start_exit_stop_position',
                        lambda lookup_position, start_uic_ref, exit_uic_ref, line,
                        fallback_start_position, fallback_exit_position:
                        _mock_test_get_public_transport_route_get_start_exit_stop_position(start_uic_ref, line))


def _mock_test_get_public_transport_route_get_connection(start, destination):
    # Test: test_get_public_transport_route_single_leg
    response_file = None
    if start == 'Zürich, Rote Fabrik' and destination == 'Zürich, Stadtgrenze':
        response_file = utils.get_file('search_ch_response_single_leg.json', 'search_ch')

    # Test: test_get_public_transport_route_filtered_walking_leg
    elif start == 'Zürich, Rote Fabrik' and destination == 'Zürich Enge, Bahnhof':
        response_file = utils.get_file('search_ch_response_walking_leg.json', 'search_ch')

    # Test: test_get_public_transport_route_filtered_multiple_leg
    elif start == 'Zürich, Seerose' and destination == 'Zürich Enge, Bahnhof':
        response_file = utils.get_file('search_ch_response_multiple_legs.json', 'search_ch')

    if response_file is None:
        assert False
    return search_ch_parser.parse_connections(response_file)['connections'][0]


def _mock_test_get_public_transport_route_get_start_exit_stop_position(start_uic_ref, line):
    # Test: test_get_public_transport_route_single_leg
    if start_uic_ref == '8587347' and line == '161':
        return (8.5362646, 47.3424624), (8.5416616, 47.3349277)

    # Test: test_get_public_transport_route_filtered_walking_leg
    elif start_uic_ref == '8591304' and line == '7':
        return (8.5333468, 47.3448353), (8.5314319, 47.3643805)

    # Test: test_get_public_transport_route_filtered_multiple_leg
    elif start_uic_ref == '8591357' and line == '161':
        return (8.53813643293702, 47.338911019762165), (8.535039877782896, 47.36338051530903)
    elif start_uic_ref == '8591317' and line == '5':
        return (8.5345504, 47.3634496), (8.5314535, 47.3640971)
