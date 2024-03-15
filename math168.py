from enum import Enum, auto
import requests
from dotenv import load_dotenv
import os

API_KEY = os.getenv("API_KEY")

class Walkability:
    class Categories(Enum):
        HOME = auto()
        GROCERY_STORE = auto()
        MEUSUM = auto()
        LIBRARY = auto()
        COFFEE_SHOP = auto()
        MEDICAL = auto()
        RESTURANT = auto()
    
    class Location:
        def __init__(self, name, coordinates, category):
            self.name = name
            self.coordinates = coordinates
            self.category = category

    def __init__(self, locations, home_address = None):
        self.locations = locations
        self.set_home_address(home_address)
        if(self.home_address):
            self.locations.insert(0, self.Location("Home", home_address, self.Categories.HOME))
        else:
            self.locations.insert(0, self.Location("Home", (34.067688225046496, -118.4421236503499), self.Categories.HOME))
        self.categories_to_indexes = {category: [i for i, loc in enumerate(self.locations) if loc.category == category] for category in self.Categories}
        self.distance_matrix, self.duration_matrix = get_walking_directions_matrices(self.locations, API_KEY)


    def set_home_address(self, new_address):
        if isinstance(new_address, str):
            self.home_address = address_to_coordinates(new_address, API_KEY)
        elif isinstance(new_address, tuple) and len(new_address) == 2:
            if all(isinstance(elem, float) for elem in new_address):
                self.home_address = new_address
            else:
                self.home_address = None
        else:
            self.home_address = None

    def set_new_home_address(self, new_address):
        self.set_home_address(new_address)
        #recalculate matrix

def get_walking_directions_matrices(locations, api_key):
    locations_str = "|".join([f"{loc.coordinates[0]},{loc.coordinates[1]}" for loc in locations])
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={locations_str}&destinations={locations_str}&units=imperial&mode=walking&key={api_key}"
    print(url)
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200:
        return extract_matrices(data)
    else:
        print("Error:", data.get("error_message", "Unknown error"))
        return None

def address_to_coordinates(address, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK':
            # Extract latitude and longitude from the response
            location = data['results'][0]['geometry']['location']
            latitude = float(location['lat'])
            longitude = float(location['lng'])
            return latitude, longitude
        else:
            # If status is not OK, print the status and return None
            print("Geocoding failed with status:", data['status'])
            return None
    except Exception as e:
        print("An error occurred:", e)
        return None

def extract_matrices(directions_matrix):
    distance_matrix = []
    duration_matrix = []
    for row in directions_matrix["rows"]:
        distance_row = []
        duration_row = []
        for element in row["elements"]:
            distance_row.append(element["distance"]["value"])
            duration_row.append(element["duration"]["value"])
        distance_matrix.append(distance_row)
        duration_matrix.append(duration_row)
    return distance_matrix, duration_matrix
