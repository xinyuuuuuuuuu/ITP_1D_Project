# park.py
# The "backend" of the app, written with classes (OOP). No Streamlit here,
# so it can be tested on its own by running:  python park.py
#
#   Place            - anything in the directory (shop, restroom, ...)
#   Ride(Place)      - a place that also has a queue
#   ParkGraph        - the zones joined by walking paths (a weighted graph)
#   Park             - the whole park: graph + all places
#   Preferences      - the visitor's survey answers
#   RouteStep        - one stop in a suggested route
#   RouteRecommender - the Ride Route Recommender (RRR)

import data


def get_wait_label(wait):
    """Turn a wait in minutes into the words short / medium / long."""
    if wait <= data.SHORT_WAIT:
        return "short"
    elif wait <= data.MEDIUM_WAIT:
        return "medium"
    else:
        return "long"


class Place:
    """Anything a visitor may look for in the park directory."""

    def __init__(self, name, zone, category, detail):
        self.name = name
        self.zone = zone
        self.category = category
        self.detail = detail


class Ride(Place):
    """A ride is a Place that also has tags, a queue and a ride time."""

    def __init__(self, name, zone, tags, indoor, base_wait, duration):
        # Reuse the Place setup, then add what only rides have.
        super().__init__(name, zone, "Rides", ", ".join(tags))
        self.tags = tags
        self.indoor = indoor
        self.base_wait = base_wait
        self.duration = duration

    def get_wait(self, hour):
        """Return the queue time in minutes at the given hour."""
        # Busy hours have a bigger multiplier, so the wait gets longer.
        return round(self.base_wait * data.CROWD_BY_HOUR[hour])

    def is_open(self, weather):
        """Outdoor rides close when it rains."""
        if weather == "Rainy" and not self.indoor:
            return False
        return True

    def suits_weather(self, weather):
        """Return True if this ride is extra comfortable in this weather."""
        if weather == "Hot":
            return self.indoor or "water" in self.tags
        if weather == "Rainy":
            return self.indoor
        return False

    def count_matches(self, interests):
        """Count how many of the visitor's interests this ride has."""
        count = 0
        for tag in interests:
            if tag in self.tags:
                count += 1
        return count


class ParkGraph:
    """A weighted graph: zones are the nodes, walking paths are the edges.

    self.paths is a dictionary of dictionaries, for example
    self.paths["Hollywood"]["Jurassic Park"] = 13   (minutes)
    """

    def __init__(self):
        self.paths = {}

    def add_zone(self, zone):
        if zone not in self.paths:
            self.paths[zone] = {}

    def add_path(self, zone_a, zone_b, minutes):
        """Join two zones. Visitors can walk in both directions."""
        self.add_zone(zone_a)
        self.add_zone(zone_b)
        self.paths[zone_a][zone_b] = minutes
        self.paths[zone_b][zone_a] = minutes

    def shortest_path(self, start, end):
        """Return (minutes, [zones on the way]) for the quickest walk.

        This is Dijkstra's algorithm:
        1. Every zone starts "infinitely far", except the start (0 minutes).
        2. Take the nearest zone we have not finished yet.
        3. See if going through it makes any neighbour closer.
        4. Repeat until we reach the end.
        """
        minutes_to = {}
        came_from = {}
        for zone in self.paths:
            minutes_to[zone] = float("inf")
        minutes_to[start] = 0
        finished = []

        while len(finished) < len(self.paths):
            # Step 2: find the nearest unfinished zone.
            current = None
            for zone in self.paths:
                if zone not in finished:
                    if current is None or minutes_to[zone] < minutes_to[current]:
                        current = zone
            if current == end or minutes_to[current] == float("inf"):
                break
            finished.append(current)

            # Step 3: update the neighbours of that zone.
            for neighbour in self.paths[current]:
                new_minutes = minutes_to[current] + self.paths[current][neighbour]
                if new_minutes < minutes_to[neighbour]:
                    minutes_to[neighbour] = new_minutes
                    came_from[neighbour] = current

        # Walk backwards from the end to rebuild the path.
        path = [end]
        while path[0] != start:
            path.insert(0, came_from[path[0]])
        return minutes_to[end], path


