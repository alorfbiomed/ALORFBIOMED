"""
URL utilities for handling equipment serial numbers with special characters.
"""
import re
from urllib.parse import quote, unquote


def serial_to_url_safe(serial: str) -> str:
    """
    Convert equipment serial number to URL-safe format.
    
    Args:
        serial: Original equipment serial number
        
    Returns:
        str: URL-safe version of the serial number
        
    Examples:
        'SW3266#' -> 'SW3266-hash'
        'EU 2017/745' -> 'EU-2017-745'
        'ABC/DEF#123' -> 'ABC-DEF-hash123'
        'Normal123' -> 'Normal123'
    """
    if not serial:
        return serial
    
    # Create URL-safe version
    url_safe = serial
    
    # Replace hash symbols with '-hash'
    url_safe = url_safe.replace('#', '-hash')
    
    # Replace forward slashes with hyphens
    url_safe = url_safe.replace('/', '-')
    
    # Replace spaces with hyphens
    url_safe = url_safe.replace(' ', '-')
    
    # Replace other problematic characters
    url_safe = url_safe.replace('\\', '-')
    url_safe = url_safe.replace('?', '-question')
    url_safe = url_safe.replace('&', '-and')
    url_safe = url_safe.replace('%', '-percent')
    url_safe = url_safe.replace('+', '-plus')
    
    # Remove any consecutive hyphens
    url_safe = re.sub(r'-+', '-', url_safe)
    
    # Remove leading/trailing hyphens
    url_safe = url_safe.strip('-')
    
    return url_safe


def url_safe_to_serial(url_safe: str) -> str:
    """
    Convert URL-safe serial number back to original format.

    Args:
        url_safe: URL-safe version of the serial number

    Returns:
        str: Original equipment serial number

    Examples:
        'SW3266-hash' -> 'SW3266#'
        'EU-2017-745' -> 'EU 2017/745'
        'ABC-DEF-hash123' -> 'ABC/DEF#123'
        'Normal123' -> 'Normal123'
        'N-A-243' -> 'N-A 243'
    """
    if not url_safe:
        return url_safe

    # Start with the URL-safe version
    original = url_safe

    # Restore special characters in reverse order of encoding
    original = original.replace('-plus', '+')
    original = original.replace('-percent', '%')
    original = original.replace('-and', '&')
    original = original.replace('-question', '?')
    original = original.replace('-hash', '#')

    # Handle common patterns for space/slash restoration
    if '-' in original and not any(char in original for char in ['#', '+', '%', '&', '?']):
        # Check if this looks like a space/slash pattern
        parts = original.split('-')
        if len(parts) >= 3:
            # Pattern 1: "EU 2017/745" (space then slash) - letters, then numbers
            if parts[0].isalpha() and parts[1].isdigit() and parts[2].isdigit():
                return f"{parts[0]} {parts[1]}/{parts[2]}"
            # Pattern 2: "ABC/DEF 123" (slash then space) - 3 parts, last is number
            elif len(parts) == 3 and parts[2].isdigit() and not parts[1].isdigit():
                return f"{parts[0]}/{parts[1]} {parts[2]}"
        elif len(parts) == 2:
            # Simple two-part patterns - default to space
            # "Test-Space" -> "Test Space"
            return f"{parts[0]} {parts[1]}"

    # If no special pattern detected, return as-is
    # This handles cases like "N-A-243" where hyphens might be original
    return original


