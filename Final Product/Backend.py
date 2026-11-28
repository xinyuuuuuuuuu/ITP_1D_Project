import Information


#Prints the waiting duration
def WaitingTime(wait):
    if wait <= Information.ShortWait:
        return "short"
    elif wait <= Information.MediumWait:
        return "medium"
    else:
        return "long"

#Stuff in the park directory
class Place:
    def __init__(self,name,zone,category,info):
        self.name = name
        self.zone = zone
        self.category = category
        self.info = info

#Contains the tags, queue and ride time
class Ride(Place):
    def __init__(self,name,zone,tags,indoor,BaseWait,duration):
        #Reuse the Place setup, then add what only rides have.
        super().__init__(name, zone, "Rides", ", ".join(tags))
        self.tags = tags
        self.indoor = indoor
        self.BaseWait = BaseWait
        self.duration = duration

    #Gets the queue time in minutes
    def GetWaiting(self,hour):
        return round(self.BaseWait * Information.CrowdByHour[hour])

    #Check open state with weather
    def IsOpen(self,weather):
        if weather == "Rainy" and not self.indoor:
            return False
        return True

    #Check if the ride is extra comfortable in this weather
    def SuitsWeather(self,Weather):
        if Weather == "Hot":
            return self.indoor or "water" in self.tags
        if Weather == "Rainy":
            return self.indoor
        return False

    #Check the interest value of the ride by the customers
    def count_interest(self,interests):
        count = 0
        for tag in interests:
            if tag in self.tags:
                count+=1
        return count

#The weighted graph for the park
class ParkGraph:
    def __init__(self):
        self.paths = {}
    def add_zone(self,zone):
        if zone not in self.paths:
            self.paths[zone] = {}

    def add_path(self, ZoneA, ZoneB, minutes):
        self.add_zone(ZoneA)
        self.add_zone(ZoneB)
        self.paths[ZoneA][ZoneB] = minutes
        self.paths[ZoneB][ZoneA] = minutes

#INSERT DJIKSTRA'S ALGORITHM
    def shortest_path(self, start, end):
        MinutesTo = {}
        came_from = {}
        for zone in self.paths:
            MinutesTo[zone] = float("inf")
        MinutesTo[start] = 0
        finished = []

        while len(finished) < len(self.paths):
            # Step 2: find the nearest unfinished zone.
            current = None
            for zone in self.paths:
                if zone not in finished:
                    if current is None or MinutesTo[zone] < MinutesTo[current]:
                        current = zone
            if current == end or MinutesTo[current] == float("inf"):
                break
            finished.append(current)

            # Step 3: update the neighbours of that zone.
            for neighbour in self.paths[current]:
                new_minutes = MinutesTo[current] + self.paths[current][neighbour]
                if new_minutes < MinutesTo[neighbour]:
                    MinutesTo[neighbour] = new_minutes
                    came_from[neighbour] = current

        # Walk backwards from the end to rebuild the path.
        path = [end]
        while path[0] != start:
            path.insert(0, came_from[path[0]])
        return MinutesTo[end], path

class Park:
    def __init__(self):
        self.graph = ParkGraph()
        for zone in Information.Zones:
            self.graph.add_zone(zone)
        for ZoneA, ZoneB, minutes in Information.Paths:
            self.graph.add_path(ZoneA, ZoneB, minutes)

        self.rides = []
        for item in Information.Rides:
            self.rides.append(Ride(item["name"], item["zone"], item["tags"],
                                   item["indoor"], item["base_wait"], item["duration"]))
        self.places = list(self.rides)
        for item in Information.Places:
            self.places.append(Place(item["name"], item["zone"],
                                     item["category"], item["detail"]))

    def GetPlaces(self, category):
        matches = []
        for place in self.places:
            if place.category == category:
                matches.append(place)
        return matches

    def search(self, text):
        text = text.lower().strip()
        matches = []
        for place in self.places:
                words = (place.name + " " + place.info + " " + place.zone).lower()
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

