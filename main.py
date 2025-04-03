import argparse
from scrapers.google_maps_scraper import GoogleMapsScraper
from scrapers.google_search_scraper import GoogleSearchScraper
import json
from datetime import datetime
from typing import Dict, List
from difflib import SequenceMatcher
from utils.fuzzy_logic import calculate_fuzzy_score, calculate_fuzzy_weights
from config.weights import (
    LEGITIMACY_WEIGHTS,
    DISPLAY_WEIGHTS,
    LEGITIMACY_THRESHOLDS,
    COLOR_THRESHOLDS,
    REQUIRED_FIELDS
)
import csv
import re
import tldextract
from fuzzywuzzy import fuzz


ABBREVIATIONS = {
    "mgmt": "management",
    "llc": "",
    "ltd": "",
    "co.": "company",
    "corp": "corporation",
    "inc": "",
    "l.l.c":'',
    "plc": "",
    "gmbh": "",
    "pty": "",
    "pty.": "",
    "ltd.": "",
    "llc.": "",
    "inc.": "",
    "corp.": "",
    "&": "and",
    "fz": "free zone",
    "fzc": "free zone company",
}


BUSINESS_SUFFIXES = [
    "llc", "ltd", "inc", "plc", "gmbh", "pty", "corporation", "company",
    "group", "holdings", "holding", "limited", "incorporated"
]

def normalize_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[^\w\s]', ' ', name)
    
    
    name = re.sub(r'\s+', ' ', name)
    
    
    words = name.split()
    
    
    words = [word for word in words if word not in BUSINESS_SUFFIXES]
    
    
    normalized_words = [ABBREVIATIONS.get(word, word) for word in words]
    
    
    return " ".join(normalized_words).strip()

def extract_domain_name(url: str) -> str:
    try:
        
        extracted = tldextract.extract(url)
        
        
        domain = f"{extracted.domain}.{extracted.suffix}"
        
        
        domain_parts = domain.split('.')
        if len(domain_parts) > 1:
            main_domain = domain_parts[0]
            
            for suffix in BUSINESS_SUFFIXES:
                main_domain = re.sub(f"{suffix}$", "", main_domain)
            domain = f"{main_domain}.{domain_parts[1]}"
        
        return domain.lower()
    except Exception:
        return ""

def calculate_domain_similarity(company_name: str, domain: str) -> float:
    normalized_company = normalize_name(company_name)
    normalized_domain = normalize_name(domain)
    
    
    domain_parts = normalized_domain.split('.')
    
    
    if len(domain_parts) >= 2:
        second_level_domain = domain_parts[-2]  
        remaining_domain = '.'.join(domain_parts[:-2])  
    else:
        second_level_domain = domain_parts[0]
        remaining_domain = ""
    
    
    
    second_level_similarity = fuzz.token_set_ratio(normalized_company, second_level_domain)
    
    
    full_domain_similarity = fuzz.token_set_ratio(normalized_company, normalized_domain)
    
    
    second_level_partial = fuzz.partial_ratio(normalized_company, second_level_domain)
    full_domain_partial = fuzz.partial_ratio(normalized_company, normalized_domain)
    
    
    weighted_score = (
        (second_level_similarity * 0.5) +    
        (second_level_partial * 0.2) +       
        (full_domain_similarity * 0.2) +     
        (full_domain_partial * 0.1)          
    )
    
    
    if weighted_score > 0:  
        
        if second_level_partial > 30 or full_domain_partial > 30:
            
            weighted_score = max(weighted_score, 60)
            
            
            if second_level_partial > 50 or full_domain_partial > 50:
                weighted_score = min(weighted_score * 1.5, 95)  
    
    return weighted_score  

