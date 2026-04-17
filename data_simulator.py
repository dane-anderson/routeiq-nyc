import random

def describe_traffic(traffic_factor):
    if traffic_factor < 1.10:
        return "Light"
    elif traffic_factor < 1.30:
        return "Normal"
    elif traffic_factor < 1.50:
        return "Heavy"
    else:
        return "Crazy"
    
def get_subway_option(origin, destination):
    walk_to_station = random.randint(3, 10)
    wait_time = random.randint(2, 8)
    ride_time = random.randint(12, 30)
    transfers = random.randint(0, 2)
    transfer_time = transfers * 4

    eta = walk_to_station + wait_time + ride_time + transfer_time
    cost = 2.90

    return {
        "mode": "subway",
        "eta": eta,
        "cost": cost,
        "walk_to_station": walk_to_station,
        "wait_time": wait_time,
        "ride_time": ride_time,
        "transfers": transfers
    }


def get_taxi_option(origin, destination):
    pickup_time = random.randint(2, 8)
    drive_time = random.randint(15, 35)
    traffic_factor = random.uniform(1.0, 1.6)
    traffic_level = describe_traffic(traffic_factor)

    eta = round(pickup_time + (drive_time * traffic_factor))
    cost = round(random.uniform(18, 45), 2)

    
    return {
    "mode": "taxi",
    "eta": eta,
    "cost": cost,
    "pickup_time": pickup_time,
    "drive_time": drive_time,
    "traffic_factor": traffic_factor,
    "traffic_level": traffic_level
}