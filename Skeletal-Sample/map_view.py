# map_view.py
# Draws the park map as an illustrated picture, in the style of a game map.
# No Streamlit here; test it with:  python map_view.py
# (python map_view.py <folder> also saves two example pictures there).
#
# The weighted graph in park.py decides the paths and the route.
# This file only decides how they LOOK: every zone gets a little landmark,
# every path becomes a winding footpath, and the route glows in gold.
# The picture is written as SVG text (SVG is the drawing language of web pages).

import random

import data

# ---------- Colours, size, and how data.py positions become pixels ----------
COLOUR_HERE = "#6fe3e1"      # cyan: where the visitor is
COLOUR_GOLD = "#e8c66a"      # gold: search results and the suggested route
MAP_WIDTH = 420
MAP_HEIGHT = 480
MAP_SCALE = 75               # pixels for 1 unit of x or y in data.ZONES
MAP_LEFT = 55                # pixel x of map position x = 0
MAP_BOTTOM = 410             # pixel y of map position y = 0
# The outline of the island, as an SVG path (a list of curve points).
ISLAND_SHAPE = ("M30 452 C2 410 2 320 14 262 C18 200 30 120 82 100 "
                "C125 62 175 28 245 32 C305 30 318 88 348 118 "
                "C404 138 416 210 402 262 C416 320 416 396 378 428 "
                "C330 462 265 466 205 462 C145 466 72 470 30 452 Z")
LAGOON = {"x": 195, "y": 220, "rx": 52, "ry": 28}

# ---------- The landmark of every zone ----------
# tint: the colour of the district.  art: a small drawing, about 40 pixels
# wide, standing on the point (0, 6). "{T}" is replaced by the tint.
LIGHT = "#eef3ee"
DEFAULT_LANDMARK = {
    "tint": "#9fb4b3",
    "art": '<path d="M-14 6L0 -18L14 6Z" fill="{T}" fill-opacity="0.7" stroke="#eef3ee" stroke-width="1.2"/>',
}
LANDMARKS = {
    "Hollywood": {"tint": "#c9a24d", "art":      # a globe on a stand
        '<circle cx="0" cy="-12" r="11" fill="{T}" fill-opacity="0.45" stroke="#eef3ee" stroke-width="1.4"/>'
        '<ellipse cx="0" cy="-12" rx="11" ry="4.2" fill="none" stroke="#eef3ee"/>'
        '<ellipse cx="0" cy="-12" rx="4.5" ry="11" fill="none" stroke="#eef3ee"/>'
        '<path d="M-16 -9Q0 -20 16 -9" fill="none" stroke="#e8c66a" stroke-width="2.2" stroke-linecap="round"/>'
        '<path d="M-6 6H6L4 0H-4Z" fill="#eef3ee"/>'},
    "Jurassic Park": {"tint": "#5fae7a", "art":  # a volcano and a palm tree
        '<path d="M-20 6L-6 -18L-2 -14L2 -18L16 6Z" fill="{T}" fill-opacity="0.6" stroke="#eef3ee" stroke-width="1.2" stroke-linejoin="round"/>'
        '<path d="M-6 -18L-2 -14L2 -18L4 -13L-1 -9L-7 -13Z" fill="#ef7a6d" fill-opacity="0.85"/>'
        '<circle class="pm-smoke" cx="-2" cy="-23" r="3" fill="#eef3ee" fill-opacity="0.5"/>'
        '<path d="M15 6Q14 -4 17 -10" fill="none" stroke="#eef3ee" stroke-width="1.4"/>'
        '<path d="M17 -10Q11 -14 8 -9M17 -10Q22 -15 25 -9M17 -10Q16 -17 11 -17M17 -10Q20 -17 24 -15" fill="none" stroke="#7fd08f" stroke-width="1.4" stroke-linecap="round"/>'},
    "Wizarding World of Harry Potter": {"tint": "#8f7fc9", "art":   # a castle
        '<rect x="-12" y="-10" width="24" height="16" fill="{T}" fill-opacity="0.6" stroke="#eef3ee" stroke-width="1.2"/>'
        '<rect x="-16" y="-16" width="7" height="22" fill="{T}" fill-opacity="0.8" stroke="#eef3ee" stroke-width="1.2"/>'
        '<rect x="9" y="-13" width="7" height="19" fill="{T}" fill-opacity="0.8" stroke="#eef3ee" stroke-width="1.2"/>'
        '<rect x="-3.5" y="-22" width="7" height="14" fill="{T}" fill-opacity="0.9" stroke="#eef3ee" stroke-width="1.2"/>'
        '<path d="M-17.5 -16L-12.5 -26L-7.5 -16ZM7.5 -13L12.5 -22L17.5 -13ZM-5 -22L0 -33L5 -22Z" fill="#eef3ee"/>'
        '<path d="M0 -33V-38l5 2l-5 2" fill="#e8c66a" stroke="#e8c66a" stroke-width="0.8"/>'
        '<path d="M-3 6V-1a3 3 0 0 1 6 0V6Z" fill="#12262b"/>'},
    "Super Nintendo World": {"tint": "#d9574f", "art":   # a big mushroom
        '<path d="M-7 6V-7H7V6Z" fill="#eef3ee" stroke="#eef3ee" stroke-linejoin="round"/>'
        '<path d="M-16 -6A16 15 0 0 1 16 -6Z" fill="{T}" stroke="#eef3ee" stroke-width="1.3"/>'
        '<circle cx="0" cy="-14" r="4" fill="#eef3ee"/><circle cx="-10" cy="-9" r="2.4" fill="#eef3ee"/>'
        '<circle cx="10" cy="-9" r="2.4" fill="#eef3ee"/>'
        '<path d="M-3 0V3M3 0V3" stroke="#12262b" stroke-width="1.4" stroke-linecap="round"/>'},
}