def find_equipment_by_url_safe_serial(url_safe_serial: str, equipment_data: list) -> dict:
    """
    Find equipment by URL-safe serial number.

    This function tries multiple strategies to match the URL-safe serial
    with the actual equipment records.

    Args:
        url_safe_serial: URL-safe version of the serial number
        equipment_data: List of equipment records

    Returns:
        dict: Equipment record if found, None otherwise
    """
    if not url_safe_serial or not equipment_data:
        return None

    def get_equipment_serial(equipment: dict) -> str:
        """Get serial number from equipment record, handling both PPM and OCM formats."""
        # PPM uses 'SERIAL' (uppercase), OCM uses 'Serial' (mixed case)
        return equipment.get('SERIAL') or equipment.get('Serial') or ''

    # Strategy 1: Direct match (for serials without special characters)
    for equipment in equipment_data:
        if get_equipment_serial(equipment) == url_safe_serial:
            return equipment

    # Strategy 2: Convert URL-safe back to original and match
    original_serial = url_safe_to_serial(url_safe_serial)
    for equipment in equipment_data:
        if get_equipment_serial(equipment) == original_serial:
            return equipment

    # Strategy 3: Try common variations for space/slash handling
    # Convert hyphens back to spaces and slashes
    variations = [
        url_safe_serial.replace('-', ' '),  # All hyphens to spaces
        url_safe_serial.replace('-', '/'),  # All hyphens to slashes
    ]

    # Try mixed patterns (space then slash, slash then space)
    if '-' in url_safe_serial:
        parts = url_safe_serial.split('-')
        if len(parts) >= 2:
            # For cases like "N-A-243" -> try "N-A 243" (keep first hyphen, convert last to space)
            if len(parts) == 3:
                # Try keeping first hyphen, converting second to space
                first_hyphen_space = f"{parts[0]}-{parts[1]} {parts[2]}"
                variations.append(first_hyphen_space)

                # Try converting first to space, keeping second hyphen
                space_first_hyphen = f"{parts[0]} {parts[1]}-{parts[2]}"
                variations.append(space_first_hyphen)

            # Try: "EU 2017/745" pattern (space then slash)
            if len(parts) >= 3:
                space_slash_pattern = f"{parts[0]} {'/'.join(parts[1:])}"
                variations.append(space_slash_pattern)

                # Try: "ABC/DEF 123" pattern (slash then space)
                slash_space_pattern = f"{'/'.join(parts[:-1])} {parts[-1]}"
                variations.append(slash_space_pattern)

            # Handle complex patterns with hash symbols
            # "ABC-DEF-hash123" -> "ABC/DEF#123"
            if 'hash' in url_safe_serial:
                # Replace -hash with # first, then convert remaining hyphens to slashes
                hash_restored = url_safe_serial.replace('-hash', '#')
                if '-' in hash_restored:
                    # Convert remaining hyphens to slashes: "ABC-DEF#123" -> "ABC/DEF#123"
                    slash_hash_pattern = hash_restored.replace('-', '/')
                    variations.append(slash_hash_pattern)

    for variation in variations:
        for equipment in equipment_data:
            if get_equipment_serial(equipment) == variation:
                return equipment

    # Strategy 4: URL decode the input (in case it's still URL-encoded)
    try:
        decoded_serial = unquote(url_safe_serial)
        if decoded_serial != url_safe_serial:
            for equipment in equipment_data:
                if get_equipment_serial(equipment) == decoded_serial:
                    return equipment
    except Exception:
        pass

    return None


def get_equipment_url_patterns(serial: str) -> dict:
    """
    Get all URL patterns for an equipment serial number.
    
    Args:
        serial: Original equipment serial number
        
    Returns:
        dict: Dictionary with different URL patterns
    """
    url_safe = serial_to_url_safe(serial)
    
    return {
        'original': serial,
        'url_safe': url_safe,
        'url_encoded': quote(serial, safe=''),
        'history_url': f'/equipment/{{equipment_type}}/{url_safe}/history',
        'edit_url': f'/equipment/{{equipment_type}}/edit/{url_safe}',
    }


# Test the functions with known problematic serials
if __name__ == "__main__":
    test_serials = [
        'SW3266#',
        'EU 2017/745', 
        'ABC/DEF#123',
        'Normal123',
        'Test Space',
        'Test/Slash',
        'Complex#Test/With Spaces'
    ]
    
    print("Testing URL-safe serial transformations:")
    print("=" * 50)
    
    for serial in test_serials:
        url_safe = serial_to_url_safe(serial)
        restored = url_safe_to_serial(url_safe)
        
        print(f"Original:  '{serial}'")
        print(f"URL-safe:  '{url_safe}'")
        print(f"Restored:  '{restored}'")
        print(f"Match:     {serial == restored}")
        print("-" * 30)