class Park:
    """The whole park: the graph, the rides and every other place."""

    def __init__(self):
        # Build the graph from the paths in data.py.
        self.graph = ParkGraph()
        for zone in data.ZONES:
            self.graph.add_zone(zone)
        for zone_a, zone_b, minutes in data.PATHS:
            self.graph.add_path(zone_a, zone_b, minutes)

        # Turn every dictionary in data.py into an object.
        self.rides = []
        for item in data.RIDES:
            self.rides.append(Ride(item["name"], item["zone"], item["tags"],
                                   item["indoor"], item["base_wait"], item["duration"]))
        self.places = list(self.rides)
        for item in data.PLACES:
            self.places.append(Place(item["name"], item["zone"],
                                     item["category"], item["detail"]))

    def get_places(self, category):
        """Return every place in one category, e.g. "Shops"."""
        matches = []
        for place in self.places:
            if place.category == category:
                matches.append(place)
        return matches

    def search(self, text):
        """Return the places whose name, detail or zone contains the text."""
        text = text.lower().strip()
        matches = []
        for place in self.places:
            words = (place.name + " " + place.detail + " " + place.zone).lower()
            if text in words:
                matches.append(place)
        return matches

    def find_ride(self, name):
        for ride in self.rides:
            if ride.name == name:
                return ride
        return None

    def sort_by_walk(self, places, from_zone):
        """Return a list of (minutes, place), nearest first."""
        pairs = []
        for place in places:
            minutes, path = self.graph.shortest_path(from_zone, place.zone)
            pairs.append((minutes, place))

        def minutes_of(pair):
            return pair[0]

        return sorted(pairs, key=minutes_of)


class Preferences:
    """The visitor's answers to the route survey."""

    def __init__(self, interests, favourites, avoid_water, minutes_available):
        self.interests = interests            # list of ride tags
        self.favourites = favourites          # list of ride names
        self.avoid_water = avoid_water        # True = skip rides that get you wet
        self.minutes_available = minutes_available


class RouteStep:
    """One stop in the route: walk there, queue, then ride."""

    def __init__(self, ride, path, walk, wait, score):
        self.ride = ride
        self.path = path          # zones walked through, start to finish
        self.walk = walk
        self.wait = wait
        self.score = score

    def total_minutes(self):
        return self.walk + self.wait + self.ride.duration


class RouteRecommender:
    """The Ride Route Recommender (RRR).

    It gives every ride a score from the weights in data.SCORE_WEIGHTS,
    then keeps picking the best-scoring ride that still fits in the time.
    """

    def __init__(self, park, weights):
        self.park = park
        self.weights = weights

    def is_candidate(self, ride, preferences, weather):
        """Decide if a ride should be considered at all."""
        if not ride.is_open(weather):
            return False
        if preferences.avoid_water and "water" in ride.tags:
            return False
        # Keep must-do rides, rides matching an interest, and keep
        # everything if the visitor chose no interests.
        if ride.name in preferences.favourites:
            return True
        if len(preferences.interests) == 0:
            return True
        return ride.count_matches(preferences.interests) > 0

    def score_ride(self, ride, preferences, walk, wait, weather):
        """Return the score. A higher score is a better next ride."""
        weights = self.weights
        score = 0
        if ride.name in preferences.favourites:
            score += weights["favourite"]
        score += weights["preference"] * ride.count_matches(preferences.interests)
        if ride.suits_weather(weather):
            score += weights["weather"]
        # Time spent queueing and walking makes the score lower.
        score -= weights["queue"] * wait
        score -= weights["walk"] * walk
        return score

    def rank_rides(self, preferences, from_zone, hour, weather, done_names):
        """Return a RouteStep for every candidate ride, best score first."""
        options = []
        for ride in self.park.rides:
            if ride.name in done_names:
                continue
            if not self.is_candidate(ride, preferences, weather):
                continue
            walk, path = self.park.graph.shortest_path(from_zone, ride.zone)
            wait = ride.get_wait(hour)
            score = self.score_ride(ride, preferences, walk, wait, weather)
            options.append(RouteStep(ride, path, walk, wait, score))

        def score_of(step):
            return step.score

        return sorted(options, key=score_of, reverse=True)

    def recommend(self, preferences, start_zone, hour, weather):
        """Build the route: a list of RouteStep that fits the visitor's time."""
        # shortcut: waits use the starting hour for the whole route,
        # recompute per step if routes get longer than about an hour.
        route = []
        done_names = []
        minutes_used = 0
        current_zone = start_zone
        while True:
            ranked = self.rank_rides(preferences, current_zone, hour, weather, done_names)
            # Take the best-scoring ride that still fits in the time left.
            chosen = None
            for step in ranked:
                if minutes_used + step.total_minutes() <= preferences.minutes_available:
                    chosen = step
                    break
            if chosen is None:
                break   # nothing fits any more
            route.append(chosen)
            done_names.append(chosen.ride.name)
            minutes_used += chosen.total_minutes()
            current_zone = chosen.ride.zone
        return route


