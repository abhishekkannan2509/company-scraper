"""
Configuration file for business legitimacy scoring weights.
"""


LEGITIMACY_WEIGHTS = {
    'name_match': 0.15,         
    'website_match': 0.15,      
    'contact_info': 0.15,       
    'location': 0.15,           
    'operational': 0.15,        
    'reviews': 0.15,            
    'completeness': 0.1,        
    'emirate_match': 0.05       
}


DISPLAY_WEIGHTS = {
    'name_match': 15,
    'website_match': 15,
    'contact_info': 15,
    'location': 15,
    'operational': 15,
    'reviews': 15,
    'completeness': 10,
    'emirate_match': 5
}


LEGITIMACY_THRESHOLDS = {
    'high': 0.8,        
    'moderate': 0.6,    
    'low': 0.4,         
    'very_low': 0.0     
}


COLOR_THRESHOLDS = {
    'green': 0.8,   
    'yellow': 0.6,  
    'red': 0.0      
}


REQUIRED_FIELDS = [
    'name',
    'formatted_address',
    'formatted_phone_number',
    'website',
    'current_opening_hours',
    'rating',
    'user_ratings_total'
] 