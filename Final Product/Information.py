# Information.py
# All the business data of the park lives in this one file.
# If a wait time, walking time, weight or description changes, change it here only.
# Note: the numbers (and some of the rides) are made up for this project,
# they are not official USJ data.

ParkName = "Universal Studios Japan"
EntranceZone = "Hollywood"

# ---------- Zones (the nodes of the park graph) ----------
# x, y: where the zone is drawn on the map (y gets bigger towards the back).
# short: the label written on the map.
Zones = {
    "Hollywood":                       {"x": 0, "y": 0, "short": "Hollywood"},
    "Jurassic Park":                   {"x": 4, "y": 3, "short": "Jurassic Park"},
    "Wizarding World of Harry Potter": {"x": 0.6, "y": 3.4, "short": "Wizarding World"},
    "Super Nintendo World":            {"x": 2.4, "y": 4.4, "short": "Nintendo World"},
}

# ---------- Paths (the weighted edges of the park graph) ----------
# (zone A, zone B, minutes to walk). Paths work in both directions.
# Not every zone is joined to every other zone: there is a lagoon in the
# middle of the park, so visitors must walk around it.
Paths = [
    ("Hollywood", "Jurassic Park", 13),
    ("Hollywood", "Wizarding World of Harry Potter", 11),
    ("Jurassic Park", "Super Nintendo World", 7),
    ("Wizarding World of Harry Potter", "Super Nintendo World", 6),
]

# ---------- Crowd level ----------
# How busy the park is at each hour (24-hour clock).
# The wait time of a ride = its base wait x the multiplier for that hour.
CrowdByHour = {
    9: 0.5, 10: 0.8, 11: 1.0, 12: 1.2, 13: 1.3, 14: 1.3,
    15: 1.2, 16: 1.0, 17: 0.9, 18: 0.7, 19: 0.5, 20: 0.4,
}
DefaultHour = 12

# A wait up to ShortWait minutes is "short", up to MediumWait is "medium".
ShortWait = 20
MediumWait = 45

# ---------- Weather ----------
# In rain, outdoor rides are closed. On a hot day, indoor and water rides
# are more comfortable, so they get a bonus in the route score.
WeatherOptions = ["Sunny", "Hot", "Rainy"]

# ---------- Rides ----------
# base_wait: queue time in minutes at a normal crowd level
# duration:  how long the ride itself takes in minutes
# tags:      matched against the answers of the survey
# indoor:    True if the ride (and its queue) is under a roof
RideTags = ["thrill", "family", "kids", "water"]
Rides = [
    {"name": "Mario Kart: Koopa's Challenge", "zone": "Super Nintendo World",
     "tags": ["family"], "indoor": True, "base_wait": 90, "duration": 5},
    {"name": "Yoshi's Adventure", "zone": "Super Nintendo World",
     "tags": ["kids", "family"], "indoor": False, "base_wait": 60, "duration": 5},
    {"name": "Mine Cart Madness", "zone": "Super Nintendo World",
     "tags": ["thrill"], "indoor": False, "base_wait": 80, "duration": 4},
    {"name": "Power-Up Band Key Challenge", "zone": "Super Nintendo World",
     "tags": ["kids", "family"], "indoor": False, "base_wait": 30, "duration": 10},
    {"name": "Harry Potter and the Forbidden Journey",
     "zone": "Wizarding World of Harry Potter",
     "tags": ["thrill"], "indoor": True, "base_wait": 80, "duration": 5},
    {"name": "Flight of the Hippogriff", "zone": "Wizarding World of Harry Potter",
     "tags": ["family"], "indoor": False, "base_wait": 50, "duration": 2},
    {"name": "Hogwarts Castle Tour", "zone": "Wizarding World of Harry Potter",
     "tags": ["family", "kids"], "indoor": True, "base_wait": 10, "duration": 15},
    {"name": "Wand Studio", "zone": "Wizarding World of Harry Potter",
     "tags": ["kids"], "indoor": True, "base_wait": 15, "duration": 10},
    {"name": "The Flying Dinosaur", "zone": "Jurassic Park",
     "tags": ["thrill"], "indoor": False, "base_wait": 75, "duration": 3},
    {"name": "Jurassic Park - The Ride", "zone": "Jurassic Park",
     "tags": ["thrill", "water"], "indoor": False, "base_wait": 45, "duration": 7},
    {"name": "Raptor Encounter", "zone": "Jurassic Park",
     "tags": ["kids", "family"], "indoor": False, "base_wait": 25, "duration": 10},
    {"name": "Dino Splash Rapids", "zone": "Jurassic Park",
     "tags": ["family", "water"], "indoor": False, "base_wait": 35, "duration": 7},
    {"name": "Hollywood Dream - The Ride", "zone": "Hollywood",
     "tags": ["thrill"], "indoor": False, "base_wait": 60, "duration": 3},
    {"name": "Space Fantasy - The Ride", "zone": "Hollywood",
     "tags": ["thrill"], "indoor": True, "base_wait": 40, "duration": 5},
    {"name": "Sesame Street 4-D Movie Magic", "zone": "Hollywood",
     "tags": ["kids", "family"], "indoor": True, "base_wait": 20, "duration": 20},
    {"name": "Minion Movie Coaster", "zone": "Hollywood",
     "tags": ["family"], "indoor": True, "base_wait": 50, "duration": 5},
]

# ---------- Everything else in the directory ----------
# category decides where the place appears in the directory.
CategoryIcons = {
    "Rides": "🎢", "Food": "🍴", "Services": "🛎️", "Emergency": "🚑",
}
Places = [
    # Food
    {"name": "Kinopio's Cafe", "zone": "Super Nintendo World", "category": "Food", "detail": "Themed cafe"},
    {"name": "Three Broomsticks", "zone": "Wizarding World of Harry Potter", "category": "Food", "detail": "British"},
    {"name": "Discovery Restaurant", "zone": "Jurassic Park", "category": "Food", "detail": "Western"},
    {"name": "Mel's Drive-In", "zone": "Hollywood", "category": "Food", "detail": "Burgers"},
    # Services
    {"name": "Guest Services", "zone": "Hollywood", "category": "Services", "detail": "Tickets, questions, lost and found"},
    {"name": "Stroller & Wheelchair Rental", "zone": "Hollywood", "category": "Services", "detail": "Rental counter"},
    {"name": "Entrance Lockers", "zone": "Hollywood", "category": "Services", "detail": "Coin lockers"},
    {"name": "Hogsmeade Lockers", "zone": "Wizarding World of Harry Potter", "category": "Services", "detail": "Coin lockers"},
    {"name": "ATM", "zone": "Hollywood", "category": "Services", "detail": "Cash machine"},
    # Emergency
    {"name": "First Aid Centre", "zone": "Hollywood", "category": "Emergency", "detail": "Nurse on duty"},
    {"name": "First Aid Post", "zone": "Jurassic Park", "category": "Emergency", "detail": "Basic first aid"},
    {"name": "Security Office", "zone": "Hollywood", "category": "Emergency", "detail": "Lost child, security"},
]

# ---------- Route Ride Recommender (RRR) weights ----------
# The score of a ride = the things the visitor wants (added)
#                     - the time it costs (subtracted).
# A bigger weight makes that factor matter more.
ScoreWeights = {
    "favourite": 100,    # the ride is on the visitor's must-do list
    "preference": 30,    # for every survey interest the ride matches
    "weather": 20,       # the ride is comfortable in today's weather
    "queue": 1,          # for every minute in the queue (subtracted)
    "walk": 1,           # for every minute of walking (subtracted)
}