# ---------- The animations (CSS inside the picture) ----------
# Every animation only describes where an element comes FROM, so if a phone
# has "reduce motion" switched on, everything is simply shown in place.
MAP_STYLE = """<style>
.pm-pop, .pm-pulse, .pm-spin, .pm-smoke { transform-box: fill-box; transform-origin: center; }
.pm-pop { animation: pm-pop 0.5s cubic-bezier(.2,1.5,.4,1) backwards; }
.pm-pulse { animation: pm-pulse 2.2s ease-out infinite; }
.pm-bob { animation: pm-bob 1.4s ease-in-out infinite alternate; }
.pm-spin { animation: pm-spin 24s linear infinite; }
.pm-blink { animation: pm-blink 2.4s ease-in-out infinite alternate; }
.pm-smoke { animation: pm-smoke 3s ease-out infinite; }
.pm-wave { animation: pm-drift 7s ease-in-out infinite alternate; }
.pm-cloud { animation: pm-drift 38s ease-in-out infinite alternate; }
.pm-route { animation: pm-draw 0.55s ease-out backwards; }
.pm-flow { animation: pm-fade 0.4s ease backwards, pm-flow 1.3s linear infinite; }
@keyframes pm-pop { from { transform: scale(0); opacity: 0; } }
@keyframes pm-pulse { from { transform: scale(0.55); opacity: 0.9; } to { transform: scale(1.9); opacity: 0; } }
@keyframes pm-bob { to { transform: translateY(-5px); } }
@keyframes pm-spin { to { transform: rotate(360deg); } }
@keyframes pm-blink { from { opacity: 0.35; } }
@keyframes pm-smoke { from { transform: translateY(4px) scale(0.5); opacity: 0.8; } to { transform: translateY(-9px) scale(1.5); opacity: 0; } }
@keyframes pm-drift { to { transform: translateX(14px); } }
@keyframes pm-draw { from { stroke-dashoffset: 1; } }
@keyframes pm-fade { from { opacity: 0; } }
@keyframes pm-flow { to { stroke-dashoffset: -0.2; } }
@media (prefers-reduced-motion: reduce) { .pm-map * { animation: none !important; } }
</style>"""


def get_map_xy(zone):
    """Turn a zone's map position in data.py into pixels on the drawing."""
    info = data.ZONES[zone]
    x = MAP_LEFT + info["x"] * MAP_SCALE
    y = MAP_BOTTOM - info["y"] * MAP_SCALE
    return x, y


def get_landmark(zone):
    """Return the landmark of a zone (a plain tent if it has none yet)."""
    if zone in LANDMARKS:
        return LANDMARKS[zone]
    return DEFAULT_LANDMARK


