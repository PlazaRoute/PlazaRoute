from ast import literal_eval
from time import gmtime, strftime

from plaza_routing.business import public_transport_service
from plaza_routing.business.util import route_cost_matrix
from plaza_routing.business.util import coordinate_transformer
from plaza_routing.integration import geocoding_service
from plaza_routing.integration import overpass_service
from plaza_routing.integration import search_ch_service
from plaza_routing.integration.routing_engine_service import RoutingEngine
from plaza_routing.integration.routing_strategy.graphhopper_strategy import GraphhopperRoutingStrategy

MAX_WALKING_TIME = 60 * 5


def route(start, destination):
    print(f'route from {start} to {destination}')
    start_tuple = literal_eval(start)
    destination_tuple = geocoding_service.geocode(destination)
    departure = strftime('%H:%M', gmtime())

    routing_engine = RoutingEngine(GraphhopperRoutingStrategy())

    walking_route = routing_engine.route(start_tuple, destination_tuple)
    walking_route_time = walking_route['time']

    if walking_route_time <= MAX_WALKING_TIME:
        # walking is faster to even consider public transportation
        return _convert_walking_route_to_overall_response(walking_route)

    best_route = _retrieve_best_route_combination(start_tuple,
                                                  destination, destination_tuple,
                                                  departure,
                                                  routing_engine)

    if not best_route or walking_route_time < best_route['accumulated_time']:
        # walking is still faster than taking the public transportation or
        # no connection was found for the given start and destination
        print(f"{walking_route_time} smaller than {best_route['accumulated_time']}" )
        return _convert_walking_route_to_overall_response(walking_route)

    return best_route


def _retrieve_best_route_combination(start_tuple, destination, destination_tuple, departure, routing_engine):
    temp_smallest_route_costs = 0
    temp_best_route = None
    public_transport_stops = overpass_service.get_public_transport_stops(start_tuple)
    for public_transport_stop in public_transport_stops:
        print(f'public transport stop: {public_transport_stop}')

        connection = search_ch_service.get_connection(public_transport_stop, destination, departure)

        if not _is_relevant_connection(connection):
            continue

        first_leg = connection['legs'][0]
        initial_start_location = _get_start_exit_stop_position(first_leg, start_tuple)[0]
        start_walking_route = routing_engine.route(start_tuple, initial_start_location)

        last_leg = connection['legs'][-2]
        final_stop_location = _get_start_exit_stop_position(last_leg, destination_tuple)[1]
        end_walking_route = routing_engine.route(final_stop_location, destination_tuple)

        total_cost = route_cost_matrix.calculate_costs((start_walking_route, connection, end_walking_route))
        if total_cost < temp_smallest_route_costs or temp_smallest_route_costs == 0:
            temp_smallest_route_costs = total_cost
            temp_best_route = {
                'start_walking_route': start_walking_route,
                'public_transport_connection':
                    public_transport_service.get_path_for_public_transport_connection(connection),
                'end_walking_route': end_walking_route,
                'accumulated_time': start_walking_route['time'] + connection['duration'] + end_walking_route['time']
            }
    return temp_best_route


def _is_relevant_connection(connection):
    if connection['legs'][0]['type'] == 'walk':
        print(f'filter connection: {connection}')
        return False
    return True


def _get_start_exit_stop_position(leg, center_location):
    line = leg['line']
    start_stop_uicref = leg['stopid']
    exit_stop_uicref = leg['exit']['stopid']
    fallback_start_position = coordinate_transformer.transform_ch_to_wgs(leg['x'], leg['y'])
    fallback_exit_position = coordinate_transformer.transform_ch_to_wgs(leg['exit']['x'], leg['exit']['y'])
    start_position, exit_position = overpass_service.get_start_exit_stop_position(center_location,
                                                                                  start_stop_uicref,
                                                                                  exit_stop_uicref,
                                                                                  line,
                                                                                  fallback_start_position,
                                                                                  fallback_exit_position)
    return start_position, exit_position


def _convert_walking_route_to_overall_response(walking_route):
    return {
        'start_walking_route': walking_route,
        'public_transport_connection': {},
        'end_walking_route': {},
        'accumulated_time': walking_route['time']
    }


if __name__ == "__main__":
    print(route('47.41071, 8.55546', 'Zürich, Hardbrücke'))
    # print(route('47.366451,8.548779', 'Bellevueplatz, Zürich'))   # walking distance
