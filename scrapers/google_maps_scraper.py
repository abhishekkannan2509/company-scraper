import googlemaps
from typing import Dict, List, Optional
import json
from datetime import datetime
from config.config import GOOGLE_MAPS_API_KEY, DEFAULT_LOCATION, DEFAULT_RADIUS
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import os

class GoogleMapsScraper:
    def __init__(self):
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("Google Maps API key not found. Please set it in your .env file.")
        self.gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        
        self.geocoder = Nominatim(user_agent="company_scraper")
    
    def search_company(self, company_name: str, location: Optional[Dict] = None) -> List[Dict]:
        """
        Search for a company using the Google Places API.
        
        Args:
            company_name (str): Name of the company to search for
            location (dict, optional): Dictionary containing lat and lng. Defaults to Dubai, UAE.
            
        Returns:
            List[Dict]: List of matching places
        """
        location = location or DEFAULT_LOCATION
        
        try:
            
            places_result = self.gmaps.places(
                company_name,
                location=location,
                radius=DEFAULT_RADIUS
            )
            
            return places_result.get('results', [])
        except Exception as e:
            print(f"Error searching for company: {str(e)}")
            return []
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific place.
        
        Args:
            place_id (str): Google Places ID
            
        Returns:
            Optional[Dict]: Detailed place information
        """
        try:
            
            place_details = self.gmaps.place(
                place_id,
                fields=[
                    
                    'name', 'place_id', 'url', 'website',
                    'formatted_address', 'adr_address', 'address_component',
                    'vicinity', 'plus_code',
                    
                    
                    'formatted_phone_number', 'international_phone_number',
                    
                    
                    'geometry', 'geometry/location', 'geometry/location/lat',
                    'geometry/location/lng', 'geometry/viewport',
                    'geometry/viewport/northeast', 'geometry/viewport/southwest',
                    
                    
                    'business_status', 'permanently_closed',
                    'opening_hours', 'current_opening_hours',
                    'secondary_opening_hours', 'utc_offset',
                    
                    
                    'rating', 'reviews', 'user_ratings_total',
                    'price_level',
                    
                    
                    'editorial_summary', 'type',
                    'photo', 'icon',
                    
                    
                    'wheelchair_accessible_entrance',
                    'curbside_pickup', 'delivery',
                    'dine_in', 'takeout',
                    
                    
                    'serves_beer', 'serves_wine',
                    'serves_breakfast', 'serves_lunch',
                    'serves_dinner', 'serves_brunch',
                    'serves_vegetarian_food',
                    
                    
                    'reservable'
                ]
            )
            
            return place_details.get('result')
        except Exception as e:
            print(f"Error getting place details: {str(e)}")
            return None
    
    def save_to_json(self, data: Dict, filename: Optional[str] = None) -> str:
        """
        Save the scraped data to a JSON file. If the file exists, it will append the new data.
        
        Args:
            data (Dict): Data to save
            filename (str, optional): Custom filename. Defaults to timestamp-based name.
            
        Returns:
            str: Path to the saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"company_data_{timestamp}.json"
            
        try:
            # Read existing data if file exists
            existing_data = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            existing_data = [existing_data]
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse existing JSON file {filename}. Starting fresh.")
                    existing_data = []
            
            # Append new data
            if isinstance(data, list):
                existing_data.extend(data)
            else:
                existing_data.append(data)
            
            # Write combined data back to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
            return filename
        except Exception as e:
            print(f"Error saving data to file: {str(e)}")
            return ""

    def validate_emirate(self, place_details: Dict, expected_emirate: str) -> Dict:
        """
        Validate if the place is located in the expected emirate using reverse geocoding.
        
        Args:
            place_details (Dict): Place details from Google Places API
            expected_emirate (str): Expected emirate name
            
        Returns:
            Dict: Validation result containing:
                - is_valid (bool): Whether the emirate matches
                - actual_emirate (str): The actual emirate found
                - confidence (str): Confidence level of the validation
        """
        if not place_details or 'geometry' not in place_details or 'location' not in place_details['geometry']:
            return {
                'is_valid': False,
                'actual_emirate': None,
                'confidence': 'low',
                'error': 'No coordinates available'
            }
        
        
        lat = place_details['geometry']['location']['lat']
        lng = place_details['geometry']['location']['lng']
        
        try:
            
            location = self.geocoder.reverse((lat, lng), language='en')
            if not location or not location.raw:
                return {
                    'is_valid': False,
                    'actual_emirate': None,
                    'confidence': 'low',
                    'error': 'No location data found',
                    'coordinates': {'latitude': lat, 'longitude': lng}
                }
            
            
            address = location.raw.get('address', {})
            
            
            
            found_emirate = None
            possible_keys = ['state', 'county', 'city']
            
            for key in possible_keys:
                if key in address:
                    value = address[key].lower()
                    
                    if value in ['dubai', 'abu dhabi', 'sharjah', 'ajman', 'umm al quwain', 'ras al khaimah', 'fujairah']:
                        found_emirate = value.title()
                        break
            
            
            
            if not found_emirate:
                full_address = location.address.lower()
                emirates = {
                    'dubai': 'Dubai',
                    'abu dhabi': 'Abu Dhabi',
                    'sharjah': 'Sharjah',
                    'ajman': 'Ajman',
                    'umm al quwain': 'Umm Al Quwain',
                    'ras al khaimah': 'Ras Al Khaimah',
                    'fujairah': 'Fujairah'
                }
                
                for emirate_key, emirate_name in emirates.items():
                    if emirate_key in full_address:
                        found_emirate = emirate_name
                        break
            
            
            confidence = 'high' if found_emirate else 'low'
            
            
            expected_emirate = expected_emirate.strip()
            print(f"Expected Emirate: {expected_emirate}, Found Emirate: {found_emirate}")
            return {
                'is_valid': found_emirate.lower().strip() == expected_emirate.lower().strip(),
                'actual_emirate': found_emirate,
                'confidence': confidence,
                'coordinates': {
                    'latitude': lat,
                    'longitude': lng
                },
                'full_address': location.address
            }
            
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            return {
                'is_valid': False,
                'actual_emirate': None,
                'confidence': 'low',
                'error': f'Geocoding error: {str(e)}',
                'coordinates': {'latitude': lat, 'longitude': lng}
            }
        except Exception as e:
            return {
                'is_valid': False,
                'actual_emirate': None,
                'confidence': 'low',
                'error': f'Unexpected error: {str(e)}',
                'coordinates': {'latitude': lat, 'longitude': lng}
            } 