def make_road(zone_a, zone_b, bend):
    """Return a gently curved footpath from zone_a to zone_b, as an SVG path.

    bend moves the middle of the path sideways, so it winds like a real
    footpath instead of being a straight line of a graph.
    """
    x1, y1 = get_map_xy(zone_a)
    x2, y2 = get_map_xy(zone_b)
    middle_x = (x1 + x2) / 2 - (y2 - y1) * bend
    middle_y = (y1 + y2) / 2 + (x2 - x1) * bend
    return f"M{x1} {y1}Q{round(middle_x, 1)} {round(middle_y, 1)} {x2} {y2}"


def make_all_roads():
    """Return {"A|B": path} for every walking path, in both directions."""
    roads = {}
    bends = [-0.16, 0, 0.16]
    index = 0
    for zone_a, zone_b, minutes in data.PATHS:
        bend = bends[index % 3]
        roads[zone_a + "|" + zone_b] = make_road(zone_a, zone_b, bend)
        # Walking back uses the same curve, so the bend is mirrored.
        roads[zone_b + "|" + zone_a] = make_road(zone_b, zone_a, -bend)
        index += 1
    return roads


ROADS = make_all_roads()


def is_on_land(x, y, scale):
    """Roughly test if a point is on the island (scale 1 = the coastline)."""
    dx = (x - 210) / (190 * scale)
    dy = (y - 248) / (208 * scale)
    return dx * dx + dy * dy < 1


def is_clear_spot(x, y):
    """A tree may only grow away from the zones and out of the lagoon."""
    for zone in data.ZONES:
        zone_x, zone_y = get_map_xy(zone)
        if abs(x - zone_x) < 30 and abs(y - zone_y) < 34:
            return False
    dx = (x - LAGOON["x"]) / (LAGOON["rx"] + 8)
    dy = (y - LAGOON["y"]) / (LAGOON["ry"] + 8)
    return dx * dx + dy * dy > 1


