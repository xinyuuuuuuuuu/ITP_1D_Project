# app.py
# The Streamlit web app (user interface only), designed for a phone screen.
# Run it with:  streamlit run app.py
#
# Problem: the park is huge, so visitors find it hard to plan and navigate.
# Section 1 (Map)   - an interactive map that works like a directory.
# Section 2 (Route) - a short survey, then a suggested route of rides.
# The chat box at the bottom answers questions about the park.

import streamlit as st

import assistant
import data
import map_view
from park import (Park, Preferences, RouteRecommender,
                  get_route_minutes, get_wait_label)

st.set_page_config(page_title=data.PARK_NAME, page_icon="🎢", layout="centered")

# Make the page as narrow as a phone, even on a laptop screen.
st.markdown("""
<style>
@import url("https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&display=swap");
.block-container, [data-testid="stBottomBlockContainer"] {
    max-width: 480px;
    padding-left: 0.9rem;
    padding-right: 0.9rem;
}
.block-container { padding-top: 3.2rem; }

/* The chat box (the container with key="chatbar") is fixed to the bottom
   of the screen, so the page still opens at the top. */
.block-container { padding-bottom: 7rem; }
.st-key-chatbar {
    position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
    width: min(480px, 100%); padding: 0.6rem 0.9rem 1.1rem; z-index: 100;
    animation: none !important;
}

/* Game-style title lettering. */
h3 {
    font-family: "Rajdhani", "Segoe UI", sans-serif !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
/* The map gets a thin gold frame and a soft glow. */
[data-testid="stImage"] img {
    border-radius: 14px;
    box-shadow: 0 0 0 1px rgba(232, 198, 106, 0.4), 0 12px 40px rgba(111, 227, 225, 0.14);
}
/* New parts of the page rise into place, one after another. */
@keyframes rise { from { opacity: 0; transform: translateY(18px); } }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div {
    animation: rise 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) backwards;
}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(2) { animation-delay: 0.06s; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(3) { animation-delay: 0.12s; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(4) { animation-delay: 0.18s; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(5) { animation-delay: 0.24s; }
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(n+6) { animation-delay: 0.3s; }
/* Respect phones that have "reduce motion" switched on. */
@media (prefers-reduced-motion: reduce) {
    [data-testid="stVerticalBlock"] > div { animation: none !important; }
}
</style>
""", unsafe_allow_html=True)

WAIT_ICONS = {"short": "🟢", "medium": "🟡", "long": "🔴"}
MENU_CATEGORIES = ["Shops", "Services", "Amenities", "Emergency"]

# The park objects (see park.py).
park = Park()
recommender = RouteRecommender(park, data.SCORE_WEIGHTS)

# st.session_state remembers values while the visitor taps around.
DEFAULTS = {
    "view": "Map",                 # which section is open
    "category": "Rides",           # which directory category is open
    "zone": data.ENTRANCE_ZONE,    # where the visitor is
    "hour": data.DEFAULT_HOUR,
    "weather": data.WEATHER_OPTIONS[0],
    "preferences": None,           # survey answers (None = not answered yet)
    "messages": [],                # chat history
}
for key in DEFAULTS:
    if key not in st.session_state:
        st.session_state[key] = DEFAULTS[key]


def open_category(category):
    """Menu button was tapped: jump to the Map section, at that category."""
    st.session_state["view"] = "Map"
    st.session_state["category"] = category


def add_icon(category):
    return data.CATEGORY_ICONS[category] + " " + category


@st.dialog("Menu")
def show_menu():
    """The hamburger menu: shortcuts into the directory, contact at the bottom."""
    for category in MENU_CATEGORIES:
        # on_click changes the section first, then st.rerun() closes the menu.
        if st.button(add_icon(category), key="menu_" + category, width="stretch",
                     on_click=open_category, args=[category]):
            st.rerun()
    st.divider()
    st.markdown("**Contact**")
    for label in data.CONTACT:
        st.caption(f"{label}: {data.CONTACT[label]}")


def show_header():
    """Title on the left, hamburger menu on the right."""
    header = st.container(horizontal=True, horizontal_alignment="distribute",
                          vertical_alignment="center")
    header.markdown("### 🎢 USJ Guide")
    if header.button("☰", key="menu_button"):
        show_menu()


def show_conditions():
    """Where the visitor is, the time and the weather. Used by both sections."""
    zone = st.session_state["zone"]
    hour = st.session_state["hour"]
    weather = st.session_state["weather"]
    with st.expander(f"📍 {zone} · {hour}:00 · {weather}"):
        # key= links each widget to the value in st.session_state.
        st.selectbox("I am at", list(data.ZONES.keys()), key="zone")
        st.select_slider("Time of day (hour)", list(data.CROWD_BY_HOUR.keys()), key="hour")
        st.radio("Weather", data.WEATHER_OPTIONS, key="weather", horizontal=True)


