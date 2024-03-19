from enum import Enum, auto
import requests
import sys
import os
from dotenv.main import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")


class Categories(Enum):
    HOME = auto()
    GROCERY_STORE = auto()
    MUSEUM = auto()
    LIBRARY = auto()
    COFFEE_SHOP = auto()
    MEDICAL = auto()
    FASTFOOD = auto()
    RESTAURANT = auto()
    OUTDOOR_SPACES = auto()
    FOOD_AMERICAN = auto()
    FOOD_ASIAN = auto()
    FOOD_ITALIAN = auto()
    FOOD_MIDDLE_EASTERN = auto()
    FOOD_MEXICAN = auto()
    DESSERTS = auto()


class Location:
    def __init__(self, name, coordinates, categories):
        self.name = name
        self.coordinates = coordinates
        if not isinstance(categories, set):
            categories = {categories}
        self.categories = categories


class Walkability:
    def __init__(self, locations, home_address=None):
        self.locations = locations
        self.set_home_address(home_address)
        if self.home_address:
            self.locations.insert(0, Location("Home", home_address, Categories.HOME))
        else:
            # Default set home to Powell UCLA
            self.locations.insert(
                0,
                Location(
                    "Home", (34.067688225046496, -118.4421236503499), Categories.HOME
                ),
            )
        self.categories_to_indexes = {
            category: [
                i for i, loc in enumerate(self.locations) if category in loc.categories
            ]
            for category in Categories
        }
        self.coordinates_list = [location.coordinates for location in self.locations]
        self.distance_matrix, self.duration_matrix = get_walking_directions_matrices(
            self.coordinates_list, self.coordinates_list, API_KEY
        )
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
                distance_matrix_batch, duration_matrix_batch = (
                    get_walking_directions_matrices(
                        origin_coordinates, destination_coordinates, API_KEY
                    )
                )
                self.distance_matrix[i][j] = (
                    distance_matrix_batch[0][0]
                    if distance_matrix_batch
                    else float("inf")
                )
                self.duration_matrix[i][j] = (
                    duration_matrix_batch[0][0]
                    if duration_matrix_batch
                    else float("inf")
                )

    def combine_matrices(matrix_list):
        combined_matrix = []
        for matrix in matrix_list:
            combined_matrix.extend(matrix)
        return combined_matrix

    # shortest_walk_with_this_path
    # input a list of catergories where each catergoy is chosen in order
    # set previous to index 0
    # get a categories_to_indexes[catergories.(whatever)]
    def random_walk(self, order_of_destinations):
        prev = 0
        total_distance = 0
        total_steps = 0
        print(f"From {self.locations[0].name}")
        for categories in order_of_destinations:
            minimum_distance = sys.maxsize
            minimum_index = -1
            for index in self.categories_to_indexes[categories]:
                if self.duration_matrix[prev][index] < minimum_distance:
                    minimum_distance = self.duration_matrix[prev][index]
                    minimum_index = index
            print(f"To {self.locations[minimum_index].name}, {categories}")
            prev = minimum_index
            total_steps += 1
            total_distance += minimum_distance
        print(f"To {self.locations[0].name}")
        total_steps += 1
        total_distance += self.duration_matrix[prev][0]
        average_distance_per_step = total_distance / total_steps
        return average_distance_per_step

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
        # recalculate matrix for the top and across rows


def get_walking_directions_matrices(
    origin_coordinates, destination_coordinates, api_key
):
    origin_locations_str = "|".join(
        [f"{coordinate[0]},{coordinate[1]}" for coordinate in origin_coordinates]
    )
    destination_coordinates_locations_str = "|".join(
        [f"{coordinate[0]},{coordinate[1]}" for coordinate in destination_coordinates]
    )
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

        if data["status"] == "OK":
            # Extract latitude and longitude from the response
            location = data["results"][0]["geometry"]["location"]
            latitude = float(location["lat"])
            longitude = float(location["lng"])
            return latitude, longitude
        else:
            # If status is not OK, print the status and return None
            print("Geocoding failed with status:", data["status"])
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
        (40.712776, -74.005974),  # New York
    ]
    matrices = get_walking_directions_matrices(locations, locations, API_KEY)
    print(matrices)