def calculate_name_similarity(name1: str, name2: str, weight_primary: float = 0.6, weight_secondary: float = 0.4) -> float:

    
    name1, name2 = normalize_name(name1), normalize_name(name2)
    
    words1 = name1.split()
    words2 = name2.split()

    if not words1 or not words2:
        return 0.0  

    
    primary1 = " ".join(words1[:2])
    secondary1 = " ".join(words1[2:])
    primary2 = " ".join(words2[:2])
    secondary2 = " ".join(words2[2:])

    
    primary_sim = SequenceMatcher(None, primary1, primary2).ratio()
    secondary_sim = SequenceMatcher(None, secondary1, secondary2).ratio()

    
    weighted_score = (primary_sim * weight_primary) + (secondary_sim * weight_secondary)
    return weighted_score

def calculate_email_similarity(email1: str, email2: str) -> float:
    
    email1 = email1.lower().strip()
    email2 = email2.lower().strip()
    
    
    try:
        local1, domain1 = email1.split('@')
        local2, domain2 = email2.split('@')
    except ValueError:
        return 0.0  
    
    
    local_similarity = SequenceMatcher(None, local1, local2).ratio()
    domain_similarity = SequenceMatcher(None, domain1, domain2).ratio()
    
    
    weighted_similarity = (local_similarity * 0.7) + (domain_similarity * 0.3)
    
    return weighted_similarity * 100  

def calculate_business_legitimacy(result: Dict, input_company_name: str) -> Dict:
    
    data = {}
    
    
    data['name_similarity'] = calculate_name_similarity(input_company_name, result.get('name', ''))
    
    
    website = result.get('website', '')
    website_similarity = 0
    if website and website.startswith('http'):
        domain = extract_domain_name(website)
        if domain:
            website_similarity = calculate_domain_similarity(input_company_name, domain) / 100  
    data['website_similarity'] = website_similarity
    
    
    contact_completeness = 0
    if result.get('formatted_phone_number'):
        contact_completeness += 0.5
    if website and website.startswith('http'):
        contact_completeness += 0.5
    data['contact_completeness'] = contact_completeness
    
    
    location_completeness = 0
    if result.get('formatted_address'):
        location_completeness += 0.5
    if result.get('geometry', {}).get('location'):
        location_completeness += 0.5
    data['location_completeness'] = location_completeness
    
    
    operational_completeness = 0
    if result.get('current_opening_hours'):
        operational_completeness += 0.5
    if result.get('business_status') == 'OPERATIONAL':
        operational_completeness += 0.5
    data['operational_completeness'] = operational_completeness
    
    
    review_score = 0
    rating = result.get('rating')
    reviews_count = result.get('user_ratings_total', 0)
    if rating and reviews_count > 0:
        
        rating_component = (rating / 5.0) * 0.7
        
        
        if reviews_count >= 100:
            review_count_component = 0.3
        elif reviews_count >= 50:
            review_count_component = 0.2
        elif reviews_count >= 25:
            review_count_component = 0.15
        elif reviews_count >= 10:
            review_count_component = 0.1
        else:
            review_count_component = 0.05
        
        review_score = rating_component + review_count_component
    data['review_score'] = review_score
    
    
    present_fields = sum(1 for field in REQUIRED_FIELDS if result.get(field))
    data['profile_completeness'] = present_fields / len(REQUIRED_FIELDS)
    
    
    emirate_confidence = 0
    if result.get('emirate_validation'):
        emirate_validation = result['emirate_validation']
        if emirate_validation.get('is_valid'):
            emirate_confidence = 1.0
        elif emirate_validation.get('confidence') == 'high':
            emirate_confidence = 0.5
    data['emirate_confidence'] = emirate_confidence
    
    
    weights = calculate_fuzzy_weights(data)
    total_score, legitimacy_level = calculate_fuzzy_score(data)
    
    return {
        'total_score': round(total_score, 2),
        'legitimacy_level': legitimacy_level,
        'breakdown': {factor: round(data[factor] * 100, 2) for factor in data},
        'weights': {factor: round(weight * 100, 2) for factor, weight in weights.items()}
    }

