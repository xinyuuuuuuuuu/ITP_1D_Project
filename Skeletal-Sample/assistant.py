# assistant.py
# The park chatbot. No Streamlit here; test it with:  python assistant.py
#
# It can answer in two ways:
# 1. With a language model, through the `openai` library. The library can
#    talk to any OpenAI-compatible server, including a small language model
#    (SLM) running on your own laptop. It is switched on by environment
#    variables, so no key is ever written in the code:
#        OPENAI_API_KEY   - the key (any text for a local server)
#        OPENAI_BASE_URL  - only for a local server, e.g. http://localhost:11434/v1
#        PARK_AI_MODEL    - the model name (default below)
# 2. Without a model (or if the model cannot be reached), simple keyword
#    rules answer from the park data, so the app always works.

import os

import data
import park as park_module

DEFAULT_MODEL = "gpt-4o-mini"

# Words in a question -> what to look for in the directory.
# If the value is a category name, the whole category is used.
# Otherwise the value is searched for in the place names and details.
KEYWORDS = {
    "eat": "Food", "food": "Food", "hungry": "Food", "restaurant": "Food",
    "lunch": "Food", "dinner": "Food",
    "locker": "locker", "atm": "atm", "cash": "atm",
    "stroller": "stroller", "wheelchair": "wheelchair",
    "first aid": "Emergency", "hurt": "Emergency", "emergency": "Emergency",
    "lost": "Emergency", "injur": "Emergency",
}

# Words that are in many ride names, so they do not identify one ride.
COMMON_WORDS = ["ride", "park", "the", "and", "adventure", "flying"]


def mentions(question, word):
    """Return True if a word of the question starts with `word`.

    Looking at the start of words stops "eat" matching inside "weather".
    """
    return (" " + question).find(" " + word) != -1


def is_model_configured():
    """Return True if a key for a language model has been set."""
    return os.environ.get("OPENAI_API_KEY", "") != ""


def describe_route(route):
    """Return the route as numbered lines of text."""
    lines = []
    number = 1
    for step in route:
        lines.append(f"{number}. {step.ride.name} ({step.ride.zone}): walk {step.walk} min, "
                     f"queue {step.wait} min, ride {step.ride.duration} min")
        number += 1
    return "\n".join(lines)


def build_context(park, zone, hour, weather, preferences, route):
    """Write everything the model needs to know as one piece of text."""
    lines = [
        f"You are the friendly guide of the theme park {data.PARK_NAME}.",
        "Answer in at most 4 short sentences. Use only the facts below.",
        "Do not invent rides, places or times.",
        "",
        f"Now: {hour}:00, weather {weather}. The visitor is in {zone}.",
        "",
        "Rides (zone, queue now, open or closed):",
    ]
    for ride in park.rides:
        status = "open"
        if not ride.is_open(weather):
            status = "closed because of rain"
        lines.append(f"- {ride.name} ({ride.zone}), {ride.get_wait(hour)} min, "
                     f"{status}, tags: {ride.detail}")

    lines.append("")
    lines.append("Other places (category, zone):")
    for place in park.places:
        if place.category != "Rides":
            lines.append(f"- {place.name}: {place.category}, {place.zone}, {place.detail}")

    lines.append("")
    lines.append("Walking paths in minutes:")
    for zone_a, zone_b, minutes in data.PATHS:
        lines.append(f"- {zone_a} to {zone_b}: {minutes}")

    # The weights and the survey, so the model can explain the route.
    lines.append("")
    lines.append(f"Route score weights: {data.SCORE_WEIGHTS}")
    if preferences is None:
        lines.append("The visitor has not answered the route survey yet.")
    else:
        lines.append(f"Survey: interests {preferences.interests}, "
                     f"must-do {preferences.favourites}, "
                     f"avoid water {preferences.avoid_water}, "
                     f"time {preferences.minutes_available} min.")
        lines.append("Suggested route:")
        lines.append(describe_route(route))
    return "\n".join(lines)


def ask_model(question, history, context):
    """Send the question to the language model and return its answer."""
    # Imported here so the app still runs if openai is not installed.
    from openai import OpenAI

    client = OpenAI(timeout=20, max_retries=0)
    messages = [{"role": "system", "content": context}]
    for message in history:
        messages.append({"role": message["role"], "content": message["content"]})
    messages.append({"role": "user", "content": question})
    response = client.chat.completions.create(
        model=os.environ.get("PARK_AI_MODEL", DEFAULT_MODEL),
        messages=messages,
    )
    return response.choices[0].message.content


