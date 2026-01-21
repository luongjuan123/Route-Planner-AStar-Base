import heapq
import osmnx as ox
import networkx as nx
import googlemaps
from geopy.distance import great_circle
import os
import config


class RoutingEngine:
    """Optimized A* Pathfinding Engine with Traffic Awareness"""

    def __init__(self):
        # Initialize Google Maps Client for Traffic Data
        self.gmaps = googlemaps.Client(key=config.GOOGLE_MAPS_API_KEY)

    def haversine_distance(self, coord1, coord2):
        return great_circle(coord1, coord2).meters

    def get_traffic_multiplier(self, start_coords, end_coords, free_flow_seconds):

        try:
            # Ask Google for current duration in traffic
            # Note: start_coords is (lat, lng)
            result = self.gmaps.distance_matrix(
                origins=[start_coords],
                destinations=[end_coords],
                mode="driving",
                departure_time="now"
            )

            element = result['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                real_duration = element['duration_in_traffic']['value']  # in seconds

                if free_flow_seconds < 10:
                    return 1.0

                multiplier = real_duration / free_flow_seconds
                return max(1.0, multiplier)

        except Exception as e:
            print(f"Traffic fetch failed, defaulting to 1.0: {e}")

        return 1.0

    def get_graph_for_segment(self, start_coords, end_coords):
        mid_lat = (start_coords[0] + end_coords[0]) / 2
        mid_lon = (start_coords[1] + end_coords[1]) / 2
        dist_between = self.haversine_distance(start_coords, end_coords)

        # Buffer radius (same logic as before)
        radius = max(2000, dist_between * 0.8)


        filename = f"graph_{mid_lat:.3f}_{mid_lon:.3f}_{int(radius / 100) * 100}.graphml"
        filepath = os.path.join(config.CACHE_DIR, filename)

        if os.path.exists(filepath):
            print(f"Loading graph from cache: {filename}")
            # Load from disk (Fast!)
            graph = ox.load_graphml(filepath)
        else:
            print(f"Downloading new graph: {filename}")

            graph = ox.graph_from_point((mid_lat, mid_lon), dist=radius, network_type='drive')


            os.makedirs(config.CACHE_DIR, exist_ok=True)
            ox.save_graphml(graph, filepath)

        graph = ox.add_edge_speeds(graph)
        graph = ox.add_edge_travel_times(graph)

        # Calculate traffic (same as before)
        estimated_free_seconds = dist_between / 8.3
        traffic_factor = self.get_traffic_multiplier(start_coords, end_coords, estimated_free_seconds)

        for u, v, k, data in graph.edges(keys=True, data=True):
            base_time = data.get('travel_time', 1)
            data['traffic_weight'] = base_time * traffic_factor

        return graph

    def get_node_coords(self, graph, node_id):
        node = graph.nodes[node_id]
        return node['y'], node['x']

    def a_star_algorithm(self, graph, start_node, end_node):
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        came_from = {}

        g_score = {node: float('inf') for node in graph.nodes}
        g_score[start_node] = 0

        target_coords = (graph.nodes[end_node]['y'], graph.nodes[end_node]['x'])

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end_node:
                return self.reconstruct_path(came_from, current, graph)

            for neighbor in graph.neighbors(current):
                edge_data = graph.get_edge_data(current, neighbor)

                weight = min(d.get('traffic_weight', float('inf')) for d in edge_data.values())

                tentative_g_score = g_score[current] + weight

                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score

                    dist_to_target = self.haversine_distance(
                        (graph.nodes[neighbor]['y'], graph.nodes[neighbor]['x']),
                        target_coords
                    )
                    h_score_seconds = dist_to_target / 28.0

                    f_score = tentative_g_score + h_score_seconds

                    heapq.heappush(open_set, (f_score, neighbor))
        return None

    def reconstruct_path(self, came_from, current, graph):
        path = []
        while current in came_from:
            node = graph.nodes[current]
            path.append((node['y'], node['x']))
            current = came_from[current]
        node = graph.nodes[current]
        path.append((node['y'], node['x']))
        return path[::-1]