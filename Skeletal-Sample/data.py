# data.py
# All the business data of the park lives in this one file.
# If a wait time, walking time, weight or description changes, change it here only.
# Note: the numbers are made up for this project, they are not official USJ data.

PARK_NAME = "Universal Studios Japan"
ENTRANCE_ZONE = "Hollywood"

# ---------- Zones (the nodes of the park graph) ----------
# x, y: where the zone is drawn on the map (y gets bigger towards the back).
# short: the label written on the map.
ZONES = {
    "Hollywood":                       {"x": 0, "y": 0, "short": "Hollywood"},
    "New York":                        {"x": 2, "y": 0, "short": "New York"},
    "San Francisco":                   {"x": 4, "y": 0.6, "short": "San Francisco"},
    "Minion Park":                     {"x": 3.2, "y": 1.6, "short": "Minion Park"},
    "Jurassic Park":                   {"x": 4, "y": 3, "short": "Jurassic Park"},
    "Amity Village":                   {"x": 2, "y": 2.6, "short": "Amity Village"},
    "Universal Wonderland":            {"x": 0, "y": 1.6, "short": "Wonderland"},
    "Wizarding World of Harry Potter": {"x": 0.6, "y": 3.4, "short": "Wizarding World"},
    "Super Nintendo World":            {"x": 2.4, "y": 4.4, "short": "Nintendo World"},
}

# ---------- Paths (the weighted edges of the park graph) ----------
# (zone A, zone B, minutes to walk). Paths work in both directions.
# Not every zone is joined to every other zone: there is a lagoon in the
# middle of the park, so visitors must walk around it.
PATHS = [
    ("Hollywood", "New York", 4),
    ("Hollywood", "Universal Wonderland", 5),
    ("New York", "San Francisco", 4),
    ("New York", "Minion Park", 5),
    ("San Francisco", "Minion Park", 3),
    ("Minion Park", "Jurassic Park", 4),
    ("San Francisco", "Jurassic Park", 6),
    ("Jurassic Park", "Amity Village", 4),
    ("Jurassic Park", "Super Nintendo World", 7),
    ("Amity Village", "Wizarding World of Harry Potter", 5),
    ("Universal Wonderland", "Amity Village", 6),
    ("Universal Wonderland", "Wizarding World of Harry Potter", 6),
    ("Wizarding World of Harry Potter", "Super Nintendo World", 6),
]

# ---------- Crowd level ----------
# How busy the park is at each hour (24-hour clock).
# The wait time of a ride = its base wait x the multiplier for that hour.
CROWD_BY_HOUR = {
    9: 0.5, 10: 0.8, 11: 1.0, 12: 1.2, 13: 1.3, 14: 1.3,
    15: 1.2, 16: 1.0, 17: 0.9, 18: 0.7, 19: 0.5, 20: 0.4,
}
DEFAULT_HOUR = 12

# With an Express Pass, the wait is only this fraction of the normal wait.
EXPRESS_WAIT_FACTOR = 0.3

# A wait up to SHORT_WAIT minutes is "short", up to MEDIUM_WAIT is "medium".
SHORT_WAIT = 20
MEDIUM_WAIT = 45

# ---------- Weather ----------
# In rain, outdoor rides are closed. On a hot day, indoor and water rides
# are more comfortable, so they get a bonus in the route score.
WEATHER_OPTIONS = ["Sunny", "Hot", "Rainy"]

# ---------- Rides ----------
# base_wait: queue time in minutes at a normal crowd level
# duration:  how long the ride itself takes in minutes
# tags:      matched against the answers of the survey
# indoor:    True if the ride (and its queue) is under a roof
RIDE_TAGS = ["thrill", "family", "kids", "water"]
RIDES = [
    {"name": "Mario Kart: Koopa's Challenge", "zone": "Super Nintendo World",
     "tags": ["family"], "indoor": True, "base_wait": 90, "duration": 5},
    {"name": "Yoshi's Adventure", "zone": "Super Nintendo World",
     "tags": ["kids", "family"], "indoor": False, "base_wait": 60, "duration": 5},
    {"name": "Mine Cart Madness", "zone": "Super Nintendo World",
     "tags": ["thrill"], "indoor": False, "base_wait": 80, "duration": 4},
    {"name": "Harry Potter and the Forbidden Journey",
     "zone": "Wizarding World of Harry Potter",
     "tags": ["thrill"], "indoor": True, "base_wait": 80, "duration": 5},
    {"name": "Flight of the Hippogriff", "zone": "Wizarding World of Harry Potter",
     "tags": ["family"], "indoor": False, "base_wait": 50, "duration": 2},
    {"name": "The Flying Dinosaur", "zone": "Jurassic Park",
     "tags": ["thrill"], "indoor": False, "base_wait": 75, "duration": 3},
    {"name": "Jurassic Park - The Ride", "zone": "Jurassic Park",
     "tags": ["thrill", "water"], "indoor": False, "base_wait": 45, "duration": 7},
    {"name": "JAWS", "zone": "Amity Village",
     "tags": ["family", "water"], "indoor": False, "base_wait": 35, "duration": 7},
    {"name": "Despicable Me Minion Mayhem", "zone": "Minion Park",
     "tags": ["family"], "indoor": True, "base_wait": 50, "duration": 5},
    {"name": "Freeze Ray Sliders", "zone": "Minion Park",
     "tags": ["kids"], "indoor": False, "base_wait": 20, "duration": 2},
    {"name": "Flying Snoopy", "zone": "Universal Wonderland",
     "tags": ["kids"], "indoor": False, "base_wait": 15, "duration": 2},
    {"name": "Elmo's Go-Go Skateboard", "zone": "Universal Wonderland",
     "tags": ["kids", "family"], "indoor": True, "base_wait": 20, "duration": 2},
    {"name": "Hollywood Dream - The Ride", "zone": "Hollywood",
     "tags": ["thrill"], "indoor": False, "base_wait": 60, "duration": 3},
    {"name": "Space Fantasy - The Ride", "zone": "Hollywood",
     "tags": ["thrill"], "indoor": True, "base_wait": 40, "duration": 5},
]