def offline_reply(question, park, zone, hour, weather, preferences, route):
    """Answer with simple keyword rules (no language model needed)."""
    question = question.lower()

    # Rule 1: looking for a kind of place -> the nearest ones.
    for keyword in KEYWORDS:
        if mentions(question, keyword):
            target = KEYWORDS[keyword]
            if target in data.CATEGORY_ICONS:
                matches = park.get_places(target)
            else:
                matches = park.search(target)
            nearest = park.sort_by_walk(matches, zone)[:3]
            lines = [f"Nearest to you in {zone}:"]
            for minutes, place in nearest:
                lines.append(f"- {place.name} ({place.zone}), {minutes} min walk")
            return "\n".join(lines)

    # Rule 2: asking about the route.
    if mentions(question, "route") or mentions(question, "plan") or mentions(question, "next"):
        if preferences is None:
            return "Open the Route tab and answer the short survey, then I can suggest a route."
        if len(route) == 0:
            return "No ride fits your time right now. Try more time in the Route tab."
        return "Your suggested route:\n" + describe_route(route)

    # Rule 3: a ride is named -> its queue right now.
    lines = []
    for ride in park.rides:
        for word in ride.name.lower().replace("-", " ").replace(":", " ").split():
            if len(word) >= 4 and word not in COMMON_WORDS and word in question:
                if ride.is_open(weather):
                    lines.append(f"- {ride.name} ({ride.zone}): "
                                 f"{ride.get_wait(hour)} min queue")
                else:
                    lines.append(f"- {ride.name}: closed because of the rain")
                break   # one line per ride is enough
    if len(lines) > 0:
        return f"At {hour}:00:\n" + "\n".join(lines)

    # Rule 4: weather.
    if mentions(question, "weather") or mentions(question, "rain") or mentions(question, "hot"):
        if weather == "Rainy":
            return "It is rainy, so outdoor rides are closed. Indoor rides are still open."
        if weather == "Hot":
            return "It is hot, so I favour indoor and water rides in your route."
        return "It is sunny. All rides are open."

    # Rule 5: queues in general -> the three shortest open queues.
    if mentions(question, "wait") or mentions(question, "queue") or mentions(question, "short"):
        open_rides = []
        for ride in park.rides:
            if ride.is_open(weather):
                open_rides.append(ride)

        def wait_of(ride):
            return ride.get_wait(hour)

        lines = [f"Shortest queues at {hour}:00:"]
        for ride in sorted(open_rides, key=wait_of)[:3]:
            lines.append(f"- {ride.name} ({ride.zone}): {wait_of(ride)} min")
        return "\n".join(lines)

    return ("I can help you find food, lockers or first aid, "
            "tell you the queue of a ride, or explain your route.")


def get_reply(question, history, park, zone, hour, weather, preferences, route):
    """Return (answer, source). source is "model" or "offline"."""
    if is_model_configured():
        try:
            context = build_context(park, zone, hour, weather, preferences, route)
            return ask_model(question, history, context), "model"
        except Exception:
            # The model is not reachable (no internet, wrong key, server off).
            # Fall back to the keyword rules so the visitor still gets help.
            pass
    answer = offline_reply(question, park, zone, hour, weather, preferences, route)
    return answer, "offline"


# ---------- Self-check ----------
if __name__ == "__main__":
    test_park = park_module.Park()
    recommender = park_module.RouteRecommender(test_park, data.SCORE_WEIGHTS)
    prefs = park_module.Preferences(["thrill"], ["Dino Splash Rapids"], False, 240)
    test_route = recommender.recommend(prefs, "Hollywood", 12, "Sunny")

    def ask(question, weather="Sunny", preferences=prefs, route=test_route):
        return offline_reply(question, test_park, "Jurassic Park", 12, weather,
                             preferences, route)

    assert "Hogsmeade Lockers" in ask("any lockers?")
    assert "First Aid Post" in ask("my friend is hurt")
    assert "108 min" in ask("how long is mario kart")
    assert "closed" in ask("is the flying dinosaur open", weather="Rainy")
    assert "1. Dino Splash Rapids" in ask("what is my route")
    assert "survey" in ask("what is my route", preferences=None, route=[])
    assert "Hogwarts Castle Tour" in ask("which queue is shortest")
    assert "I can help" in ask("hello")
    # "weather" contains "eat", but it must not be treated as a food question.
    assert "sunny" in ask("what's the weather like?")
    assert "outdoor rides are closed" in ask("what's the weather like?", weather="Rainy")
    assert "Discovery Restaurant" in ask("where can we eat?")

    # The context for the model mentions the weights and the route.
    context = build_context(test_park, "Hollywood", 12, "Sunny", prefs, test_route)
    assert "favourite" in context and "1. Dino Splash Rapids" in context

    # A model that cannot be reached must fall back to the offline rules.
    os.environ["OPENAI_API_KEY"] = "test"
    os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:9/v1"
    answer, source = get_reply("any lockers?", [], test_park, "Jurassic Park",
                               12, "Sunny", prefs, test_route)
    assert source == "offline" and "Hogsmeade Lockers" in answer

    print("All assistant checks passed.")