def format_company_summary(result: Dict, input_company_name: str, input_emirate: str = None, plain_text: bool = False) -> str:
    
    
    GREEN = '' if plain_text else '\033[92m'
    RED = '' if plain_text else '\033[91m'
    YELLOW = '' if plain_text else '\033[93m'
    BLUE = '' if plain_text else '\033[94m'
    RESET = '' if plain_text else '\033[0m'
    
    
    UP_ARROW = '[UP]' if plain_text else '↑'
    DOWN_ARROW = '[DOWN]' if plain_text else '↓'
    
    formatted = []
    
    # Add search information at the top
    formatted.append("0. Search Information:")
    formatted.append(f"• Search Company Name: {input_company_name}")
    formatted.append(f"• Search Emirate: {input_emirate if input_emirate else 'N/A'}")
    formatted.append("")
    
    legitimacy = calculate_business_legitimacy(result, input_company_name)
    
    
    formatted.append("1. General Information:")
    business_name = result.get('name', 'Unknown')
    formatted.append(f"• Business Name: {business_name}")
    
    
    similarity = legitimacy['breakdown']['name_similarity']
    similarity_percentage = round(similarity, 2)
    similarity_color = GREEN if similarity >= COLOR_THRESHOLDS['green'] else YELLOW if similarity >= COLOR_THRESHOLDS['yellow'] else RED
    formatted.append(f"• Name Match: {similarity_color}{similarity_percentage}%{RESET}")
    
    
    legitimacy_color = GREEN if legitimacy['total_score'] >= COLOR_THRESHOLDS['green'] * 100 else YELLOW if legitimacy['total_score'] >= COLOR_THRESHOLDS['yellow'] * 100 else RED
    formatted.append(f"• Business Legitimacy Score: {legitimacy_color}{legitimacy['total_score']}% ({legitimacy['legitimacy_level']}){RESET}")
    
    formatted.append(f"• Address: {result.get('formatted_address', 'N/A')}")
    formatted.append(f"• Phone Number: {result.get('formatted_phone_number', 'N/A')}")
    formatted.append(f"• International Phone: {result.get('international_phone_number', 'N/A')}")
    formatted.append(f"• Website URL: {result.get('website', 'N/A')}")
    
    
    formatted.append("\n2. Operational Hours:")
    hours = result.get('current_opening_hours', {})
    if hours and ('periods' in hours or 'weekday_text' in hours):
        formatted.append(f"• Status: {GREEN}{UP_ARROW} Updated{RESET}")
        formatted.append("• Hours Details:")
        hours_text = format_opening_hours(hours)
        for line in hours_text.split('\n'):
            formatted.append(f"  {line}")
    else:
        formatted.append(f"• Status: {RED}{DOWN_ARROW} Not Updated{RESET}")
        formatted.append("• Hours Details: N/A")
    
    
    formatted.append("\n3. Website Information:")
    website = result.get('website', '')
    if website and website.startswith('http'):
        formatted.append(f"• Status: {GREEN}{UP_ARROW} Updated{RESET}")
        formatted.append(f"• URL: {website}")
        domain = website.split('//')[-1].split('/')[0]
        formatted.append(f"• Domain: {domain}")
        
        
        domain_name = extract_domain_name(website)
        if domain_name:
            website_similarity = calculate_domain_similarity(input_company_name, domain_name)
            similarity_percentage = round(website_similarity, 2)
            similarity_color = GREEN if website_similarity >= COLOR_THRESHOLDS['green'] * 100 else YELLOW if website_similarity >= COLOR_THRESHOLDS['yellow'] * 100 else RED
            formatted.append(f"• Website Name Match: {similarity_color}{similarity_percentage}%{RESET}")
    else:
        formatted.append(f"• Status: {RED}{DOWN_ARROW} Not Updated{RESET}")
        formatted.append("• URL: N/A")
        formatted.append("• Domain: N/A")
        formatted.append("• Website Name Match: N/A")
    
    
    formatted.append("\n4. Review Information:")
    rating = result.get('rating')
    reviews_count = result.get('user_ratings_total', 0)
    if rating and reviews_count > 0:
        formatted.append(f"• Status: {GREEN}{UP_ARROW} Available{RESET}")
        formatted.append(f"• Number of Reviews: {reviews_count}")
        formatted.append(f"• Average Rating: {rating:.1f}")
        formatted.append(f"• Price Level: {'$' * result.get('price_level', 0) if result.get('price_level') else 'N/A'}")
    else:
        formatted.append(f"• Status: {RED}{DOWN_ARROW} Not Available{RESET}")
        formatted.append("• Number of Reviews: 0")
        formatted.append("• Average Rating: N/A")
        formatted.append("• Price Level: N/A")
    
    
    formatted.append("\n5. Location Information:")
    formatted.append(f"• Google Maps Link: {result.get('url', 'N/A')}")
    formatted.append(f"• Coordinates: {format_location(result.get('geometry'))}")
    formatted.append("\n• Address Components:")
    formatted.append(format_address_components(result.get('address_components')))
    
    
    emirate_validation = result.get('emirate_validation')
    if emirate_validation:
        status_color = GREEN if emirate_validation['is_valid'] else RED
        status_arrow = UP_ARROW if emirate_validation['is_valid'] else DOWN_ARROW
        formatted.append("\n• Emirate Validation:")
        formatted.append(f"• Status: {status_color}{status_arrow} {'Valid' if emirate_validation['is_valid'] else 'Invalid'}{RESET}")
        formatted.append(f"• Expected Emirate: {emirate_validation.get('actual_emirate', 'N/A')}")
        formatted.append(f"• Confidence: {emirate_validation.get('confidence', 'N/A').title()}")
        if 'coordinates' in emirate_validation:
            coords = emirate_validation['coordinates']
            formatted.append(f"• Validation Coordinates: {coords['latitude']:.6f}, {coords['longitude']:.6f}")
        if 'full_address' in emirate_validation:
            formatted.append(f"• Geocoded Address: {emirate_validation['full_address']}")
        if 'error' in emirate_validation:
            formatted.append(f"• Error: {RED}{emirate_validation['error']}{RESET}")
    
    
    formatted.append("\n6. Business Details:")
    if result.get('types'):
        business_types = []
        for type_name in result['types']:
            readable_type = type_name.replace('_', ' ').title()
            business_types.append(readable_type)
        formatted.append(f"• Business Types: {', '.join(business_types)}")
    formatted.append(f"• Business Status: {result.get('business_status', 'N/A')}")
    if result.get('editorial_summary'):
        formatted.append(f"• Description: {result.get('editorial_summary', {}).get('overview', 'N/A')}")
    
    
    formatted.append("\n7. Services and Amenities:")
    formatted.append(format_services(result))
    
    
    formatted.append("\n8. Additional Information:")
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted.append(f"• Last Updated Date: {last_updated}")
    formatted.append(f"• Place ID: {result.get('place_id', 'N/A')}")
    
    
    formatted.append("\n9. Comprehensive Legitimacy/similarity Analysis:")
    formatted.append(f"• Overall Score: {legitimacy_color}{legitimacy['total_score']}% ({legitimacy['legitimacy_level']}){RESET}")
    
    
    formatted.append("\nDetailed Score Breakdown:")
    for factor, weight in DISPLAY_WEIGHTS.items():
        
        data_key = {
            'name_match': 'name_similarity',
            'website_match': 'website_similarity',
            'contact_info': 'contact_completeness',
            'location': 'location_completeness',
            'operational': 'operational_completeness',
            'reviews': 'review_score',
            'completeness': 'profile_completeness',
            'emirate_match': 'emirate_confidence'
        }.get(factor, factor)
        
        score = legitimacy['breakdown'][data_key]
        fuzzy_weight = legitimacy['weights'].get(factor, weight)
        color = GREEN if score >= COLOR_THRESHOLDS['green'] * 100 else YELLOW if score >= COLOR_THRESHOLDS['yellow'] * 100 else RED
        formatted.append(f"• {factor.replace('_', ' ').title()}: {color}{score}%{RESET}")
        formatted.append(f"  - Base Weight: {weight}%")
        formatted.append(f"  - Fuzzy Weight: {fuzzy_weight}%")
        formatted.append(f"  - Weight Adjustment: {fuzzy_weight - weight:+.1f}%")
    
    
    formatted.append("\nRecommendations:")
    for factor, score in legitimacy['breakdown'].items():
        if score < COLOR_THRESHOLDS['yellow'] * 100:
            
            display_factor = {
                'name_similarity': 'name_match',
                'website_similarity': 'website_match',
                'contact_completeness': 'contact_info',
                'location_completeness': 'location',
                'operational_completeness': 'operational',
                'review_score': 'reviews',
                'profile_completeness': 'completeness',
                'emirate_confidence': 'emirate_match'
            }.get(factor, factor)
            
            formatted.append(f"• {display_factor.replace('_', ' ').title()}: {RED}Needs improvement ({score}%){RESET}")
            if display_factor == 'name_match':
                formatted.append("  - Verify if this is the correct business")
            elif display_factor == 'contact_info':
                formatted.append("  - Contact information should be verified")
            elif display_factor == 'location':
                formatted.append("  - Location details need verification")
            elif display_factor == 'operational':
                formatted.append("  - Business operational status needs confirmation")
            elif display_factor == 'reviews':
                formatted.append("  - Limited or no customer reviews available")
            elif display_factor == 'completeness':
                formatted.append("  - Business profile is incomplete")
            elif display_factor == 'emirate_match':
                formatted.append("  - Location verification needed")
    
    return "\n".join(formatted)