#The visitor's answers to the route survey
class Preferences:
    def __init__(self, Interests, Favourites, AvoidWater, MinutesAvailable):
        self.Interests = Interests                 # list of ride tags
        self.Favourites = Favourites               # list of ride names
        self.AvoidWater = AvoidWater               # True = skip rides that get you wet
        self.MinutesAvailable = MinutesAvailable

#One stop in the route: walk there, queue, then ride
class RouteStep:
    def __init__(self, Ride, Path, Walk, Wait, Score):
        self.Ride = Ride
        self.Path = Path          # zones walked through, start to finish
        self.Walk = Walk
        self.Wait = Wait
        self.Score = Score

    def TotalMinutes(self):
        return self.Walk + self.Wait + self.Ride.duration

#The Ride Route Recommender (RRR): scores every ride, then keeps picking
#the best-scoring ride that still fits in the time
class RouteRecommender:
    def __init__(self, Park, Weights):
        self.Park = Park
        self.Weights = Weights

    #Decide if a ride should be considered at all
    def IsCandidate(self, Ride, Prefs, Weather):
        if not Ride.IsOpen(Weather):
            return False
        if Prefs.AvoidWater and "water" in Ride.tags:
            return False
        # Keep must-do rides, rides matching an interest, and keep
        # everything if the visitor chose no interests.
        if Ride.name in Prefs.Favourites:
            return True
        if len(Prefs.Interests) == 0:
            return True
        return Ride.count_interest(Prefs.Interests) > 0

    #Higher score = better next ride
    def ScoreRide(self, Ride, Prefs, Walk, Wait, Weather):
        Weights = self.Weights
        Score = 0
        if Ride.name in Prefs.Favourites:
            Score += Weights["favourite"]
        Score += Weights["preference"] * Ride.count_interest(Prefs.Interests)
        if Ride.SuitsWeather(Weather):
            Score += Weights["weather"]
        # Time spent queueing and walking makes the score lower.
        Score -= Weights["queue"] * Wait
        Score -= Weights["walk"] * Walk
        return Score

    #Return a RouteStep for every candidate ride, best score first
    def RankRides(self, Prefs, FromZone, Hour, Weather, DoneNames):
        Options = []
        for Ride in self.Park.rides:
            if Ride.name in DoneNames:
                continue
            if not self.IsCandidate(Ride, Prefs, Weather):
                continue
            Walk, Path = self.Park.graph.shortest_path(FromZone, Ride.zone)
            Wait = Ride.GetWaiting(Hour)
            Score = self.ScoreRide(Ride, Prefs, Walk, Wait, Weather)
            Options.append(RouteStep(Ride, Path, Walk, Wait, Score))

        def ScoreOf(Step):
            return Step.Score

        return sorted(Options, key=ScoreOf, reverse=True)

    #Build the route: a list of RouteStep that fits the visitor's time
    def Recommend(self, Prefs, StartZone, Hour, Weather):
        # shortcut: waits use the starting hour for the whole route,
        # recompute per step if routes get longer than about an hour.
        Route = []
        DoneNames = []
        MinutesUsed = 0
        CurrentZone = StartZone
        while True:
            Ranked = self.RankRides(Prefs, CurrentZone, Hour, Weather, DoneNames)
            # Take the best-scoring ride that still fits in the time left.
            Chosen = None
            for Step in Ranked:
                if MinutesUsed + Step.TotalMinutes() <= Prefs.MinutesAvailable:
                    Chosen = Step
                    break
            if Chosen is None:
                break   # nothing fits any more
            Route.append(Chosen)
            DoneNames.append(Chosen.Ride.name)
            MinutesUsed += Chosen.TotalMinutes()
            CurrentZone = Chosen.Ride.zone
        return Route

#Add up the time of every step in a route
def GetRouteMinutes(Route):
    Total = 0
    for Step in Route:
        Total += Step.TotalMinutes()
    return Total