def get_route_minutes(route):
    """Add up the time of every step in a route."""
    total = 0
    for step in route:
        total += step.total_minutes()
    return total


# ---------- Self-check ----------
# Run "python park.py" to test the logic without opening the web app.
if __name__ == "__main__":
    park = Park()
    graph = park.graph

    # Every place must be in a zone that exists.
    for place in park.places:
        assert place.zone in data.ZONES, place.name

    # 4 zones with 4 rides each.
    assert len(data.ZONES) == 4
    for zone in data.ZONES:
        assert len([ride for ride in park.rides if ride.zone == zone]) == 4, zone

    # Graph: every zone can be reached, and A->B takes as long as B->A.
    for zone_a in data.ZONES:
        for zone_b in data.ZONES:
            there, path = graph.shortest_path(zone_a, zone_b)
            back, path_back = graph.shortest_path(zone_b, zone_a)
            assert there == back and there < float("inf"), (zone_a, zone_b)
            assert path[0] == zone_a and path[-1] == zone_b
    assert graph.shortest_path("Hollywood", "Hollywood") == (0, ["Hollywood"])
    # No direct path: the quickest way to Jurassic Park is around the lagoon.
    assert graph.shortest_path("Hollywood", "Super Nintendo World") == (
        17, ["Hollywood", "Wizarding World of Harry Potter", "Super Nintendo World"])

    # Rides: busier hour = longer wait, rain closes outdoor.
    mario = park.find_ride("Mario Kart: Koopa's Challenge")
    dinosaur = park.find_ride("The Flying Dinosaur")
    assert mario.get_wait(11) == 90
    assert mario.get_wait(13) == 117
    assert mario.is_open("Rainy") and not dinosaur.is_open("Rainy")
    assert get_wait_label(20) == "short" and get_wait_label(46) == "long"

    # Directory: categories, search and nearest-first sorting.
    assert len(park.get_places("Rides")) == len(data.RIDES)
    assert len(park.get_places("Emergency")) == 3
    assert park.search("locker")[0].category == "Services"
    nearest = park.sort_by_walk(park.search("locker"), "Super Nintendo World")[0]
    assert nearest[1].name == "Hogsmeade Lockers" and nearest[0] == 6

    # Route: fits the time, no ride twice, the must-do ride comes first.
    recommender = RouteRecommender(park, data.SCORE_WEIGHTS)
    prefs = Preferences(["thrill"], ["Dino Splash Rapids"], False, 240)
    route = recommender.recommend(prefs, "Hollywood", 12, "Sunny")
    assert route[0].ride.name == "Dino Splash Rapids"
    assert get_route_minutes(route) <= 240
    names = []
    for step in route:
        assert step.ride.name not in names
        names.append(step.ride.name)
    assert "Wand Studio" not in names   # not a thrill ride

    # Rain: only indoor rides are suggested, so the route changes.
    rainy = recommender.recommend(prefs, "Hollywood", 12, "Rainy")
    assert len(rainy) > 0
    for step in rainy:
        assert step.ride.indoor
    assert "Dino Splash Rapids" not in [step.ride.name for step in rainy]

    # Avoid water: no water rides, even a must-do one.
    dry = Preferences(["thrill"], ["Dino Splash Rapids"], True, 240)
    for step in recommender.recommend(dry, "Hollywood", 12, "Sunny"):
        assert "water" not in step.ride.tags

    # Weights matter: if walking costs a lot, the nearest ride wins.
    anything = Preferences([], [], False, 240)
    normal_first = recommender.rank_rides(anything, "Jurassic Park", 12, "Sunny", [])[0]
    lazy = RouteRecommender(park, {"favourite": 100, "preference": 30,
                                   "weather": 20, "queue": 1, "walk": 50})
    lazy_first = lazy.rank_rides(anything, "Jurassic Park", 12, "Sunny", [])[0]
    assert normal_first.ride.zone != "Jurassic Park"
    assert lazy_first.ride.zone == "Jurassic Park"

    # No time means an empty route.
    no_time = Preferences([], [], False, 0)
    assert recommender.recommend(no_time, "Hollywood", 12, "Sunny") == []

    print("All park checks passed.")