def format_services(result: Dict) -> str:
    
    services = []
    
    
    if result.get('wheelchair_accessible_entrance'):
        services.append("Wheelchair Accessible")
    
    
    if result.get('delivery'):
        services.append("Delivery Available")
    if result.get('dine_in'):
        services.append("Dine-in Available")
    if result.get('takeout'):
        services.append("Takeout Available")
    
    
    payment_methods = []
    if result.get('payment_methods'):
        for method in result['payment_methods']:
            if method == 'cash':
                payment_methods.append("Cash")
            elif method == 'credit_card':
                payment_methods.append("Credit Card")
            elif method == 'debit_card':
                payment_methods.append("Debit Card")
    if payment_methods:
        services.append(f"Payment Methods: {', '.join(payment_methods)}")
    
    
    if result.get('curbside_pickup'):
        services.append("Curbside Pickup")
    if result.get('outdoor_seating'):
        services.append("Outdoor Seating")
    if result.get('reservable'):
        services.append("Reservations Available")
    
    return ", ".join(services) if services else "N/A"

def format_opening_hours(hours: Dict) -> str:
    
    if not hours:
        return "N/A"
    
    formatted = []
    
    
    if 'periods' in hours:
        for period in hours['periods']:
            open_time = period.get('open', {})
            close_time = period.get('close', {})
            
            if open_time and close_time:
                day = open_time.get('day', 0)
                open_str = open_time.get('time', '')
                close_str = close_time.get('time', '')
                
                
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_name = days[day - 1] if 1 <= day <= 7 else f'Day {day}'
                
                
                if len(open_str) == 4 and len(close_str) == 4:
                    open_time = f"{open_str[:2]}:{open_str[2:]}"
                    close_time = f"{close_str[:2]}:{close_str[2:]}"
                    formatted.append(f"{day_name}: {open_time} - {close_time}")
    
    
    if not formatted and 'weekday_text' in hours:
        formatted.extend(hours['weekday_text'])
    
    return "\n".join(formatted) if formatted else "N/A"

