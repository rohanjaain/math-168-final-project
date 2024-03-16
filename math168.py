from enum import Enum, auto
import requests
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")
class Categories(Enum):
    HOME = auto()
    GROCERY_STORE = auto()
    MEUSUM = auto()
    LIBRARY = auto()
    COFFEE_SHOP = auto()
    MEDICAL = auto()
    RESTURANT = auto()
    OUTDOOR_SPACES = auto()

class Location:
    def __init__(self, name, coordinates, category):
        self.name = name
        self.coordinates = coordinates
        self.category = category

class Walkability:
    def __init__(self, locations, home_address = None):
        self.locations = locations
        self.set_home_address(home_address)
        if(self.home_address):
            self.locations.insert(0, Location("Home", home_address, Categories.HOME))
        else:
            #Default set home to Powell UCLA
            self.locations.insert(0, Location("Home", (34.067688225046496, -118.4421236503499), Categories.HOME))
        self.categories_to_indexes = {category: [i for i, loc in enumerate(self.locations) if loc.category == category] for category in Categories}
        self.coordinates_list = [location.coordinates for location in self.locations]
        self.distance_matrix, self.duration_matrix = get_walking_directions_matrices(self.coordinates_list, self.coordinates_list, API_KEY)
        self.distance_matrix = None
        self.duration_matrix = None
        self.calculate_matrices()  # Added this line to calculate matrices during initialization

    # Added this method to calculate matrices using batches
    def calculate_matrices(self):
        num_locations = len(self.locations)
        self.distance_matrix = [[0] * num_locations for _ in range(num_locations)]
        self.duration_matrix = [[0] * num_locations for _ in range(num_locations)]

        for i in range(num_locations):
            origin_coordinates = [self.locations[i].coordinates]
            for j in range(num_locations):
                destination_coordinates = [self.locations[j].coordinates]
                distance_matrix_batch, duration_matrix_batch = get_walking_directions_matrices(origin_coordinates, destination_coordinates, API_KEY)
                self.distance_matrix[i][j] = distance_matrix_batch[0][0] if distance_matrix_batch else float('inf')
                self.duration_matrix[i][j] = duration_matrix_batch[0][0] if duration_matrix_batch else float('inf')

    def combine_matrices(matrix_list):
        combined_matrix = []
        for matrix in matrix_list:
            combined_matrix.extend(matrix)
        return combined_matrix

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
        #recalculate matrix for the top and across rows

def get_walking_directions_matrices(origin_coordinates, destination_coordinates, api_key):
    origin_locations_str = "|".join([f"{coordinate[0]},{coordinate[1]}" for coordinate in origin_coordinates])
    destination_coordinates_locations_str = "|".join([f"{coordinate[0]},{coordinate[1]}" for coordinate in destination_coordinates])
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin_locations_str}&destinations={destination_coordinates_locations_str}&units=imperial&mode=walking&key={api_key}"
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

# Test case for address_to_coordinates function
def test_address_to_coordinates():
    address = "UCLA"
    coordinates = address_to_coordinates(address, API_KEY)
    print(coordinates)

# Test case for get_walking_directions_matrices function
def test_get_walking_directions_matrices():
    locations = [
        (37.774929, -122.419416),  # San Francisco
        (34.052235, -118.243683),  # Los Angeles
        (40.712776, -74.005974),   # New York
    ]
    matrices = get_walking_directions_matrices(locations, locations, API_KEY)
    print(matrices)

