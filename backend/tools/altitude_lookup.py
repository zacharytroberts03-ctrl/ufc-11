"""
Tool: altitude_lookup.py
Purpose: Return the elevation in feet for known UFC venue cities.
         Used by analysis_runner to feed Section 7.5 (high-altitude cardio penalty).

Usage:
    from altitude_lookup import lookup_altitude
    lookup_altitude("Denver, Colorado, USA")  # → 5280
    lookup_altitude("Las Vegas")              # → 2030
    lookup_altitude("Unknown City")           # → None

The lookup is intentionally a hardcoded dict — no scraping. Add new venues as
the UFC visits them. Cities below 4000 ft do not trigger the cardio penalty
in Rule 7.5, but they're still listed here for completeness.
"""

# Elevation in feet for cities the UFC has hosted events in
_VENUE_ALTITUDES = {
    # High-altitude (Rule 7.5 trigger — above 4000 ft)
    "denver": 5280,
    "mexico city": 7350,
    "salt lake city": 4226,
    "albuquerque": 5312,
    "calgary": 3438,
    "la paz": 11942,
    "quito": 9350,
    "bogota": 8612,

    # Sea-level / low-altitude (below the 4000 ft Rule 7.5 threshold)
    "las vegas": 2030,
    "los angeles": 305,
    "anaheim": 157,
    "san diego": 62,
    "phoenix": 1086,
    "houston": 80,
    "dallas": 430,
    "austin": 489,
    "new york": 33,
    "newark": 30,
    "boston": 141,
    "philadelphia": 39,
    "washington": 410,
    "miami": 6,
    "orlando": 82,
    "jacksonville": 16,
    "tampa": 48,
    "atlanta": 1050,
    "nashville": 597,
    "charlotte": 751,
    "raleigh": 315,
    "chicago": 594,
    "detroit": 600,
    "columbus": 902,
    "cleveland": 653,
    "pittsburgh": 1223,
    "minneapolis": 830,
    "st louis": 466,
    "kansas city": 910,
    "st paul": 837,
    "sacramento": 30,
    "san jose": 82,
    "san francisco": 52,
    "oakland": 43,
    "fresno": 308,
    "portland": 50,
    "seattle": 175,
    "vancouver": 230,
    "toronto": 250,
    "montreal": 233,
    "edmonton": 2192,
    "winnipeg": 783,
    "halifax": 476,
    "ottawa": 233,

    # International
    "london": 36,
    "manchester": 125,
    "liverpool": 230,
    "glasgow": 39,
    "dublin": 33,
    "paris": 115,
    "berlin": 112,
    "hamburg": 20,
    "stockholm": 92,
    "copenhagen": 79,
    "amsterdam": 7,
    "rotterdam": 0,
    "rome": 69,
    "milan": 400,
    "madrid": 2188,
    "barcelona": 39,
    "lisbon": 39,
    "warsaw": 374,
    "prague": 656,
    "moscow": 512,
    "istanbul": 100,
    "abu dhabi": 89,
    "dubai": 52,
    "riyadh": 2017,
    "tokyo": 131,
    "saitama": 56,
    "osaka": 56,
    "yokohama": 39,
    "seoul": 282,
    "busan": 30,
    "shanghai": 13,
    "beijing": 144,
    "macau": 23,
    "manila": 52,
    "singapore": 49,
    "kuala lumpur": 217,
    "bangkok": 5,
    "perth": 102,
    "sydney": 190,
    "melbourne": 102,
    "brisbane": 89,
    "adelaide": 164,
    "auckland": 643,
    "wellington": 102,
    "rio de janeiro": 16,
    "sao paulo": 2493,
    "curitiba": 3045,
    "belem": 33,
    "brasilia": 3494,
    "buenos aires": 82,
    "santiago": 1700,
    "lima": 502,
}


def lookup_altitude(venue_str: str) -> int | None:
    """
    Given a venue string (city + state + country, any format), return elevation in feet.
    Returns None if no city in the lookup table matches.

    Match is substring-based and case-insensitive — works for any input that
    contains a known city name.
    """
    if not venue_str or venue_str == "Unknown":
        return None
    s = venue_str.lower()
    # Longest match first so "salt lake city" beats "lake city" if both were keys
    for city in sorted(_VENUE_ALTITUDES.keys(), key=len, reverse=True):
        if city in s:
            return _VENUE_ALTITUDES[city]
    return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print('Usage: python tools/altitude_lookup.py "Venue String"')
        sys.exit(1)
    result = lookup_altitude(sys.argv[1])
    print(f"{sys.argv[1]} → {result} ft" if result else f"{sys.argv[1]} → not in lookup table")