def format_location(geometry: Dict) -> str:
    
    if not geometry or 'location' not in geometry:
        return "N/A"
    
    location = geometry['location']
    return f"Latitude: {location.get('lat', 'N/A')}, Longitude: {location.get('lng', 'N/A')}"

def format_address_components(components: List[Dict]) -> str:
    
    if not components:
        return "N/A"
    
    formatted = []
    for component in components:
        types = component.get('types', [])
        if types:
            formatted.append(f"{component.get('long_name', '')} ({', '.join(types)})")
    
    return "\n".join(formatted) if formatted else "N/A"

def format_news_article(article: Dict) -> str:
    
    formatted = []
    
    
    title = article.get('title', 'No title')
    source = article.get('source', {}).get('name', 'Unknown source')
    formatted.append(f"Title: {title}")
    formatted.append(f"Source: {source}")
    
    
    published_at = article.get('publishedAt', '')
    if published_at:
        try:
            date_obj = datetime.strptime(published_at, '%a, %d %b %Y %H:%M:%S %Z')
            formatted_date = date_obj.strftime('%B %d, %Y')
            formatted.append(f"Published: {formatted_date}")
        except:
            formatted.append(f"Published: {published_at}")
    
    
    url = article.get('url', '')
    if url:
        formatted.append(f"URL: {url}")
    
    
    description = article.get('description', '')
    if description:
        formatted.append(f"Description: {description}")
    
    return "\n".join(formatted)

