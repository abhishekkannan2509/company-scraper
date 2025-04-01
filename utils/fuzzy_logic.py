from typing import Dict, Tuple
import numpy as np
from config.fuzzy_config import (
    MEMBERSHIP_PARAMS,
    BASE_WEIGHTS,
    MISMATCH_THRESHOLDS,
    LEGITIMACY_THRESHOLDS,
    COLOR_THRESHOLDS
)

def triangular_membership(x: float, a: float, b: float, c: float) -> float:
    if x <= a:
        return 0.0
    elif x >= c:
        return 1.0  
    elif a < x <= b:
        return (x - a) / (b - a)
    else:
        return (c - x) / (c - b)

def calculate_fuzzy_weights(data: Dict) -> Dict[str, float]:
    weights = {}
    for factor, base_weight in BASE_WEIGHTS.items():
        params = MEMBERSHIP_PARAMS[factor]
        if factor == 'name_match':
            score = data.get('name_similarity', 0)
        elif factor == 'website_match':
            score = data.get('website_similarity', 0)
        elif factor == 'contact_info':
            score = data.get('contact_completeness', 0)
        elif factor == 'location':
            score = data.get('location_completeness', 0)
        elif factor == 'operational':
            score = data.get('operational_completeness', 0)
        elif factor == 'reviews':
            score = data.get('review_score', 0)
        elif factor == 'completeness':
            score = data.get('profile_completeness', 0)
        elif factor == 'emirate_match':
            score = data.get('emirate_confidence', 0)
        else:
            score = 0
        membership = triangular_membership(
            score,
            params['a'],
            params['b'],
            params['c']
        )
        weights[factor] = membership * base_weight
    
    significant_mismatch = False
    for factor, score in data.items():
        if factor.endswith('_similarity') or factor.endswith('_completeness'):
            if score < MISMATCH_THRESHOLDS['significant_mismatch']:
                significant_mismatch = True
                
                weights = {k: v * MISMATCH_THRESHOLDS['weight_reduction'] 
                          for k, v in weights.items()}
                break
    
    
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {k: v/total_weight for k, v in weights.items()}
    
    return weights

def calculate_fuzzy_score(data: Dict) -> Tuple[float, str]:    
    weights = calculate_fuzzy_weights(data)
    
    
    scores = {}
    
    
    scores['name_match'] = data.get('name_similarity', 0)
    
    
    scores['website_match'] = data.get('website_similarity', 0)
    
    
    scores['contact_info'] = data.get('contact_completeness', 0)
    
    
    scores['location'] = data.get('location_completeness', 0)
    
    
    scores['operational'] = data.get('operational_completeness', 0)
    
    
    scores['reviews'] = data.get('review_score', 0)
    
    
    scores['completeness'] = data.get('profile_completeness', 0)
    
    
    scores['emirate_match'] = data.get('emirate_confidence', 0)
    
    
    significant_mismatch = False
    for factor, score in scores.items():
        if score < MISMATCH_THRESHOLDS['significant_mismatch']:
            significant_mismatch = True
            break
    
    
    total_score = sum(scores[k] * weights[k] for k in scores)
    
    
    if significant_mismatch:
        total_score *= MISMATCH_THRESHOLDS['score_reduction']
    
    
    if total_score >= LEGITIMACY_THRESHOLDS['high'] and not significant_mismatch:
        level = "High"
    elif total_score >= LEGITIMACY_THRESHOLDS['moderate']:
        level = "Moderate"
    elif total_score >= LEGITIMACY_THRESHOLDS['low']:
        level = "Low"
    else:
        level = "Very Low"
    
    return total_score * 100, level 