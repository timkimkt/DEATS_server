from geopy.distance import geodesic

DELTA_RADIAL_DISTANCE = 0.2  # in miles
COST_PER_DELTA_RADIAL_DISTANCE = 0.25  # in DEATS tokens

DELTA_SURGE = 2  # Every 2 unmatched orders constitute delivery request surge
COST_PER_DELTA_SURGE = 0.2


def compute_token_fee(pickup_coordinates, drop_coordinates, num_unmatched_orders):
    pickup_tuple = (pickup_coordinates["lat"], pickup_coordinates["long"])
    drop_tuple = (drop_coordinates["lat"], pickup_coordinates["long"])
    base_fee = 0.1
    distance = geodesic(pickup_tuple, drop_tuple).miles
    distance_fee = (distance // DELTA_RADIAL_DISTANCE) * COST_PER_DELTA_RADIAL_DISTANCE
    surge_fee = (num_unmatched_orders // DELTA_SURGE) * COST_PER_DELTA_SURGE

    return base_fee + distance_fee + surge_fee
