from geopy.geocoders import Nominatim
import os
import openrouteservice as ors
import folium
import math
import requests
import re
import json
import geocoder
import time


def address_to_lat_long(address_detail, lat_long=True):
    locator = Nominatim(user_agent="myGeocoder")
    location = locator.geocode(address_detail)
    if lat_long:
        return location.latitude, location.longitude
    else:
        return location.longitude, location.latitude
    
def create_isochrone(long_lat, travel_mode, commute_minutes, draw_map=False):
    
    ors_api_key = os.getenv("ors_api_key")
    client = ors.Client(key=ors_api_key)
    commute_seconds = commute_minutes*60
    pc_isochrone = client.isochrones(
        locations=[long_lat],
        profile=travel_mode,
        range=[commute_seconds],
        validate=False
    )

    polygon_coords = pc_isochrone['features'][0]['geometry']['coordinates'][0]
    
    if draw_map:
        lat_long = (long_lat[1], long_lat[0])
        m = folium.Map(location=lat_long, tiles='cartodbpositron', zoom_start=11)
        folium.GeoJson(pc_isochrone, name='isochrone').add_to(m)
        folium.Marker(lat_long).add_to(m)
        #m.save("maps/map4.html")
        return m, polygon_coords
        
    else:
        return polygon_coords


def get_distance_mi(point1, point2):
    lon1, lat1 = point1
    lon2, lat2 = point2
    radius = 3959 # radius of the Earth in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c
    return d

def furthest_point_distance(point, polygon):
    all_distances = [get_distance_mi(point, polygon_point) for polygon_point in polygon]
    max_index = all_distances.index(max(all_distances))
    max_distance =  max(all_distances)
    furthest_point = polygon[max_index]
    return max_distance

def round_up_to_nearest(input_num, num_list):
    next_highest = None
    for num in num_list:
        if num > input_num:
            next_highest = num
            break
    if next_highest is None:
        return None
    else:
        return math.ceil(next_highest)

def get_postcode_id(postcode):
    dashed_postcode = postcode.replace(' ', '-')
    l = f"https://www.rightmove.co.uk/house-prices/{dashed_postcode}.html"
    html_text = requests.get(l).text
    data = re.search(r"__PRELOADED_STATE__ = ({.*?})<", html_text)
    data_js = json.loads(data.group(1))
    pc_location_id = data_js["searchLocation"]["locationId"]
    return pc_location_id

def address_to_long_lat_bing(address):
    bing_map_key=os.getenv("bing_map_key")
    try_count = 0
    max_tries = 5
    s_betw_tries = 5
    while try_count < max_tries:
        try:   
            g = geocoder.bing(address, key=bing_map_key)
            results = g.json
            longitude = results['lng']
            latitude = results['lat']
            return longitude, latitude
        except Exception as e:
            print(f"API call failed. Retrying in {s_betw_tries} seconds (try {try_count + 1}/{max_tries})")
            try_count += 1
            time.sleep(s_betw_tries)
    raise Exception("API call failed after multiple retries")

def is_point_inside_polygon(point, polygon):
    num_intersections = 0
    x, y = point

    # Iterate over each pair of adjacent vertices in the polygon
    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]

        # Check if the ray intersects with the line segment
        if ((y1 <= y < y2) or (y2 <= y < y1)) and (x < (x1 - x2) * (y - y2) / (y1 - y2) + x2):
            num_intersections += 1

    return num_intersections % 2 == 1

def polygon_filter(df, polygon_coords):
    in_or_out_list = []
    for index, row in df.iterrows():
        longitude = row['longitude']
        latitude = row['latitude']
        in_or_out = is_point_inside_polygon([longitude, latitude], polygon_coords)
        in_or_out_list.append(in_or_out)
    return in_or_out_list

def map_houses(long_lat, travel_mode, commute_minutes, houses_for_sale, rm_area):
    ors_api_key = os.getenv("ors_api_key")
    client = ors.Client(key=ors_api_key)
    commute_seconds = commute_minutes*60
    pc_isochrone = client.isochrones(
        locations=[long_lat],
        profile=travel_mode,
        range=[commute_seconds],
        validate=False
    )

    lat_long = (long_lat[1], long_lat[0])
    m = folium.Map(location=lat_long, tiles='cartodbpositron', zoom_start=11)
    folium.Marker(lat_long).add_to(m)
    folium.GeoJson(pc_isochrone, name='isochrone').add_to(m)
    
    # define the icon types for each category
    icon_dict = {"True": 'green', "False": 'red'}

    # add markers to the map based on the categorical column
    for index, row in houses_for_sale.iterrows():
        #home_color = icon_dict.get(row['in_polygon'])
        icon_col = 'green' if row['in_polygon'] else 'red'
        url = row['url']
        popup_content = f'<a href="{url}" target="_blank">View on Rightmove</a>'
        folium.Marker([row['latitude'], row['longitude']], icon=folium.Icon(icon='home', color=icon_col), popup=popup_content).add_to(m)

    folium.Circle(lat_long, radius=(rm_area*1609.34), popup="Rightmove search area").add_to(m)

    return m