def show_map_section():
    """Section 1: the interactive map and directory."""
    zone = st.session_state["zone"]
    hour = st.session_state["hour"]
    weather = st.session_state["weather"]
    # Use the Express Pass answer from the survey, if it has been answered.
    preferences = st.session_state["preferences"]
    has_express = preferences is not None and preferences.has_express

    search_text = st.text_input("Search", placeholder="🔍 Search rides, food, shops...",
                                label_visibility="collapsed")
    category = st.pills("Category", list(data.CATEGORY_ICONS.keys()), key="category",
                        format_func=add_icon, label_visibility="collapsed")

    # Typing in the search box searches everything; otherwise show one category.
    if search_text.strip() != "":
        matches = park.search(search_text)
    elif category is None:
        matches = park.places
    else:
        matches = park.get_places(category)
    nearest_first = park.sort_by_walk(matches, zone)

    # For every zone with a match, remember its icon and count the matches.
    match_icons = {}
    for minutes, place in nearest_first:
        if place.zone not in match_icons:
            match_icons[place.zone] = [data.CATEGORY_ICONS[place.category], 0]
        match_icons[place.zone][1] += 1
    st.image(map_view.build_map_svg(zone, match_icons, []), width="stretch")
    st.caption("Cyan rings: you are here · Gold badge: found here (with how many)")

    if len(nearest_first) == 0:
        st.warning("Nothing found. Try another word.")
    # The results scroll inside their own box, so the map stays on screen.
    with st.container(height=340):
        for minutes, place in nearest_first:
            with st.container(border=True):
                st.markdown(f"{data.CATEGORY_ICONS[place.category]} **{place.name}**")
                st.caption(f"{place.zone} · {minutes} min walk · {place.detail}")
                # Rides also show their queue right now.
                if place.category == "Rides":
                    if place.is_open(weather):
                        wait = place.get_wait(hour, has_express)
                        st.caption(f"{WAIT_ICONS[get_wait_label(wait)]} {wait} min queue at {hour}:00")
                    else:
                        st.caption("⛔ Closed because of the rain")


def show_survey():
    """Ask the visitor's preferences. The answers are saved in session_state."""
    st.markdown("**Tell us about your visit**")
    ride_names = []
    for ride in park.rides:
        ride_names.append(ride.name)

    # Inside a form, nothing reruns until the button is pressed.
    with st.form("survey"):
        interests = st.pills("What do you enjoy?", data.RIDE_TAGS, selection_mode="multi")
        favourites = st.multiselect("Must-do rides", ride_names)
        minutes_available = st.slider("Time you have (minutes)", 30, 480, 180, step=15)
        avoid_water = st.toggle("I don't want to get wet")
        has_express = st.toggle("I have an Express Pass")
        submitted = st.form_submit_button("Suggest my route", type="primary", width="stretch")
    if submitted:
        st.session_state["preferences"] = Preferences(
            interests, favourites, avoid_water, has_express, minutes_available)
        st.rerun()


def show_route_section(route):
    """Section 2: the survey first, then the suggested route."""
    preferences = st.session_state["preferences"]
    if preferences is None:
        show_survey()
        return

    zone = st.session_state["zone"]
    hour = st.session_state["hour"]
    weather = st.session_state["weather"]

    if len(route) == 0:
        st.warning("No ride fits. Try more time, other interests or another hour.")
    else:
        st.success(f"{len(route)} ride(s) in {get_route_minutes(route)} of your "
                   f"{preferences.minutes_available} minutes")
        st.image(map_view.build_map_svg(zone, {}, route), width="stretch")
        st.caption(f"Cyan rings: start · Gold: your route, in order · "
                   f"based on {hour}:00, {weather.lower()} weather")

    number = 1
    for step in route:
        with st.container(border=True):
            st.markdown(f"**{number}. {step.ride.name}**")
            if step.walk == 0:
                walk_text = "you are already here"
            else:
                walk_text = f"walk {step.walk} min: " + " → ".join(step.path)
            st.caption(f"🚶 {walk_text}")
            st.caption(f"{WAIT_ICONS[get_wait_label(step.wait)]} queue {step.wait} min · "
                       f"🎢 ride {step.ride.duration} min")
            if len(step.reasons) > 0:
                st.caption("Why: " + ", ".join(step.reasons))
        number += 1

    # Explain every must-do ride that is not in the route.
    planned_names = []
    for step in route:
        planned_names.append(step.ride.name)
    for name in preferences.favourites:
        if name not in planned_names:
            ride = park.find_ride(name)
            if not ride.is_open(weather):
                st.warning(f"{name} is closed because of the rain.")
            elif preferences.avoid_water and "water" in ride.tags:
                st.warning(f"{name} is skipped because you may get wet.")
            else:
                st.warning(f"Not enough time for {name}.")

    if st.button("Retake survey", width="stretch"):
        st.session_state["preferences"] = None
        st.rerun()


@st.dialog("💬 Park assistant")
def show_chat():
    """Show the last few chat messages in a pop-up."""
    for message in st.session_state["messages"][-6:]:
        st.chat_message(message["role"]).write(message["content"])
    if not assistant.is_model_configured():
        st.caption("Offline helper: answers come from simple keyword rules.")


# ---------- Main page ----------
show_header()
# The Map / Route switch under the title.
st.segmented_control("Section", ["Map", "Route"], key="view",
                     label_visibility="collapsed", width="stretch")
show_conditions()

# Work out the route here so that the chatbot can also talk about it.
route = []
if st.session_state["preferences"] is not None:
    route = recommender.recommend(st.session_state["preferences"], st.session_state["zone"],
                                  st.session_state["hour"], st.session_state["weather"])

if st.session_state["view"] == "Route":
    show_route_section(route)
else:
    show_map_section()

# The chat box stays at the bottom of the screen.
question = st.container(key="chatbar").chat_input("Ask the park assistant")
if question:
    with st.spinner("Thinking..."):
        answer, source = assistant.get_reply(
            question, st.session_state["messages"], park, st.session_state["zone"],
            st.session_state["hour"], st.session_state["weather"],
            st.session_state["preferences"], route)
    st.session_state["messages"].append({"role": "user", "content": question})
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    show_chat()