def build_base_art():
    """Draw everything that never changes: sea, island, paths, landmarks."""
    # The same "random" numbers every time, so the map always looks the same.
    rng = random.Random(7)
    gold = COLOUR_GOLD
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" class="pm-map" width="{MAP_WIDTH}" '
        f'height="{MAP_HEIGHT}" viewBox="0 0 {MAP_WIDTH} {MAP_HEIGHT}" '
        f'font-family="Rajdhani, Segoe UI, Helvetica, Arial, sans-serif">',
        MAP_STYLE,
        '<defs>',
        '<radialGradient id="pm-sea" cx="50%" cy="50%" r="75%">'
        '<stop offset="0" stop-color="#1b4350"/><stop offset="1" stop-color="#07121a"/></radialGradient>',
        '<linearGradient id="pm-land" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#35564f"/><stop offset="1" stop-color="#1e3335"/></linearGradient>',
        '<radialGradient id="pm-water" cx="50%" cy="40%" r="70%">'
        '<stop offset="0" stop-color="#2a6b7c"/><stop offset="1" stop-color="#123642"/></radialGradient>',
        '<filter id="pm-glow" x="-60%" y="-60%" width="220%" height="220%">'
        '<feGaussianBlur stdDeviation="3" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<filter id="pm-soft" x="-30%" y="-30%" width="160%" height="160%">'
        '<feGaussianBlur stdDeviation="9"/></filter>',
        # The map opens outwards from where the visitor is standing.
        '<clipPath id="pm-reveal"><circle cx="REVEAL_X" cy="REVEAL_Y" r="700">'
        '<animate attributeName="r" from="0" to="700" dur="1.1s" calcMode="spline" '
        'keyTimes="0;1" keySplines="0.3 0 0.2 1" fill="freeze"/></circle></clipPath>',
        '</defs>',
        f'<rect width="{MAP_WIDTH}" height="{MAP_HEIGHT}" rx="14" fill="url(#pm-sea)"/>',
        '<g clip-path="url(#pm-reveal)">',
    ]

    # Little waves on the sea, outside the island.
    waves = 0
    while waves < 9:
        x = rng.randint(16, MAP_WIDTH - 40)
        y = rng.randint(20, MAP_HEIGHT - 16)
        if not is_on_land(x, y, 1.1):
            svg.append(f'<path class="pm-wave" style="animation-delay:-{waves}s" d="M{x} {y}q4 -3 8 0t8 0" '
                       f'fill="none" stroke="{COLOUR_HERE}" stroke-opacity="0.3" stroke-linecap="round"/>')
            waves += 1

    # The island: glowing shallow water, a sandy shore, then the land.
    svg.append(f'<path d="{ISLAND_SHAPE}" fill="none" stroke="{COLOUR_HERE}" stroke-opacity="0.4" '
               f'stroke-width="7" filter="url(#pm-glow)"/>')
    svg.append(f'<path d="{ISLAND_SHAPE}" fill="url(#pm-land)" stroke="#d9cfa6" stroke-opacity="0.55" '
               f'stroke-width="2.5"/>')

    # A soft patch of colour on the ground of every district.
    for zone in data.ZONES:
        x, y = get_map_xy(zone)
        tint = get_landmark(zone)["tint"]
        svg.append(f'<ellipse cx="{x}" cy="{y}" rx="46" ry="40" fill="{tint}" fill-opacity="0.28" '
                   f'filter="url(#pm-soft)"/>')

    # The lagoon, with ripples that spread out.
    lagoon = LAGOON
    svg.append(f'<ellipse cx="{lagoon["x"]}" cy="{lagoon["y"]}" rx="{lagoon["rx"]}" ry="{lagoon["ry"]}" '
               f'fill="url(#pm-water)" stroke="#d9cfa6" stroke-opacity="0.45" stroke-width="1.5"/>')
    for delay in [0, 1.1]:
        svg.append(f'<ellipse class="pm-pulse" style="animation-delay:{delay}s" cx="{lagoon["x"]}" '
                   f'cy="{lagoon["y"]}" rx="20" ry="9" fill="none" stroke="{COLOUR_HERE}" stroke-opacity="0.5"/>')
    svg.append(f'<text x="{lagoon["x"]}" y="{lagoon["y"] + 3}" text-anchor="middle" font-size="8" '
               f'letter-spacing="3" fill="{COLOUR_HERE}" fill-opacity="0.7" font-style="italic">LAGOON</text>')

    # Trees, scattered where there is room.
    trees = 0
    while trees < 70:
        x = rng.randint(20, MAP_WIDTH - 20)
        y = rng.randint(40, MAP_HEIGHT - 24)
        if is_on_land(x, y, 0.86) and is_clear_spot(x, y):
            size = rng.choice([3, 3.6, 4.4])
            svg.append(f'<circle cx="{x}" cy="{y}" r="{size}" fill="#24484a"/>'
                       f'<circle cx="{x - 1}" cy="{y - 1.2}" r="{round(size * 0.6, 1)}" fill="#3d7468"/>')
            trees += 1

    # The footpaths: a dark edge first, then the sandy path on top of it.
    for zone_a, zone_b, minutes in data.PATHS:
        road = ROADS[zone_a + "|" + zone_b]
        svg.append(f'<path d="{road}" fill="none" stroke="#0e1d20" stroke-opacity="0.55" '
                   f'stroke-width="7" stroke-linecap="round"/>')
        svg.append(f'<path class="pm-road" d="{road}" fill="none" stroke="#d9cfa6" stroke-opacity="0.6" '
                   f'stroke-width="3" stroke-linecap="round"/>')

    # Every zone: a small plaza, its landmark, and its name on a banner.
    for zone in data.ZONES:
        x, y = get_map_xy(zone)
        landmark = get_landmark(zone)
        name = data.ZONES[zone]["short"].upper()
        banner = len(name) * 6.2 + 14
        svg.append(f'<ellipse cx="{x}" cy="{y + 6}" rx="21" ry="7.5" fill="#d9cfa6" fill-opacity="0.5" '
                   f'stroke="#0e1d20" stroke-opacity="0.4"/>')
        svg.append(f'<g transform="translate({x} {y})">' + landmark["art"].replace("{T}", landmark["tint"]) + '</g>')
        svg.append(f'<rect x="{x - banner / 2}" y="{y + 16}" width="{banner}" height="14" rx="7" '
                   f'fill="#0b1418" fill-opacity="0.78" stroke="{gold}" stroke-opacity="0.45" stroke-width="0.8"/>')
        svg.append(f'<text x="{x}" y="{y + 26.2}" text-anchor="middle" font-size="9.5" font-weight="600" '
                   f'letter-spacing="1.2" fill="{LIGHT}">{name}</text>')

    x, y = get_map_xy(data.ENTRANCE_ZONE)
    svg.append(f'<text x="{x}" y="{y + 42}" text-anchor="middle" font-size="7.5" letter-spacing="2" '
               f'fill="{gold}">▲ ENTRANCE</text>')

    # Drifting clouds, the frame corners, the title and the compass.
    svg.append('<ellipse class="pm-cloud" cx="300" cy="120" rx="70" ry="22" fill="#ffffff" '
               'fill-opacity="0.07" filter="url(#pm-soft)"/>')
    svg.append('<ellipse class="pm-cloud" style="animation-delay:-19s" cx="90" cy="400" rx="80" ry="24" '
               'fill="#ffffff" fill-opacity="0.06" filter="url(#pm-soft)"/>')
    svg.append(f'<path d="M12 30V12H30 M{MAP_WIDTH - 30} 12H{MAP_WIDTH - 12}V30 '
               f'M12 {MAP_HEIGHT - 30}V{MAP_HEIGHT - 12}H30 '
               f'M{MAP_WIDTH - 30} {MAP_HEIGHT - 12}H{MAP_WIDTH - 12}V{MAP_HEIGHT - 30}" '
               f'fill="none" stroke="{gold}" stroke-opacity="0.7" stroke-width="1.5"/>')
    svg.append(f'<text x="22" y="28" font-size="9" letter-spacing="2.5" fill="{gold}" '
               f'fill-opacity="0.85">PARK MAP</text>')
    svg.append(f'<g transform="translate({MAP_WIDTH - 34} 46)" fill="none" stroke="{gold}" '
               f'stroke-opacity="0.8"><circle r="11"/><path d="M0 -8L3 0L0 8L-3 0Z" '
               f'fill="{gold}" fill-opacity="0.8" stroke="none"/></g>')
    svg.append(f'<text x="{MAP_WIDTH - 34}" y="30" text-anchor="middle" font-size="8" fill="{gold}">N</text>')
    return "".join(svg)