def format_for_csv(result: Dict, input_company_name: str, input_emirate: str = None) -> Dict:
    
    legitimacy = calculate_business_legitimacy(result, input_company_name)


    hours = result.get('current_opening_hours', {})
    hours_text = format_opening_hours(hours)
    
    
    services = format_services(result)
    
    
    address_components = format_address_components(result.get('address_components'))
    
    
    location = format_location(result.get('geometry'))
    
    
    emirate_validation = result.get('emirate_validation', {})
    
    
    csv_data = {
        'search_company_name': input_company_name,
        'search_emirate': input_emirate if input_emirate else 'N/A',
        'business_name': result.get('name', 'N/A'),
        'name_match_percentage': legitimacy['breakdown']['name_similarity'] ,
        'website_match_percentage': legitimacy['breakdown']['website_similarity'],
        'legitimacy_score': legitimacy['total_score'],
        'legitimacy_level': legitimacy['legitimacy_level'],
        
        
        'address': result.get('formatted_address', 'N/A'),
        'phone': result.get('formatted_phone_number', 'N/A'),
        'international_phone': result.get('international_phone_number', 'N/A'),
        'website': result.get('website', 'N/A'),
        
        
        'opening_hours': hours_text,
        'business_status': result.get('business_status', 'N/A'),
        
        
        'rating': result.get('rating', 'N/A'),
        'reviews_count': result.get('user_ratings_total', 0),
        'price_level': result.get('price_level', 'N/A'),
        
        
        'google_maps_url': result.get('url', 'N/A'),
        'coordinates': location,
        'address_components': address_components,
        
        
        'emirate_valid': emirate_validation.get('is_valid', False),
        'expected_emirate': emirate_validation.get('actual_emirate', 'N/A'),
        'emirate_confidence': emirate_validation.get('confidence', 'N/A'),
        
        
        'business_types': ', '.join(result.get('types', [])),
        'description': result.get('editorial_summary', {}).get('overview', 'N/A'),
        
        
        'services': services,
        
        
        'place_id': result.get('place_id', 'N/A'),
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    
    for factor, weight in DISPLAY_WEIGHTS.items():
        data_key = {
            'name_match': 'name_similarity',
            'website_match': 'website_similarity',
            'contact_info': 'contact_completeness',
            'location': 'location_completeness',
            'operational': 'operational_completeness',
            'reviews': 'review_score',
            'completeness': 'profile_completeness',
            'emirate_match': 'emirate_confidence'
        }.get(factor, factor)
        
        score = legitimacy['breakdown'][data_key]
        fuzzy_weight = legitimacy['weights'].get(factor, weight)
        
        csv_data[f'{factor}_score'] = round(score, 2)

    
    return csv_data

def save_summary_to_csv(results: List[Dict], output_file: str = None) -> str:

    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"company_summary_{timestamp}.csv"
    
    
    csv_data = [format_for_csv(result, result['company_name'], result['emirate']) for result in results]
    
    if not csv_data:
        return ""
    
    
    fieldnames = set()
    for data in csv_data:
        fieldnames.update(data.keys())
    fieldnames = sorted(list(fieldnames))
    
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        return output_file
    except Exception as e:
        print(f"Error saving CSV file: {str(e)}")
        return ""

def save_summary_to_file(summary: str, input_company_name: str, output_file: str = None) -> str:

    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"company_summary_{input_company_name}_{timestamp}.txt"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        return output_file
    except Exception as e:
        print(f"Error saving summary file: {str(e)}")
        return ""

def main():
    parser = argparse.ArgumentParser(description='Company Data Analyzer')
    parser.add_argument('--input', help='Input CSV file containing company names and emirates (columns: company_name,emirate)')
    parser.add_argument('company_name', nargs='?', help='Company name to search for (optional if using --input)')
    parser.add_argument('-e', '--emirate', help='Expected emirate for validation (optional if using --input)')
    parser.add_argument('--domains', nargs='+', help='List of domains to search for news')
    parser.add_argument('--output', help='Output file path for company data')
    parser.add_argument('--csv', help='Output file path for CSV summary')
    parser.add_argument('-s', '--summary', help='Custom output file path for text summary (optional)')
    args = parser.parse_args()

    try:
        maps_scraper = GoogleMapsScraper()
        google_scraper = GoogleSearchScraper()

        
        if args.input:
            try:
                with open(args.input, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    companies = list(reader)
            except Exception as e:
                print(f"Error reading CSV file: {str(e)}")
                return
        else:
            if not args.company_name:
                print("Please provide either --input CSV file or company_name argument")
                return
            companies = [{'company_name': args.company_name, 'emirate': args.emirate}]

        
        all_detailed_results = []
        all_news = []
        all_summaries = []
        all_summaries_txt = []
        seen_urls = set()

        
        for company in companies:
            company_name = company['company_name']
            emirate = company.get('emirate')
            
            print(f"\nProcessing company: {company_name}")
            if emirate:
                print(f"Expected emirate: {emirate}")

            
            maps_results = maps_scraper.search_company(company_name)
            
            if maps_results:
                detailed_results = []
                for place in maps_results:
                    print(f"Getting details for: {place.get('name', 'Unknown')}")
                    details = maps_scraper.get_place_details(place['place_id'])
                    details['company_name'] = company_name
                    details['emirate'] = emirate
                    if details:
                        if emirate:
                            details['emirate_validation'] = maps_scraper.validate_emirate(details, emirate)
                        detailed_results.append(details)
                
                if not detailed_results:
                    print("No detailed company information found.")
                    continue
                
                
                all_detailed_results.extend(detailed_results)
                
                
                for result in detailed_results:
                    console_summary = format_company_summary(result, company_name, emirate, plain_text=False)
                    console_summary_txt = format_company_summary(result, company_name, emirate, plain_text=True)
                    all_summaries.append(console_summary)
                    all_summaries_txt.append(console_summary_txt)
                    print(console_summary)
                    print("-" * 50)

            
            print(f"\nSearching for news and press releases: {company_name}")
            google_news_results = google_scraper.search_news(company_name, args.domains)
            
            if google_news_results:
                for article in google_news_results:
                    url = article.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_news.append(article)
                        print(format_news_article(article))
                        print("-" * 50)
            
            print("\n" + "="*80 + "\n")  

        
        if all_detailed_results:
            
            maps_output_file = args.output or maps_scraper.save_to_json(all_detailed_results)
            if maps_output_file:
                print(f"\nAll company data saved to: {maps_output_file}")
            
            
            csv_output_file = save_summary_to_csv(all_detailed_results, args.csv)
            if csv_output_file:
                print(f"All company summaries saved to: {csv_output_file}")
            
            
            combined_summary = "\n\n".join(all_summaries_txt)
            summary_file = save_summary_to_file(combined_summary, "all_companies", args.summary)
            if summary_file:
                print(f"All company summaries saved to: {summary_file}")

        if all_news:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            news_output_file = f"all_news_data_{timestamp}.json"
            
            with open(news_output_file, 'w', encoding='utf-8') as f:
                json.dump(all_news, f, ensure_ascii=False, indent=4)
            
            print(f"All news data saved to: {news_output_file}")
        else:
            print("No news or press releases found for any company.")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 