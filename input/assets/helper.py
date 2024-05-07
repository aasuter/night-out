import googlemaps
import pandas as pd
from serpapi import GoogleSearch
from datetime import datetime as dt
from os import environ
from dotenv import load_dotenv
load_dotenv()

def clean_input(data):
    return data.replace("'", "").replace('"', '')


# helper functions
def get_token(path):
    with open(path) as file:
        token = file.read()
    return token

def rm_zone(timestr):
    if (timestr[-1].isnumeric() == False) and (timestr[-2:] != "PM" and timestr[-2:] != "AM"):
        timestr = timestr[:-4]
    return timestr

def convert_time(timestr):
    timestr = rm_zone(timestr)
    weekdays = {"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"}
    formatstr = ""
    if timestr[0:3] in weekdays:
        formatstr += "%a, "
    if "AM" in timestr or "PM" in timestr:
        if ":" in timestr:
            formatstr += "%b %d, %I:%M %p"
        else:
            formatstr += "%b %d, %I %p"
    else:
        formatstr += "%b %d"
    date = dt.strptime(timestr, formatstr)
    date = date.replace(year = dt.now().year)
    return date

def split_time(timestr):
    timestr = rm_zone(timestr)
    timestr = timestr.split(" – ")
    if len(timestr) == 1:
        return convert_time(timestr[0]), None
    if "AM" not in timestr[0] and "PM" not in timestr[0]:
        if "AM" in timestr[1]:
            timestr[0] += " AM"
        elif "PM" in timestr[1]:
            timestr[0] += " PM"
    date1 = convert_time(timestr[0])
    if timestr[1].isnumeric():
        date2 = dt.strptime(timestr[1], "%d")
        date2 = date2.replace(year = date1.year,
                              month = date1.month)
    elif not timestr[1][0].isnumeric():
        date2 = convert_time(timestr[1])
    else:
        if ":" in timestr[1]:
            date2 = dt.strptime(timestr[1], "%I:%M %p")
        else:
            date2 = dt.strptime(timestr[1], "%I %p")
        date2 = date2.replace(year = date1.year,
                              month = date1.month,
                              day = date1.day)
    return date1, date2

def punt_esc(string):
    return string.encode().decode("unicode_escape").replace("\\", "")

# TODO: Figure out how to keep secrets SECRETS
def event_search_table(searches,
                    serp_token = environ["SERP_TOKEN"]):
    table = {
        "name": [],
        "time": [],
        "venue_name": [],
        "venue_address": [],
        "event_link": [],
        "venue_link": [],
        "maps_link": [],
        "ticket_link": [],
        "description": [],
        "venue_rating": [],
    }

    base_params = {
        "engine": "google_events",
        "hl": "en",
        "gl": "us",
        "api_key": serp_token
    }

    surface_serp_fields = {
        "title": "name",
        "address": "venue_address",
        "link": "event_link",
        "description": "description"
    }

    lvl2_serp_fields = {
        ("date", "when"): "time",
        ("event_location_map", "link"): "maps_link",
        ("venue", "name"): "venue_name",
        ("venue", "link"): "venue_link",
        ("venue", "rating"): "venue_rating"
    }

    for search in searches:
        search_params = base_params
        search_params["q"] = search
        serp_search = GoogleSearch(search_params)
        results = serp_search.get_dict()
        if "events_results" not in results:
            continue
        events = results["events_results"]
        for event in events:
            for field in surface_serp_fields:
                if field in event:
                    if field == "address":
                        adstr = punt_esc(", ".join(event[field]))
                        table[surface_serp_fields[field]].append(adstr)
                    else:
                        to_append = event[field]
                        if type(to_append) == type(""):
                            to_append = punt_esc(to_append)
                        table[surface_serp_fields[field]].append(to_append)
                else:
                    table[surface_serp_fields[field]].append(None)
            for field in lvl2_serp_fields:
                if (field[0] in event) and (field[1] in event[field[0]]):
                    to_append = event[field[0]][field[1]]
                    if (type(to_append) == type("")) and (field[0] != "date"):
                        to_append = punt_esc(to_append)
                    table[lvl2_serp_fields[field]].append(to_append)
                else:
                    table[lvl2_serp_fields[field]].append(None)
            if ("ticket_info" in event) and (len(event["ticket_info"]) > 0) and ("link" in event["ticket_info"][0]):
                table["ticket_link"].append(event["ticket_info"][0]["link"])
            else:
                table["ticket_link"].append(None)
    pdtable = pd.DataFrame(table).drop_duplicates()
    remove = []
    for index, row in pdtable.iterrows():
        try:
            split_time(row["time"])
        except:
            remove.append(index)
    pdtable = pdtable.drop(index = remove)
    pdtable.time = pdtable.time.apply(split_time)
    pdtable = pdtable.assign(
        start_time = lambda x: x.time.apply(lambda y: y[0]),
        end_time = lambda x: x.time.apply(lambda y: y[1])
    )
    pdtable = pdtable.drop(columns = "time")
    return pdtable

def format_event_table(table):
    n = len(table)
    if n < 8:
        sampled = table
    else:
        sampled = table.sample(n = 8)
    pass_str = ""
    for index, row in sampled.iterrows():
        pass_str += (f"Event Name: {row['name']}\\n"
                     f"  Event Venue: {row['venue_name']}\\n"
                     f"  Event Address: {row['venue_address']}\\n"
                     f"  Event Link: {row['event_link']}\\n"
                     f"  Venue Link: {row['venue_link']}\\n"
                     f"  Maps Link: {row['maps_link']}\\n"
                     f"  Ticket Link: {row['ticket_link']}\\n"
                     f"  Venue Rating: {row['venue_rating']}\\n"
                     f"  Event Start Time: {row['start_time']}\\n"
                     f"  Event End Time: {row['end_time']}\\n\\n")
    return pass_str

def format_place_table(table):
    n = len(table)
    if n < 8:
        sampled = table
    else:
        sampled = table.sample(n = 8)
    pass_str = ""
    for index, row in sampled.iterrows():
        pass_str += (f"Location Name: {row['name']}\\n"
                     f"  Location Address: {row['address']}\\n"
                     f"  Location Rating: {row['rating']}\\n"
                     f"  Location Price Level: {row['price_level']}")
    return pass_str

def place_search_table(searches,
                       gmaps_token = environ["GMAPS_TOKEN"]):
    place_table = {
        "name": [],
        "address": [],
        "lat": [],
        "lng": [],
        "rating": [],
        "price_level": []
    }

    surface_fields = {
        "name": "name",
        "formatted_address": "address",
        "rating": "rating",
        "price_level": "price_level"
    }

    gmaps = googlemaps.Client(gmaps_token)
    for search in searches:
        results = gmaps.places(query = search)
        if ("results" in results) and (len(results["results"]) > 0):
            for spot in results["results"]:
                for field in surface_fields:
                    if field in spot:
                        to_append = spot[field]
                        if type(to_append) == type(""):
                            to_append = punt_esc(to_append)
                        place_table[surface_fields[field]].append(to_append)
                    else:
                        place_table[surface_fields[field]].append(None)
                lat = spot["geometry"]["location"]["lat"]
                lng = spot["geometry"]["location"]["lng"]
                place_table["lat"].append(lat)
                place_table["lng"].append(lng)
    return pd.DataFrame(place_table).drop_duplicates()