# fmt: off
westwood_locations = [
    # Museums
    Location("Fowler", (34.07295131764241, -118.4430971751043), Categories.MUSEUM),
    Location("Hammer", (34.058969830022825, -118.44372707997064), Categories.MUSEUM),
    Location("UCLA Meteorite Gallery", (34.070011702924354, -118.44097314749347), Categories.MUSEUM),
    # Grocery Stores
    Location("Ralphs Fare Fresh", (34.063545627687496, -118.44452510013357), Categories.GROCERY_STORE),
    Location("Target Grocery", (34.063185517875056, -118.4439900903507), Categories.GROCERY_STORE),
    Location("Trader Joe's", (34.062465293659386, -118.44378946168212), Categories.GROCERY_STORE),
    Location("99 Ranch", (34.05639854677763, -118.44198380366491), Categories.GROCERY_STORE),
    # Location("Bristol Farms", (34.053766717882034, -118.44054596487344), Categories.GROCERY_STORE),
    # Location("Sprouts Farms Market", (34.05116251202463, -118.43853967818764), Categories.GROCERY_STORE),
    # Location("Whole Foods", (34.06127414017762, -118.44686576793366), Categories.GROCERY_STORE),
    # Location("Tochal Market", (34.05498065400885, -118.44126722505742), Categories.GROCERY_STORE),
    # Location("Shater Abbass Bakery & Market", (34.054599070362606, -118.4413963877709), Categories.GROCERY_STORE),
    # Location("Jordan Market", (34.05442172919427, -118.44124922547164), Categories.GROCERY_STORE),
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
    Location("UCLA Health Westwood Immediate Care", (34.065031025948734, -118.44637409160573), Categories.MEDICAL),
    # Coffee Shops
    Location("Starbucks at Broxton & Weyburn", (34.062813417291395, -118.44734600020898), Categories.COFFEE_SHOP),
    Location("Starbucks at Target", (34.06267483355451, -118.44405841000487), Categories.COFFEE_SHOP),
    Location("Starbucks at Westwood & Lindbrook", (34.05943358304032, -118.44475000526252), Categories.COFFEE_SHOP),
    Location("Ministry of Coffee", (34.06190603000339, -118.44396969102587), Categories.COFFEE_SHOP),
    Location("Bluestone Lane Westwood Coffee Shop", (34.062750970168416, -118.44494786860172), Categories.COFFEE_SHOP),
    Location("Bruin Buzz", (34.07038186224621, -118.44423400337479), Categories.COFFEE_SHOP),
    Location("Kerckhoff Coffee House", (34.07058891225211, -118.4434140771605), Categories.COFFEE_SHOP),
    Location("Dunkin'", (34.061743317848794, -118.44806453637115), {Categories.COFFEE_SHOP, Categories.DESSERTS}),
    # Fast Food
    Location("In-N-Out Burger", (34.0678046489839, -118.44676173368809), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("Taco Bell", (34.06288685898035, -118.44671980255414), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("Chick-fil-A", (34.063532040390264, -118.44512449939936), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("Chipotle Mexican Grill", (34.06116982000721, -118.44633039784706), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("CAVA", (34.061216789951025, -118.44634902374378), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("Subway at Ronald Raegan", (34.06654648085844, -118.446500273193), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("Subway at Court of Sciences", (34.06829417589296, -118.44224648935402), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("Subway at Westwood Blvd", (34.05936160936182, -118.44478682399304), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("Lamonica's NY Pizza", (34.06089576901573, -118.44684549163996), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("Egg Tuck", (34.06103780839104, -118.44741923367974), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("Jersey Mike's Subs", (34.061716847472674, -118.4440020419062), {Categories.RESTAURANT, Categories.FASTFOOD}),
    Location("Pinches Tacos", (34.061563011594025, -118.44410863136186), {Categories.RESTAURANT, Categories.FASTFOOD, Categories.FOOD_MEXICAN}),
    Location("Denny's", (34.06027927011324, -118.44302735472495), {Categories.RESTAURANT, Categories.FASTFOOD}),
    # Restaurants
    Location("BJ's Restaurant & Brewhouse", (34.06291014508286, -118.4472550323028), {Categories.RESTAURANT, Categories.FOOD_AMERICAN}),
    Location("Mr. Noodle", (34.06299772320804, -118.44684412060222), {Categories.RESTAURANT, Categories.FOOD_ASIAN}),
    Location("HIBACHI PAPI", (34.06313892201584, -118.44682171446215), {Categories.RESTAURANT, Categories.FOOD_ASIAN}),
    Location("Hangry Moon's", (34.06258989817038, -118.44803854823276), {Categories.RESTAURANT, Categories.FOOD_AMERICAN}),
    Location("Fat Sal's Deli", (34.06252046026004, -118.44804659485973), {Categories.RESTAURANT, Categories.FOOD_AMERICAN}),
    Location("Gushi", (34.062246407841556, -118.44791291042803), {Categories.RESTAURANT, Categories.FOOD_ASIAN}),
    Location("Northern Cafe Noodle House", (34.062355413149234, -118.4476311009415), {Categories.RESTAURANT, Categories.FOOD_ASIAN}),
    Location("Falafel Inc", (34.06301853362697, -118.44725000860093), {Categories.RESTAURANT, Categories.FOOD_MIDDLE_EASTERN}),
    Location("Enzo's Pizzeria", (34.06237826992287, -118.4466472515402), {Categories.RESTAURANT, Categories.FOOD_ITALIAN}),
    Location("Mr. Rice", (34.062227357845245, -118.44667805912319), {Categories.RESTAURANT, Categories.FOOD_ASIAN}),
    Location("California Pizza Kitchen at Westwood", (34.06227840165904, -118.44716696207378), {Categories.RESTAURANT, Categories.FOOD_AMERICAN}),
    Location("AMI Japanese Restaurant", (34.06154048254968, -118.4464999109244), {Categories.RESTAURANT, Categories.FOOD_ASIAN}),
    Location("Gogobop Korean Rice Bar", (34.06141176216899, -118.44647446118196), {Categories.RESTAURANT, Categories.FOOD_ASIAN}),
    Location("Northern Cafe Chinese Hotpot", (34.061337414963496, -118.44647580064209), {Categories.RESTAURANT, Categories.FOOD_ASIAN}),
    Location("The Boiling Crab", (34.06093920473367, -118.44458849942919), {Categories.RESTAURANT, Categories.FOOD_AMERICAN}),
    Location("Nick the Greek", (34.060168202294776, -118.44698701292269), {Categories.RESTAURANT, Categories.FOOD_MIDDLE_EASTERN}),
    Location("First Szechuan Wok", (34.060330828801945, -118.44283748451946), {Categories.RESTAURANT, Categories.FOOD_ASIAN}),
    Location("Frida Mexican Cuisine - Westwood", (34.0603290810503, -118.44266449166557), {Categories.RESTAURANT, Categories.FOOD_MEXICAN}),
    # Desserts
    Location("Diddy Riese", (34.06305744557268, -118.44685790656162), Categories.DESSERTS),
    Location("Insomnia Cookies", (34.062870400962396, -118.44561934288824), Categories.DESSERTS),
    Location("Just Boba Tea House", (34.06291876954755, -118.44814983023765), Categories.DESSERTS),
    Location("Junbi - Westwood",(34.06234935734012, -118.44762016564313),Categories.DESSERTS),
    Location("Meet Fresh", (34.06272148899564, -118.44626892944939), Categories.DESSERTS),
    Location("Sharetea", (34.06148083346903, -118.44647982944939), Categories.DESSERTS),
]
# fmt: on


if __name__ == "__main__":
    a = Walkability(westwood_locations)

    # fmt: off
    routes = [
        [Categories.COFFEE_SHOP, Categories.LIBRARY, Categories.FASTFOOD, Categories.LIBRARY],
        [Categories.COFFEE_SHOP, Categories.LIBRARY, Categories.GROCERY_STORE],
        [Categories.MUSEUM, Categories.COFFEE_SHOP, Categories.OUTDOOR_SPACES, Categories.RESTAURANT],
        [Categories.FOOD_AMERICAN, Categories.DESSERTS, Categories.COFFEE_SHOP, Categories.OUTDOOR_SPACES],
        [Categories.MEDICAL, Categories.GROCERY_STORE],
        [Categories.FOOD_MEXICAN, Categories.OUTDOOR_SPACES, Categories.RESTAURANT, Categories.DESSERTS], 
        [Categories.LIBRARY, Categories.COFFEE_SHOP, Categories.FOOD_ASIAN],
        [Categories.OUTDOOR_SPACES, Categories.COFFEE_SHOP, Categories.FOOD_MEXICAN],
        [Categories.FOOD_MIDDLE_EASTERN, Categories.DESSERTS, Categories.COFFEE_SHOP, Categories.LIBRARY],
        [Categories.RESTAURANT, Categories.COFFEE_SHOP, Categories.MUSEUM, Categories.OUTDOOR_SPACES],
    ]
    # fmt: on

    route_total_dist = 0
    for route in routes:
        route_avg_dist = a.random_walk(route)
        print(f"avg_dist: {route_avg_dist} meters\n")
        route_total_dist += route_avg_dist
    print(f"avg_dist: {route_total_dist/len(routes)} meters")