# ---------- Everything else in the directory ----------
# category decides where the place appears in the directory and the menu.
CATEGORY_ICONS = {
    "Rides": "🎢", "Food": "🍴", "Shops": "🛍️",
    "Services": "🛎️", "Amenities": "🚻", "Emergency": "🚑",
}
PLACES = [
    # Food
    {"name": "Kinopio's Cafe", "zone": "Super Nintendo World", "category": "Food", "detail": "Themed cafe"},
    {"name": "Three Broomsticks", "zone": "Wizarding World of Harry Potter", "category": "Food", "detail": "British"},
    {"name": "Discovery Restaurant", "zone": "Jurassic Park", "category": "Food", "detail": "Western"},
    {"name": "Snoopy's Backlot Cafe", "zone": "Universal Wonderland", "category": "Food", "detail": "Kids meals"},
    {"name": "Amity Landing Restaurant", "zone": "Amity Village", "category": "Food", "detail": "Fast food"},
    {"name": "Mel's Drive-In", "zone": "Hollywood", "category": "Food", "detail": "Burgers"},
    {"name": "Finnegan's Bar & Grill", "zone": "New York", "category": "Food", "detail": "Irish"},
    {"name": "Happiness Cafe", "zone": "San Francisco", "category": "Food", "detail": "Family dining"},
    # Shops
    {"name": "Universal Studios Store", "zone": "Hollywood", "category": "Shops", "detail": "Park souvenirs"},
    {"name": "1-UP Factory", "zone": "Super Nintendo World", "category": "Shops", "detail": "Nintendo goods"},
    {"name": "Honeydukes", "zone": "Wizarding World of Harry Potter", "category": "Shops", "detail": "Sweets"},
    {"name": "Ollivanders", "zone": "Wizarding World of Harry Potter", "category": "Shops", "detail": "Wands"},
    {"name": "Minion Marketplace", "zone": "Minion Park", "category": "Shops", "detail": "Minion goods"},
    {"name": "Jurassic Outfitters", "zone": "Jurassic Park", "category": "Shops", "detail": "Dinosaur goods"},
    # Services
    {"name": "Guest Services", "zone": "Hollywood", "category": "Services", "detail": "Tickets, questions, lost and found"},
    {"name": "Stroller & Wheelchair Rental", "zone": "Hollywood", "category": "Services", "detail": "Rental counter"},
    {"name": "Entrance Lockers", "zone": "Hollywood", "category": "Services", "detail": "Coin lockers"},
    {"name": "Hogsmeade Lockers", "zone": "Wizarding World of Harry Potter", "category": "Services", "detail": "Coin lockers"},
    {"name": "ATM", "zone": "New York", "category": "Services", "detail": "Cash machine"},
    # Amenities
    {"name": "Hollywood Restroom", "zone": "Hollywood", "category": "Amenities", "detail": "Restroom"},
    {"name": "Mushroom Kingdom Restroom", "zone": "Super Nintendo World", "category": "Amenities", "detail": "Restroom"},
    {"name": "Jurassic Restroom", "zone": "Jurassic Park", "category": "Amenities", "detail": "Restroom"},
    {"name": "Amity Restroom", "zone": "Amity Village", "category": "Amenities", "detail": "Restroom"},
    {"name": "Waterfront Restroom", "zone": "San Francisco", "category": "Amenities", "detail": "Restroom"},
    {"name": "Family Services", "zone": "Universal Wonderland", "category": "Amenities", "detail": "Baby care and nursing room"},
    {"name": "Smoking Area", "zone": "New York", "category": "Amenities", "detail": "Smoking area"},
    # Emergency
    {"name": "First Aid Centre", "zone": "New York", "category": "Emergency", "detail": "Nurse on duty"},
    {"name": "First Aid Post", "zone": "Jurassic Park", "category": "Emergency", "detail": "Basic first aid"},
    {"name": "Security Office", "zone": "Hollywood", "category": "Emergency", "detail": "Lost child, security"},
]

# ---------- Contact (shown at the bottom of the menu) ----------
# Placeholders for this project, not real USJ contact details.
CONTACT = {
    "Emergency hotline": "000-0000-0000",
    "Information centre": "000-1111-1111",
    "Email": "help@example.com",
    "Opening hours": "9:00 - 21:00",
}

# ---------- Route Ride Recommender (RRR) weights ----------
# The score of a ride = the things the visitor wants (added)
#                     - the time it costs (subtracted).
# A bigger weight makes that factor matter more.
SCORE_WEIGHTS = {
    "favourite": 100,    # the ride is on the visitor's must-do list
    "preference": 30,    # for every survey interest the ride matches
    "weather": 20,       # the ride is comfortable in today's weather
    "queue": 1,          # for every minute in the queue (subtracted)
    "walk": 1,           # for every minute of walking (subtracted)
}