westwood_locations = [
    # Museums
    Location("Fowler", (34.07295131764241, -118.4430971751043), Categories.MEUSUM),
    Location("Hammer", (34.058969830022825, -118.44372707997064), Categories.MEUSUM),
    Location("UCLA Metieoritte Gallery", (34.070011702924354, -118.44097314749347), Categories.MEUSUM),
    
    # Grocery Stores
    Location("Ralphs Fare Fresh", (34.063545627687496, -118.44452510013357), Categories.GROCERY_STORE),
    Location("Target Grocery", (34.063185517875056, -118.4439900903507), Categories.GROCERY_STORE),
    Location("Trader Joe's", (34.062465293659386, -118.44378946168212), Categories.GROCERY_STORE),
    Location("99 Ranch", (34.05639854677763, -118.44198380366491), Categories.GROCERY_STORE),
    Location("Bristol Farms", (34.053766717882034, -118.44054596487344), Categories.GROCERY_STORE),
    Location("Sprouts Farms Market", (34.05116251202463, -118.43853967818764), Categories.GROCERY_STORE),
    Location("Whole Foods", (34.06127414017762, -118.44686576793366), Categories.GROCERY_STORE),
    Location("Tochal Market", (34.05498065400885, -118.44126722505742), Categories.GROCERY_STORE),
    Location("Shater Abbass Bakery & Market", (34.054599070362606, -118.4413963877709), Categories.GROCERY_STORE),
    Location("Jordan Market", (34.05442172919427, -118.44124922547164), Categories.GROCERY_STORE),
    
    # # Parks/Outdoor Spaces
    Location("Franklin D. Murphy Sculpture Garden", (34.075054982302994, -118.43999402069396), Categories.OUTDOOR_SPACES),
    Location("Janns Steps", (34.072187186585474, -118.443604590362), Categories.OUTDOOR_SPACES),
    Location("UCLA Mathias Botanical Garden", (34.06657407849101, -118.4415245206948), Categories.OUTDOOR_SPACES),
    Location("Holmby Park", (34.072328951465416, -118.42965135371733), Categories.OUTDOOR_SPACES),
    Location("Westwood Gardens Park", (34.057350296959, -118.44163610041117), Categories.OUTDOOR_SPACES),
    Location("Westwood Park", (34.053292222987984, -118.44830587248427), Categories.OUTDOOR_SPACES),
    Location("Sunset Canyon Recreation Center", (34.07472519888769, -118.45154393662891), Categories.OUTDOOR_SPACES),

    # Libraries
    Location("Science and Engineering Library/Geology", (34.06919911706539, -118.44067281447126), Categories.LIBRARY),
    Location("UCLA Science and Engineering Library", (34.06890059753678, -118.44267488565191), Categories.LIBRARY),
    Location("UCLA Louise M. Darling Biomedical Library", (34.06637972401974, -118.44187405717965), Categories.LIBRARY),
    Location("Westwood Branch Library", (34.05788780880445, -118.44179397433243), Categories.LIBRARY),
    Location("Powell Library", (34.07158723542848, -118.44215434714495), Categories.LIBRARY),
    Location("UCLA Music Library", (34.070990212148736, -118.44035248308232), Categories.LIBRARY),
    Location("UCLA Rosenfeld Library", (34.074273788120244, -118.4435157555478), Categories.LIBRARY),
    Location("Charles E. Young Research Library", (34.07487078825886, -118.4414736429435), Categories.LIBRARY),

    # Medical
    Location("Ronald Raegan", (34.06568666470719, -118.44575099010206), Categories.MEDICAL),
    Location("Ashe Center", (34.07130232965063, -118.44475761899842), Categories.MEDICAL),
    Location("UCLA Health Westwood Immediate Care", (34.065031025948734, -118.44637409160573), Categories.MEDICAL)
    ]


a = Walkability(westwood_locations)

def get_dimensions(matrix):
    num_rows = len(matrix)
    num_columns = len(matrix[0]) if matrix else 0  # Assuming all rows have the same length
    
    return num_rows, num_columns

rows, columns = get_dimensions(a.distance_matrix)
print("Number of rows:", rows)
print("Number of columns:", columns)

def print_matrix(matrix):
    for row in matrix:
        print(" ".join(map(str, row)))

print_matrix(a.distance_matrix)
print_matrix(a.duration_matrix)
