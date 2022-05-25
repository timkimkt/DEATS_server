from geopy.distance import geodesic

DELTA_RADIAL_DISTANCE = 0.2  # in miles
COST_PER_DELTA_RADIAL_DISTANCE = 0.25  # in DEATS tokens

DELTA_SURGE = 2  # Every 2 unmatched orders constitute delivery request surge
COST_PER_DELTA_SURGE = 0.2

COST_PER_TOKEN = 300  # $3


def compute_token_fee(pickup_loc, drop_loc, num_unmatched_orders):
    pickup_tuple = (pickup_loc["coordinates"]["lat"], pickup_loc["coordinates"]["long"])
    drop_tuple = (drop_loc["coordinates"]["lat"], drop_loc["coordinates"]["long"])
    base_fee = 0.1
    distance = geodesic(pickup_tuple, drop_tuple).miles
    print("pickup loc:", pickup_loc, "drop loc:", drop_loc, "distance:", distance)

    distance_fee = (distance // DELTA_RADIAL_DISTANCE) * COST_PER_DELTA_RADIAL_DISTANCE
    print("distance fee:", distance_fee)

    surge_fee = (num_unmatched_orders // DELTA_SURGE) * COST_PER_DELTA_SURGE
    print("surge fee:", surge_fee)

    return base_fee + distance_fee + surge_fee


def compute_new_fee(new_pickup_loc, new_drop_loc, old_pickup_loc, old_drop_loc, old_fee):
    new_pickup_tuple = (new_pickup_loc["coordinates"]["lat"], new_pickup_loc["coordinates"]["long"])
    new_drop_tuple = (new_drop_loc["coordinates"]["lat"], new_drop_loc["coordinates"]["long"])

    new_distance = geodesic(new_pickup_tuple, new_drop_tuple).miles
    print("pickup loc:", new_pickup_loc, "drop loc:", new_drop_loc, "distance:", new_distance)

    new_distance_fee = (new_distance // DELTA_RADIAL_DISTANCE) * COST_PER_DELTA_RADIAL_DISTANCE
    print("distance fee:", new_distance_fee)

    old_pickup_tuple = (old_pickup_loc["coordinates"]["lat"], old_pickup_loc["coordinates"]["long"])
    old_drop_tuple = (old_drop_loc["coordinates"]["lat"], old_drop_loc["coordinates"]["long"])

    old_distance = geodesic(old_pickup_tuple, old_drop_tuple).miles
    print("pickup loc:", old_pickup_loc, "drop loc:", old_drop_loc, "distance:", old_distance)

    old_distance_fee = (old_distance // DELTA_RADIAL_DISTANCE) * COST_PER_DELTA_RADIAL_DISTANCE
    print("distance fee:", old_distance_fee)

    return old_fee + new_distance_fee - old_distance_fee


def compute_amount(order_fee):
    return order_fee * COST_PER_TOKEN

