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