# Drawn once, when the program starts, because it never changes.
BASE_ART = build_base_art()


def build_overlay(here, match_icons, route):
    """Draw what changes: the visitor, the search results and the route."""
    gold = COLOUR_GOLD
    cyan = COLOUR_HERE
    svg = []

    # --- The route: each walked path lights up in gold, one after another ---
    stop_numbers = {}       # zone -> list of step numbers, e.g. {"Hollywood": ["1", "3"]}
    segment = 0
    number = 1
    for step in route:
        if step.ride.zone not in stop_numbers:
            stop_numbers[step.ride.zone] = []
        stop_numbers[step.ride.zone].append(str(number))
        number += 1
        for i in range(len(step.path) - 1):
            road = ROADS[step.path[i] + "|" + step.path[i + 1]]
            delay = round(0.9 + segment * 0.45, 2)
            # pathLength="1" lets the animation "draw" the line from 0 to 1.
            svg.append(f'<path class="pm-route" style="animation-delay:{delay}s" d="{road}" pathLength="1" '
                       f'fill="none" stroke="{gold}" stroke-width="4" stroke-linecap="round" '
                       f'stroke-dasharray="1" filter="url(#pm-glow)"/>')
            # Small bright dashes that keep flowing in the walking direction.
            svg.append(f'<path class="pm-flow" style="animation-delay:{round(delay + 0.5, 2)}s, 0s" d="{road}" '
                       f'pathLength="1" fill="none" stroke="#fff8e0" stroke-width="1.6" '
                       f'stroke-linecap="round" stroke-dasharray="0.05 0.15"/>')
            segment += 1

    order = 0
    for zone in data.ZONES:
        x, y = get_map_xy(zone)

        if zone == here:
            # The visitor: cyan rings on the ground and a pointer that bobs.
            svg.append(f'<ellipse cx="{x}" cy="{y + 6}" rx="25" ry="9.5" fill="none" stroke="{cyan}" '
                       f'stroke-width="2" filter="url(#pm-glow)"/>')
            for delay in [0, 1.1]:
                svg.append(f'<ellipse class="pm-pulse" style="animation-delay:{delay}s" cx="{x}" cy="{y + 6}" '
                           f'rx="25" ry="9.5" fill="none" stroke="{cyan}" stroke-width="1.5"/>')
            svg.append(f'<path class="pm-bob" d="M{x - 6} {y - 46}H{x + 6}L{x} {y - 37}Z" fill="{cyan}" '
                       f'filter="url(#pm-glow)"/>')

        if zone in stop_numbers:
            # A stop on the route: gold diamond with the step number(s).
            delay = round(1.0 + order * 0.3, 2)
            numbers = "·".join(stop_numbers[zone])
            svg.append(f'<g transform="translate({x + 20} {y - 24})"><g class="pm-pop" '
                       f'style="animation-delay:{delay}s"><rect x="-9" y="-9" width="18" height="18" rx="3" '
                       f'transform="rotate(45)" fill="{gold}" filter="url(#pm-glow)"/>'
                       f'<text y="4" text-anchor="middle" font-size="12" font-weight="700" '
                       f'fill="#1a1608">{numbers}</text></g></g>')
            order += 1
        elif zone in match_icons:
            # A search result is here: gold ring on the ground and a badge.
            icon, count = match_icons[zone]
            delay = round(0.6 + order * 0.08, 2)
            svg.append(f'<ellipse cx="{x}" cy="{y + 6}" rx="23" ry="8.5" fill="none" stroke="{gold}" '
                       f'stroke-width="1.6" filter="url(#pm-glow)"/>')
            badge = (f'<circle r="10" fill="#0e181c" stroke="{gold}" stroke-width="1.6"/>'
                     f'<text y="3.6" text-anchor="middle" font-size="10">{icon}</text>')
            if count > 1:
                badge += (f'<circle cx="9" cy="-8" r="6" fill="{gold}"/><text x="9" y="-4.8" '
                          f'text-anchor="middle" font-size="9" font-weight="700" fill="#1a1608">{count}</text>')
            svg.append(f'<g transform="translate({x + 20} {y - 24})"><g class="pm-pop" '
                       f'style="animation-delay:{delay}s">{badge}</g></g>')
            order += 1
    return "".join(svg)


