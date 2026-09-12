"""
India Locations Utility: State codes, district code normalization, and lookup helpers.
Used for geo-encoded Child IDs, jurisdictional routing, and address validation.
"""
import re
from typing import Dict, Optional, Tuple

STATE_NAME_TO_CODE: Dict[str, str] = {
    "ANDAMAN AND NICOBAR ISLANDS": "AN",
    "ANDHRA PRADESH": "AP",
    "ARUNACHAL PRADESH": "AR",
    "ASSAM": "AS",
    "BIHAR": "BR",
    "CHANDIGARH": "CH",
    "CHHATTISGARH": "CG",
    "DADRA AND NAGAR HAVELI AND DAMAN AND DIU": "DN",
    "DELHI": "DL",
    "GOA": "GA",
    "GUJARAT": "GJ",
    "HARYANA": "HR",
    "HIMACHAL PRADESH": "HP",
    "JAMMU AND KASHMIR": "JK",
    "JHARKHAND": "JH",
    "KARNATAKA": "KA",
    "KERALA": "KL",
    "LADAKH": "LA",
    "LAKSHADWEEP": "LD",
    "MADHYA PRADESH": "MP",
    "MAHARASHTRA": "MH",
    "MANIPUR": "MN",
    "MEGHALAYA": "ML",
    "MIZORAM": "MZ",
    "NAGALAND": "NL",
    "ODISHA": "OR",
    "PUDUCHERRY": "PY",
    "PUNJAB": "PB",
    "RAJASTHAN": "RJ",
    "SIKKIM": "SK",
    "TAMIL NADU": "TN",
    "TELANGANA": "TS",
    "TRIPURA": "TR",
    "UTTAR PRADESH": "UP",
    "UTTARAKHAND": "UK",
    "WEST BENGAL": "WB",
}

STATE_CODE_TO_NAME: Dict[str, str] = {v: k for k, v in STATE_NAME_TO_CODE.items()}

KNOWN_DISTRICT_CODES: Dict[str, str] = {
    "MUMBAI": "MUM",
    "MUMBAI SUBURBAN": "MSU",
    "PUNE": "PUN",
    "NAGPUR": "NAG",
    "THANE": "THA",
    "DELHI": "DEL",
    "NEW DELHI": "NDL",
    "NORTH DELHI": "NDL",
    "SOUTH DELHI": "SDL",
    "CENTRAL DELHI": "CDL",
    "EAST DELHI": "EDL",
    "WEST DELHI": "WDL",
    "BANGALORE": "BLR",
    "BENGALURU": "BLR",
    "BENGALURU URBAN": "BLR",
    "CHENNAI": "CHE",
    "KOLKATA": "KOL",
    "HYDERABAD": "HYD",
    "AHMEDABAD": "AHM",
    "SURAT": "SUR",
    "JAIPUR": "JAI",
    "LUCKNOW": "LKO",
    "KANPUR": "KNP",
    "PATNA": "PAT",
    "BHOPAL": "BHO",
    "INDORE": "IND",
    "CHANDIGARH": "CHD",
    "COIMBATORE": "CBE",
    "KOCHI": "KOC",
    "ERNAKULAM": "ERN",
    "THIRUVANANTHAPURAM": "TVM",
    "GUWAHATI": "GUW",
    "KAMRUP": "KAM",
    "RANCHI": "RAN",
    "VARANASI": "VAR",
    "AGRA": "AGR",
    "DEHRADUN": "DDN",
    "GURGAON": "GUR",
    "GURUGRAM": "GUR",
    "NOIDA": "NOI",
    "GAUTAM BUDDHA NAGAR": "GBN",
    "GHAZIABAD": "GZB",
    "FARIDABAD": "FBD",
}

def normalize_state_code(state_input: Optional[str]) -> str:
    """
    Normalizes a state name or code into a standard 2-letter uppercase Indian State code.
    Returns 'IN' if unknown or not provided.
    """
    if not state_input:
        return "IN"
    
    cleaned = re.sub(r"[^A-Za-z]", "", state_input).upper()
    if len(cleaned) == 2 and cleaned in STATE_CODE_TO_NAME:
        return cleaned
    
    norm_name = re.sub(r"[^A-Za-z\s]", "", state_input).strip().upper()
    if norm_name in STATE_NAME_TO_CODE:
        return STATE_NAME_TO_CODE[norm_name]
    
    # Prefix match
    for name, code in STATE_NAME_TO_CODE.items():
        if norm_name in name or name in norm_name:
            return code
            
    return cleaned[:2] if len(cleaned) >= 2 else "IN"

