"""
Configuration file for fuzzy logic parameters.
"""

# Triangular membership function parameters for each factor
MEMBERSHIP_PARAMS = {
    'name_match': {
        'a': 0.0,    # Left vertex
        'b': 0.9,    # Peak vertex
        'c': 1.0     # Right vertex
    },
    'website_match': {
        'a': 0.0,
        'b': 0.9,
        'c': 1.0
    },
    'contact_info': {
        'a': 0.0,
        'b': 0.9,
        'c': 1.0
    },
    'location': {
        'a': 0.0,
        'b': 0.9,
        'c': 1.0
    },
    'operational': {
        'a': 0.0,
        'b': 0.9,
        'c': 1.0
    },
    'reviews': {
        'a': 0.0,
        'b': 0.9,
        'c': 1.0
    },
    'completeness': {
        'a': 0.0,
        'b': 0.9,
        'c': 1.0
    },
    'emirate_match': {
        'a': 0.0,
        'b': 0.9,
        'c': 1.0
    }
}

# Base weights for each factor (before fuzzy adjustment)
BASE_WEIGHTS = {
    'name_match': 0.15,      # 15%
    'website_match': 0.15,   # 15%
    'contact_info': 0.15,    # 15%
    'location': 0.15,        # 15%
    'operational': 0.15,     # 15%
    'reviews': 0.15,         # 15%
    'completeness': 0.1,     # 10%
    'emirate_match': 0.05    # 5%
}

# Thresholds for significant mismatches
MISMATCH_THRESHOLDS = {
    'significant_mismatch': 0.7,    # Below 70% is considered significant
    'weight_reduction': 0.5,        # 50% reduction in weights
    'score_reduction': 0.7          # 30% reduction in overall score
}

# Legitimacy level thresholds
LEGITIMACY_THRESHOLDS = {
    'high': 0.8,        # ≥ 90% for high
    'moderate': 0.6,    # ≥ 70% for moderate
    'low': 0.4,         # ≥ 50% for low
    'very_low': 0.0     # < 50% for very low
}

# Color coding thresholds (for display)
COLOR_THRESHOLDS = {
    'green': 0.8,   # ≥ 80% for green
    'yellow': 0.6,  # ≥ 60% for yellow
    'red': 0.0      # < 60% for red
} 