def build_map_svg(here, match_icons, route):
    """Return the whole map picture as SVG text.

    here        - the zone the visitor is in (cyan rings)
    match_icons - {zone: [icon, count]} for zones with a search result (gold badge)
    route       - list of RouteStep (glowing gold paths and numbered stops)
    """
    x, y = get_map_xy(here)
    # The map is revealed outwards from the visitor's position.
    base = BASE_ART.replace("REVEAL_X", str(x)).replace("REVEAL_Y", str(y))
    return base + build_overlay(here, match_icons, route) + "</g></svg>"


# ---------- Self-check ----------
if __name__ == "__main__":
    import sys

    from park import Park, Preferences, RouteRecommender

    # Map view: every zone is named, every path is a road, matches get a badge.
    map_svg = build_map_svg("Hollywood", {"Jurassic Park": ["🎢", 2]}, [])
    assert map_svg.startswith("<svg") and map_svg.endswith("</svg>")
    for zone in data.ZONES:
        assert data.ZONES[zone]["short"].upper() in map_svg, zone
    assert map_svg.count('class="pm-road"') == len(data.PATHS)
    assert map_svg.count('class="pm-route"') == 0          # no route yet
    assert ">🎢</text>" in map_svg and ">2</text>" in map_svg
    assert "REVEAL_X" not in map_svg
    assert len(ROADS) == 2 * len(data.PATHS)

    # Route view: one glowing path per walked road, every step number is drawn.
    park = Park()
    recommender = RouteRecommender(park, data.SCORE_WEIGHTS)
    preferences = Preferences(["thrill"], ["Dino Splash Rapids"], False, 240)
    route = recommender.recommend(preferences, "Hollywood", 12, "Sunny")
    route_svg = build_map_svg("Hollywood", {}, route)
    walked = 0
    for step in route:
        walked += len(step.path) - 1
    assert route_svg.count('class="pm-route"') == walked
    numbers_drawn = ""
    for part in route_svg.split('fill="#1a1608">')[1:]:
        numbers_drawn += part.split("<")[0] + "·"
    for number in range(1, len(route) + 1):
        assert str(number) in numbers_drawn.split("·"), number

    # Optional: python map_view.py <folder> saves both pictures there.
    if len(sys.argv) > 1:
        open(sys.argv[1] + "/map_preview.svg", "w", encoding="utf-8").write(map_svg)
        open(sys.argv[1] + "/route_preview.svg", "w", encoding="utf-8").write(route_svg)

    print("All map checks passed.")