def normalize_district_code(district_input: Optional[str]) -> str:
    """
    Normalizes a district name into a standard 3-letter uppercase code.
    Returns 'GEN' if unknown or not provided.
    """
    if not district_input:
        return "GEN"
        
    norm = re.sub(r"[^A-Za-z\s]", "", district_input).strip().upper()
    if norm in KNOWN_DISTRICT_CODES:
        return KNOWN_DISTRICT_CODES[norm]
        
    # Check partial
    for name, code in KNOWN_DISTRICT_CODES.items():
        if norm in name or name in norm:
            return code
            
    cleaned = re.sub(r"[^A-Za-z]", "", district_input).upper()
    if len(cleaned) >= 3:
        return cleaned[:3]
    elif len(cleaned) > 0:
        return cleaned.ljust(3, "X")
    return "GEN"

def get_location_codes(state: Optional[str], district: Optional[str]) -> Tuple[str, str]:
    """Returns (state_code_2, district_code_3)."""
    return normalize_state_code(state), normalize_district_code(district)

MAJOR_CITY_CENTROIDS = [
    # (state, district, pin_code, lat, lng)
    ("Delhi", "Delhi", "110001", 28.6139, 77.2090),
    ("Delhi", "South Delhi", "110016", 28.5400, 77.1800),
    ("Delhi", "North Delhi", "110007", 28.6900, 77.2100),
    ("Maharashtra", "Mumbai", "400001", 18.9220, 72.8347),
    ("Maharashtra", "Mumbai Suburban", "400050", 19.0760, 72.8777),
    ("Maharashtra", "Pune", "411001", 18.5204, 73.8567),
    ("Maharashtra", "Nagpur", "440001", 21.1458, 79.0882),
    ("Karnataka", "Bangalore", "560001", 12.9716, 77.5946),
    ("Tamil Nadu", "Chennai", "600001", 13.0827, 80.2707),
    ("Telangana", "Hyderabad", "500001", 17.3850, 78.4867),
    ("West Bengal", "Kolkata", "700001", 22.5726, 88.3639),
    ("Gujarat", "Ahmedabad", "380001", 23.0225, 72.5714),
    ("Rajasthan", "Jaipur", "302001", 26.9124, 75.7873),
    ("Uttar Pradesh", "Lucknow", "226001", 26.8467, 80.9462),
    ("Uttar Pradesh", "Noida", "201301", 28.5355, 77.3910),
    ("Haryana", "Gurgaon", "122001", 28.4595, 77.0266),
    ("Chandigarh", "Chandigarh", "160001", 30.7333, 76.7794),
    ("Kerala", "Kochi", "682001", 9.9312, 76.2673),
    ("Kerala", "Thiruvananthapuram", "695001", 8.5241, 76.9366),
    ("Bihar", "Patna", "800001", 25.5941, 85.1376),
    ("Madhya Pradesh", "Bhopal", "462001", 23.2599, 77.4126),
    ("Madhya Pradesh", "Indore", "452001", 22.7196, 75.8577),
    ("Assam", "Guwahati", "781001", 26.1445, 91.7362),
    ("Odisha", "Bhubaneswar", "751001", 20.2961, 85.8245),
    ("Punjab", "Amritsar", "143001", 31.6340, 74.8723),
    ("Uttarakhand", "Dehradun", "248001", 30.3165, 78.0322),
    ("Jammu and Kashmir", "Srinagar", "190001", 34.0837, 74.7973),
    ("Goa", "Panaji", "403001", 15.4909, 73.8278)
]

def reverse_geocode_coordinates(latitude: float, longitude: float) -> Dict[str, Optional[str]]:
    """
    Reverse geocodes GPS coordinates into nearest Indian State, District, and PIN Code.
    """
    best_match = None
    min_dist_sq = float("inf")
    
    for state, district, pin_code, c_lat, c_lng in MAJOR_CITY_CENTROIDS:
        d_lat = latitude - c_lat
        d_lng = longitude - c_lng
        dist_sq = d_lat * d_lat + d_lng * d_lng
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            best_match = (state, district, pin_code)
            
    if best_match:
        state, district, pin_code = best_match
        return {
            "state": state,
            "district": district,
            "pin_code": pin_code,
            "latitude": latitude,
            "longitude": longitude,
            "state_code": normalize_state_code(state),
            "district_code": normalize_district_code(district)
        }
    return {
        "state": "Delhi",
        "district": "Delhi",
        "pin_code": "110001",
        "latitude": latitude,
        "longitude": longitude,
        "state_code": "DL",
        "district_code": "DEL"
    }

