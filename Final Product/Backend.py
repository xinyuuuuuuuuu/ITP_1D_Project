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
        self.base_wait = BaseWait
        self.duration = duration

    #Gets the queue time in minutes
    def GetWaiting(self,hour):
        return round(self.BaseWait * Information.CrowdByHour[hour])

    #Check open state with weather
    def IsOpen(self,weather):
        if weather == "Rainy" and not self.indoor:
            return False
        return True

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