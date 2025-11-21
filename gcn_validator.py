import re
from typing import Tuple


def normalize_gcn_number(gcn_str: str) -> str:
    """
    Normalize GCN number: add space between letters and digits, uppercase
    
    Rules for prefix (remove the first character):
    - 4 letters → remove 2 characters, keep 2 characters (SOAH → AH, SOCJ → CJ)
    - 3 letters → remove 2 characters, keep 1 character (SCV → V, SOB → B)
    - 2 letters → keep as is (AA → AA)
    - 1 letter → keep as is (D → D)
    
    Args:
        gcn_str: GCN number string to normalize
        
    Returns:
        Normalized GCN number (format: "XX 1234567")
    """
    # Remove special characters, only keep letters and numbers
    cleaned = re.sub(r'[^A-Za-z0-9]', '', gcn_str).upper()
    
    # Try to split letters and digits
    match = re.match(r'^([A-Z]+)(\d+)$', cleaned)
    if match:
        letters = match.group(1)
        digits = match.group(2)
        
        # Apply rules based on number of letters
        if len(letters) >= 4:
            # 4+ letters: remove 2 characters, keep 2 characters
            letters = letters[-2:]
        elif len(letters) == 3:
            # 3 letters: remove 2 characters, keep 1 character
            letters = letters[-1:]
        # 1-2 letters: keep as is
        
        return f"{letters} {digits}"
    
    return cleaned


def validate_filename_format(filename: str) -> Tuple[bool, str]:
    """
    Check if the filename format is correct
    
    Rules:
    1. 1-2 uppercase letters at the beginning
    2. Followed by an optional space and numbers
    3. Ends with "-GCN.pdf"
    
    Args:
        filename: Filename to check
        
    Returns:
        (True if valid, error message if invalid)
    """
    # Pattern: [1-2 uppercase letters][optional space][numbers]-GCN.pdf
    pattern = r'^([A-Z]{1,2})\s*(\d+)-GCN\.pdf$'
    
    match = re.match(pattern, filename)
    if not match:
        # Analyze error details
        if not filename.endswith('.pdf'):
            return False, "Không phải file PDF"
        
        if not filename.endswith('-GCN.pdf'):
            return False, "Không kết thúc bằng -GCN.pdf"
        
        # Check prefix part
        prefix_match = re.match(r'^([a-zA-Z]{1,2})', filename)
        if not prefix_match:
            return False, "Không có chữ cái đầu tiên"
        
        prefix = prefix_match.group(1)
        if not prefix.isupper():
            return False, f"Chữ cái phải viết HOA (hiện tại: '{prefix}')"
        
        # Check if there is a number
        if not re.search(r'\d+', filename):
            return False, "Thiếu phần số"
        
        return False, "Sai format tên file"
    
    return True, ""


def extract_gcn_from_filename(filename: str) -> str:
    """
    Extract GCN number from filename
    
    Args:
        filename: Filename (example: "AA 01555158-GCN.pdf")
        
    Returns:
        GCN number from filename (example: "AA 01555158")
    """
    # Find pattern: letter + number before "-GCN"
    match = re.search(r'([A-Z]{1,2}\s*\d+)-GCN', filename, re.IGNORECASE)
    if match:
        gcn = match.group(1)
        return normalize_gcn_number(gcn)
    
    # Fallback: find different pattern
    match = re.search(r'_([A-Z]{1,2}\s*\d+)-', filename, re.IGNORECASE)
    if match:
        gcn = match.group(1)
        return normalize_gcn_number(gcn)
    
    return "UNKNOWN"


def compare_gcn(filename_gcn: str, predicted_gcn: str) -> str:
    """
    Compare GCN number from filename with AI prediction
    
    Args:
        filename_gcn: GCN number from filename
        predicted_gcn: GCN number predicted by AI
        
    Returns:
        "Đúng" or "Cần hiệu đính"
    """
    normalized_filename = normalize_gcn_number(filename_gcn)
    normalized_predicted = normalize_gcn_number(predicted_gcn)
    
    return "Đúng" if normalized_filename == normalized_predicted else "Cần hiệu đính"

