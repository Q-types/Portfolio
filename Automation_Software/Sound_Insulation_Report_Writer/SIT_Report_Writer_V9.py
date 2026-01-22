"""
Sound Insulation Test Report Writer - Version 9

Automated tool for generating professional Sound Insulation Test reports.
Processes Excel test data, generates acoustic charts, and produces PDF reports
with proper formatting and compliance documentation.

Features:
- Excel automation with win32com for data processing
- PDF generation and merging capabilities
- Acoustic chart generation with VBA macros
- Insightly CRM API integration for project details
- Automated report formatting with superscript deviations
- Support for Airborne (ABF/ABW) and Impact (IPF) sound tests

Author: Q-types
License: MIT
"""

import os
import re
import time
import sys
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import win32com.client
from win32com.client import constants, gencache
from docx import Document
import datetime
import requests
import base64
import shutil
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from io import BytesIO

# Get the executable's directory
if getattr(sys, 'frozen', False):
    # Running as executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Constants
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
TEMPLATES_PATH = os.path.join(BASE_DIR, "Templates")
MACROS_PATH = os.path.join(BASE_DIR, "Macros")
GDRIVE_PATH = r"G:\My Drive"

# Insightly API configuration
# For security, store API key in environment variable or secure config file
INSIGHTLY_API_KEY = os.environ.get('INSIGHTLY_API_KEY', '')
INSIGHTLY_BASE_URL = "https://api.na1.insightly.com/v3.1"

# Register Arial font
pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))

def get_insightly_headers():
    """Get headers for Insightly API requests with API key authentication."""
    encoded_key = base64.b64encode(INSIGHTLY_API_KEY.encode()).decode()
    return {
        "Authorization": f"Basic {encoded_key}",
        "Accept": "application/json"
    }

def get_project_by_number(project_number):
    """Get project details from Insightly using project number."""
    try:
        # Remove 'NP-' prefix if present for the API query
        clean_number = project_number.replace('NP-', '')
        
        # Search for projects with the given number
        headers = get_insightly_headers()
        response = requests.get(
            f"{INSIGHTLY_BASE_URL}/Projects/Search?field_name=PROJECT_NUMBER&field_value={clean_number}",
            headers=headers
        )
        response.raise_for_status()
        
        projects = response.json()
        if not projects:
            print(f"No project found with number {project_number}")
            return None
            
        return projects[0]  # Return the first matching project
        
    except Exception as e:
        print(f"Error fetching project from Insightly: {e}")
        return None
'''
def format_address(address):
    """Format address with commas between parts."""
    if not address:
        return address
    
    # UK postcode pattern
    postcode_pattern = r'([A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}|[A-Z]{1,2}[0-9][0-9]? ?[0-9][A-Z]{2}|GIR ?0A{2}|SAN ?TA1)'
    
    # Find and extract postcode if present
    postcode = None
    postcode_match = re.search(postcode_pattern, address)
    if postcode_match:
        postcode = postcode_match.group()
        # Remove postcode from address for processing
        address = address[:postcode_match.start()].strip()
    
    # Split remaining address into parts
    parts = []
    # First split on obvious delimiters
    for chunk in re.split(r'[,\n]', address):
        chunk = chunk.strip()
        if not chunk:
            continue
        # Then split on spaces between words that look like address parts
        words = chunk.split()
        current_part = []
        for word in words:
            # If word looks like it starts a new part (e.g. starts with number or common address words)
            if (word[0].isdigit() or 
                any(word.lower().startswith(p) for p in ['unit', 'flat', 'apt', 'suite', 'room', 'floor'])):
                if current_part:  # Save previous part if exists
                    parts.append(' '.join(current_part))
                current_part = [word]
            else:
                current_part.append(word)
        if current_part:  # Add final part
            parts.append(' '.join(current_part))
    
    # Add postcode back if we had one
    if postcode:
        parts.append(postcode)
    
    return ', '.join(parts)'''
    
def format_address(address, client_name):
    """Format address with commas between parts and cities."""
    if not address:
        return address
    
    # Common UK cities and towns
    uk_cities = {
        'London', 'Manchester', 'Birmingham', 'Leeds', 'Glasgow', 'Liverpool',
        'Newcastle', 'Sheffield', 'Bristol', 'Edinburgh', 'Cardiff', 'Nottingham',
        'Belfast', 'Leicester', 'York', 'Cambridge', 'Oxford', 'Portsmouth',
        'Brighton', 'Hull', 'Plymouth', 'Norwich', 'Bradford', 'Reading',
        'Middlesbrough', 'Huddersfield', 'Southampton', 'Derby', 'Milton Keynes'
    }
    
    # UK postcode pattern
    postcode_pattern = r'([A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}|[A-Z]{1,2}[0-9][0-9]? ?[0-9][A-Z]{2}|GIR ?0A{2}|SAN ?TA1)'
    
    # Find and extract postcode if present
    postcode = None
    postcode_match = re.search(postcode_pattern, address)
    if postcode_match:
        postcode = postcode_match.group()
        # Remove postcode from address for processing
        address = address[:postcode_match.start()].strip()
    
    # Find the client name if present
    client_name = client_name.strip()
    if client_name in address:
        address = address.replace(client_name, '').strip()

    # Split remaining address into parts
    parts = []
    # First split on obvious delimiters
    for chunk in re.split(r'[,\n]', address):
        chunk = chunk.strip()
        if not chunk:
            continue
        
        # Check if this chunk contains a city name
        words = chunk.split()
        city_found = False
        for i in range(len(words)):
            potential_city = ' '.join(words[i:])  # Try multi-word cities
            if potential_city in uk_cities:
                if i > 0:  # If there's content before the city
                    parts.append(' '.join(words[:i]))
                parts.append(potential_city)
                city_found = True
                break
        
        if city_found:
            continue
            
        # Process non-city chunks
        current_part = []
        for i, word in enumerate(words):
            # Check if this word is a unit/suite keyword
            is_unit_keyword = any(word.lower().startswith(p) for p in ['unit', 'flat', 'apt', 'suite', 'room', 'floor'])
            
            # If word starts with digit and previous wasn't a unit keyword, start new part
            if word[0].isdigit() and current_part and not any(current_part[-1].lower().startswith(p) for p in ['unit', 'flat', 'apt', 'suite', 'room', 'floor']):
                parts.append(' '.join(current_part))
                current_part = [word]
            # If it's a unit keyword and we have content, save previous and start new
            elif is_unit_keyword and current_part:
                parts.append(' '.join(current_part))
                current_part = [word]
            else:
                current_part.append(word)
        if current_part:  # Add final part
            parts.append(' '.join(current_part))
    
    # Add postcode back if we had one
    if postcode:
        parts.append(postcode)
    
    return ', '.join(parts)

def trim_at_postcode(address):
    """Trim address at postcode and format with commas on one line."""
    if not address:
        return address
        
    # UK postcode pattern
    postcode_pattern = r'([A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}|[A-Z]{1,2}[0-9][0-9]? ?[0-9][A-Z]{2}|GIR ?0A{2}|SAN ?TA1)'
    
    # Find postcode in address
    match = re.search(postcode_pattern, address)
    if match:
        # Get index where postcode ends
        postcode_end = match.end()
        # Trim address at postcode
        address = address[:postcode_end].strip()
    
    # Format the trimmed address
    return address

def get_project_addresses(project_id, client_name):
    """Get billing and site addresses for a project."""
    try:
        headers = get_insightly_headers()
        
        # Get project details including custom fields
        response = requests.get(
            f"{INSIGHTLY_BASE_URL}/Projects/{project_id}",
            headers=headers
        )
        response.raise_for_status()
        project = response.json()
        
        # Initialize addresses
        billing_address = ""
        site_address = ""
        
        # Extract addresses from custom fields
        if "CUSTOMFIELDS" in project:
            for field in project["CUSTOMFIELDS"]:
                if field.get("FIELD_NAME") == "BILLING_ADDRESS":
                    billing_address = trim_at_postcode(field.get("FIELD_VALUE", ""))
                elif field.get("FIELD_NAME") == "SITE_ADDRESS":
                    site_address = trim_at_postcode(field.get("FIELD_VALUE", ""))
        
        return billing_address, site_address
        
    except Exception as e:
        print(f"Error fetching project addresses: {e}")
        return None, None

def get_contact_details(contact_id, auth):
    """Get contact details from Insightly."""
    try:
        contact_url = f"{INSIGHTLY_BASE_URL}/Contacts/{contact_id}"
        headers = {'Accept': 'application/json'}
        response = requests.get(contact_url, auth=auth, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching contact details: {e}")
        return None

def get_project_details(project_number, client_name):
    """Get project details and addresses from Insightly."""
    try:
        # Remove 'NP-' prefix if present for the API query
        clean_number = project_number.replace('NP-', '')
        
        print(f"Fetching project details from Insightly for {project_number}...")
        
        # Get authentication headers
        headers = get_insightly_headers()
        
        # Try searching by project name containing the number
        search_url = f"{INSIGHTLY_BASE_URL}/Projects/Search?brief=true&top=10&count_total=true&field_name=PROJECT_NAME&field_value={clean_number}"
        
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        projects = response.json()
        
        matching_project = None
        for project in projects:
            project_name = project.get('PROJECT_NAME', '')
            if clean_number in project_name:
                matching_project = project
                break
        
        if not matching_project:
            print(f"No project found containing number {project_number}")
            return None, None
        
        # Get full project details including custom fields
        project_id = matching_project["PROJECT_ID"]
        details_url = f"{INSIGHTLY_BASE_URL}/Projects/{project_id}"
        response = requests.get(details_url, headers=headers)
        response.raise_for_status()
        project_details = response.json()
        
        # Initialize variables
        billing_address = None
        site_address = None
        
        if "CUSTOMFIELDS" in project_details:
            for field in project_details["CUSTOMFIELDS"]:
                field_name = field.get("FIELD_NAME", "")
                field_value = field.get("FIELD_VALUE", "")
                
                if field_name == "Billing_Notes__c":
                    # Extract billing address from notes
                    billing_address = field_value.split("INVOICE SENT")[0].strip() if "INVOICE SENT" in field_value else field_value
                elif field_name == "PROJECT_FIELD_2":
                    # Get site address
                    site_address = field_value
        
        # Format addresses
        if billing_address:
            billing_address = format_address(billing_address, client_name)
        if site_address:
            formatted_site_address = format_address(site_address, client_name)
            print(f"\nFound site address: {formatted_site_address}")
            use_address = input("Use this site address? (y/n): ").lower().strip()
            
            if use_address != 'y':
                print("\nEnter new site address:")
                site_address = input("> ").strip()
                if not site_address:  # If user entered nothing, keep original formatted address
                    site_address = formatted_site_address
            else:
                site_address = formatted_site_address
        
        return billing_address, site_address
        
    except Exception as e:
        print(f"Error fetching project from Insightly: {e}")
        return None, None

def get_associated_job():
    """Get previous job version from User."""
    previous_job = input("Was there a previous job version?")
    if previous_job.lower() in ["yes", "y", "1"]:
        associated_job = input("\nPrevious version reference: ").strip()
    else:
        associated_job = None
    return associated_job
    
def get_property_type():
    """Ask user for the property type."""
    property_types = {
        1: "Purpose built dwelling-flats",
        2: "Purpose built dwelling-houses",
        3: "Dwelling-flats formed by material change of use",
        4: "Dwelling-houses formed by material change of use",
        5: "Purpose built rooms for residential purposes",
        6: "Rooms for residential purposes formed by material change of use"
    }
    
    print("\nProperty Types:")
    for num, desc in property_types.items():
        print(f"{num}. {desc}")
        
    while True:
        try:
            choice = input("\nEnter property type number (1-6): ").strip()
            if not choice and sys.stdin.isatty():  # Non-interactive mode
                return property_types[3]  # Default to option 3
            
            choice = int(choice)
            if choice in property_types:
                return property_types[choice]
            else:
                print("Invalid choice. Please enter a number between 1 and 6.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_test_letter(index):
    """
    Generate test letter for a given index.
    Supports: A-Z (0-25), AA-AZ (26-51), BA-BZ (52-77), etc.
    
    Args:
        index: Zero-based index (0=A, 1=B, ..., 25=Z, 26=AA, 27=AB, etc.)
        
    Returns:
        str: Test letter (e.g., 'A', 'Z', 'AA', 'AB', 'BA', etc.)
    """
    if index < 26:
        # Single letter: A-Z
        return chr(65 + index)
    else:
        # Double letter: AA-AZ, BA-BZ, etc.
        first_letter_index = (index - 26) // 26
        second_letter_index = (index - 26) % 26
        return chr(65 + first_letter_index) + chr(65 + second_letter_index)

def parse_test_letter(letter):
    """
    Convert test letter back to index.
    
    Args:
        letter: Test letter (e.g., 'A', 'Z', 'AA', 'AB', 'BA', etc.)
        
    Returns:
        int: Zero-based index, or None if invalid
    """
    letter = letter.upper().strip()
    
    if len(letter) == 1:
        # Single letter: A-Z
        if 'A' <= letter <= 'Z':
            return ord(letter) - 65
    elif len(letter) == 2:
        # Double letter: AA-AZ, BA-BZ, etc.
        if 'A' <= letter[0] <= 'Z' and 'A' <= letter[1] <= 'Z':
            first_index = ord(letter[0]) - 65
            second_index = ord(letter[1]) - 65
            return 26 + (first_index * 26) + second_index
    
    return None

def get_deviation_text(deviation_number):
    """Convert deviation number to its corresponding text."""
    deviations = {
        1: "Soft / cosmetic flooring installed",
        2: "Mock-up doors installed",
        3: "Rooms furnished",
        4: "Testing into non-habitable rooms",
        5: "Room volumes <25m3",
        6: "Lower than minimum sample of testing required",
        7: "6dB difference between 1/3 octave bands not achieved",
        8: "Testing from lower volume room to higher volume room",
        9: "Testing in to corridors"
    }
    return deviations.get(int(deviation_number), "")

def get_deviations(wb, num_tests):
    """Get deviations for each test and create a numbered unique list."""
    test_deviations = {}  # Store original deviations for each test
    unique_deviations = []  # Store unique deviations in order of appearance
    deviation_mapping = {}  # Map original deviation numbers to new sequential numbers
    # Generate letters based on number of tests (supports A-Z, AA-AZ, BA-BZ, etc.)
    letters = [get_test_letter(i) for i in range(num_tests)]
    
    print("\nAvailable deviations:")
    print("1. Soft / cosmetic flooring installed")
    print("2. Mock-up doors installed")
    print("3. Rooms furnished")
    print("4. Testing into non-habitable rooms")
    print("5. Room volumes <25m3")
    print("6. Lower than minimum sample of testing required")
    print("7. 6dB difference between 1/3 octave bands not achieved")
    print("8. Testing from lower volume room to higher volume room")
    print("9. Testing in to corridors")
    
    for letter in letters:
        while True:
            print(f"\nEnter deviations for test {letter} (comma-separated numbers, or press Enter for none):")
            deviation_input = input().strip()
            
            if not deviation_input:  # No deviations
                test_deviations[letter] = []
                break
                
            try:
                # Convert input to list of integers
                devs = [int(d.strip()) for d in deviation_input.split(',') if d.strip()]
                # Validate numbers are in range 1-9
                if all(1 <= d <= 9 for d in devs):
                    test_deviations[letter] = devs
                    # Add to unique deviations if not already present
                    for dev in devs:
                        if dev not in unique_deviations:
                            unique_deviations.append(dev)
                    break
                else:
                    print("Error: Deviations must be numbers between 1 and 9")
            except ValueError:
                print("Error: Please enter valid numbers separated by commas")
    
    # Sort unique deviations in ascending order
    unique_deviations.sort()
    
    # Create mapping from original deviation numbers to sequential numbers
    deviation_mapping = {dev: i+1 for i, dev in enumerate(unique_deviations)}
    
    return test_deviations, unique_deviations, deviation_mapping

def to_superscript(text, include_separator=False):
    """Convert numbers and optionally separators to their superscript equivalents."""
    superscript_map = {
        '1': '¹',
        '2': '²',
        '3': '³',
        '4': '⁴',
        '5': '⁵',
        '6': '⁶',
        '7': '⁷',
        '8': '⁸',
        '9': '⁹'
    }
    if include_separator:
        superscript_map['|'] = '⸴'
    return ''.join(superscript_map.get(c, c) for c in text)

def format_deviation_text(deviation_number):
    """Get the text for a single deviation number."""
    deviation_texts = {
        1: "Soft / cosmetic flooring installed",
        2: "Mock-up doors installed",
        3: "Rooms furnished",
        4: "Testing into non-habitable rooms",
        5: "Room volumes <25m³",
        6: "Lower than minimum sample of testing required",
        7: "6dB difference between 1/3 octave bands not achieved",
        8: "Testing from lower volume room to higher volume room",
        9: "Testing in to corridors"
    }
    
    return deviation_texts.get(deviation_number, "")

def format_date(date_str):
    """Convert YYYY-MM-DD to DD Month YYYY format."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d %B %Y")
    except:
        return date_str

def open_excel_app():
    """
    Create a new Excel instance (using DispatchEx) and suppress alerts and link-update prompts.
    """
    excel_app = win32com.client.DispatchEx("Excel.Application")
    excel_app.Visible = False
    excel_app.DisplayAlerts = False
    excel_app.AskToUpdateLinks = False
    return excel_app

def open_workbook_with_editing(excel_app, filename, **kwargs):
    """
    Open an Excel workbook. If the workbook opens in Protected View, call .Edit()
    to enable editing (equivalent to clicking "Enable Editing").
    """
    wb = excel_app.Workbooks.Open(filename, **kwargs)
    if excel_app.ProtectedViewWindows.Count > 0:
        basename = os.path.basename(filename).lower()
        for i in range(1, excel_app.ProtectedViewWindows.Count + 1):
            pvw = excel_app.ProtectedViewWindows.Item(i)
            if pvw.SourceName.lower() == basename:
                print(f"File {filename} was in Protected View; enabling editing.")
                wb = pvw.Edit()
                break
    return wb

def add_and_run_macro(wb, test_type=None):
    """
    Adds and runs the plotting macro to generate all acoustic charts.
    Note: test_type parameter kept for backward compatibility but not used.
    """
    try:
        # Use the updated macro file
        macro_file = os.path.join(MACROS_PATH, "SIT_Macro_V4.txt")
        macro_name = "GenerateAcousticCharts_V4"
            
        # Read the macro code
        with open(macro_file, 'r') as f:
            macro_code = f.read()
            
        # Add a new module to the workbook
        vba_module = wb.VBProject.VBComponents.Add(1)  # 1 = vbext_ct_StdModule
        vba_module.CodeModule.AddFromString(macro_code)
        
        # Run the macro
        wb.Application.Run(macro_name)
        
        # Check the result
        data_sheet = wb.Sheets("Data")
        chart_count = data_sheet.Range("AB1").Value
        status = data_sheet.Range("AB2").Value
        
        if status == "Charts Generated":
            print(f"Successfully generated {int(chart_count)} charts")
        else:
            print("Warning: Charts may not have been generated correctly")
        
        # Remove the module
        wb.VBProject.VBComponents.Remove(vba_module)
        
    except Exception as e:
        print(f"Error running macro: {e}")

def clear_range(sheet, range_str, keep_merged=False):
    """Clear a range while optionally preserving merged cells."""
    try:
        if keep_merged:
            # For merged cells, we need to clear contents only
            sheet.Range(range_str).ClearContents()
        else:
            # For individual cells, we can try to clear them one by one
            rng = sheet.Range(range_str)
            for cell in rng.Cells:
                try:
                    cell.Clear()
                except:
                    print(f"Warning: Could not clear cell {cell.Address}")
    except Exception as e:
        print(f"Warning: Could not clear range {range_str}: {e}")

def replace_commas_with_periods(sheet):
    try:
        data_range = sheet.Range("D11:X53")
        for cell in data_range:
            try:
                if cell.Text and isinstance(cell.Text, str) and "," in cell.Text:
                    cell.Value = cell.Text.replace(",", ".")
            except Exception as e:
                print(f"Warning: Could not process cell {cell.Address}: {e}")
    except Exception as e:
        print(f"Warning: Could not replace commas with periods: {e}")

def save_print_sheet_as_pdf(wb, filepath):
    """Save the Print sheet as a PDF."""
    try:
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]
        output_pdf = os.path.join(os.path.dirname(filepath), f"{base_name}_Print.pdf")
        
        # Get the Print sheet but don't select it
        print_sheet = wb.Sheets("Print")
        
        # Try multiple times in case of Excel COM issues
        for attempt in range(3):
            try:
                print(f"\nAttempt {attempt + 1} of 3 to save PDF...")
                # Configure page setup to match settings
                print_sheet.PageSetup.Orientation = 1  # 1 = Portrait
                print_sheet.PageSetup.Zoom = False  # Disable zoom
                print_sheet.PageSetup.FitToPagesTall = 1
                print_sheet.PageSetup.FitToPagesWide = 1
                print_sheet.PageSetup.TopMargin = 1.9  # Match your margins exactly
                print_sheet.PageSetup.BottomMargin = 1.9
                print_sheet.PageSetup.LeftMargin = 1.8
                print_sheet.PageSetup.RightMargin = 1.8
                print_sheet.PageSetup.HeaderMargin = 0.8
                print_sheet.PageSetup.FooterMargin = 0.8
                print_sheet.PageSetup.CenterHorizontally = False
                print_sheet.PageSetup.CenterVertically = False
                print_sheet.PageSetup.Zoom = 100  # Set to 100% normal size
                
                # Export directly from the sheet without selecting it
                print_sheet.ExportAsFixedFormat(0, output_pdf)  # 0 = PDF format
                print(f"PDF saved to: {output_pdf}")
                return True
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(1)  # Wait a second before retrying
        
        return False
        
    except Exception as e:
        print(f"Error saving PDF: {e}")
        return False

def process_excel_file(excel_app, filepath, test_type, project_number):
    """Process an Excel file, performing necessary modifications and saving as PDF."""
    # Extract letter from filename (e.g., "NP-012432 - A.xlsx" -> "A", "NP-012432 - AA.xlsx" -> "AA")
    letter = os.path.basename(filepath).split(" - ")[1].split(".")[0]
    perf_value = None
    client_name = None
    receiving_room = None
    source_room = None
    
    print(f"\nProcessing {os.path.basename(filepath)} as {test_type} test...")
    
    try:
        print(f"\nOpening {filepath}...")
        wb = excel_app.Workbooks.Open(filepath)
        # When opening workbooks, try:
        excel_app.EnableEvents = True
        excel_app.AutomationSecurity = 1  # msoAutomationSecurityLow
        
        try:
            print("Getting sheets...")
            lang_sheet = wb.Sheets("LANG")
            data_sheet = wb.Sheets("Data")
            print_sheet = wb.Sheets("Print")
            
            Title = "Standardized Level Difference According to Resistance to the Passage of Sound Approved Document E"
            Airborne_subtitle = "Field Measurements of Airbourne Sound Insulation Between Rooms"
            Impact_subtitle = "Field Measurements of Impact Sound Insulation Between Rooms"
            
            # Set LANG sheet text based on test type
            cell = lang_sheet.Range("A2")
            cell.Value = Title
            #cell.Font.Bold = True
            #cell.Font.Size = 12
            #cell.Font.Name = "Arial"
            #cell.Font.Color = HexColor("000000")
            cell = print_sheet.Range("C2")
            cell.RowHeight = 37.5 
            #cell.VerticalAlignment = -4108
            #cell.HorizontalAlignment = -4108
            
            lang_text = Airborne_subtitle if test_type == "airborne" else Impact_subtitle
            print("\nUpdating LANG sheet...")
            lang_sheet.Range("A3").Value = lang_text
            
            # Get client name and room info from Data sheet
            client_name = data_sheet.Range("N2").Value
            receiving_room = data_sheet.Range("L2").Value
            
            # For impact tests, ask user for source room
            if test_type == "impact":
                potential_source = data_sheet.Range("L4").Value
                if potential_source: 
                    print(f"\nFound potential source room for impact test {filepath[-18:-5]}: \n{potential_source}")
                    source_room = input("Press Enter to confirm this source room or enter a new one:").strip()
                    if not source_room:
                        source_room = potential_source.strip()
                else:
                    print(f"\nEnter source room for impact test {filepath[-18:-5]} (e.g. 'Living Room Floor'):")
                    source_room = input().strip()
            else:
                source_room = data_sheet.Range("L3").Value  # For airborne tests, get from Data sheet
            
            # Get room volumes
            source_volume = data_sheet.Range("D2").Value
            receiving_volume = data_sheet.Range("C2").Value
            partition_area = data_sheet.Range("C1").Value

            print("\nProcessing Data sheet...")
            # Clear ranges
            clear_range(data_sheet, "D15:F15")
            clear_range(data_sheet, "D18:F18")
            clear_range(data_sheet, "W15:X15")
            clear_range(data_sheet, "W18:X18")
            clear_range(data_sheet, "D20:F20")
            clear_range(data_sheet, "W20:X20")
            clear_range(print_sheet, "H20:H22")
            clear_range(print_sheet, "H39:H40")
            
            print("\nReplacing commas with periods...")
            replace_commas_with_periods(data_sheet)
            
            print("\nGenerating acoustic charts...")
            add_and_run_macro(wb, test_type)
            
            print("\nProcessing Print sheet...")
            # Clear specific cells in row 5
            print("\nClearing row 5 cells...")
            for col in ["C5", "D5", "E5", "F5", "G5", "H5", "K5", "L5", "M5"]:
                try:
                    print_sheet.Range(col).Clear()
                except Exception as e:
                    print(f"Warning: Could not clear cell {col}: {e}")

            # Clear merged cells
            print("\nClearing merged cells...")
            try:
                # Unmerge and clear D20:D22 range
                range_d20_22 = print_sheet.Range("D20:D22")
                range_d20_22.UnMerge()
                range_d20_22.Clear()
                print("Successfully cleared D20:D22")
            except Exception as e:
                print(f"Warning: Could not clear range D20:D22: {e}")
                
            try:
                # Unmerge and clear D39:D40 range
                range_d39_40 = print_sheet.Range("D39:D40")
                range_d39_40.UnMerge()
                range_d39_40.Clear()
                # Add bottom border to D40
                print_sheet.Range("D40").Borders(9).LineStyle = 1  # 9 is xlEdgeBottom, 1 is xlContinuous
                print("Successfully cleared D39:D40 and added bottom border to D40")
            except Exception as e:
                print(f"Warning: Could not clear range D39:D40: {e}")
                
            try:
                # Unmerge and clear M5
                cell_m5 = print_sheet.Range("M5")
                cell_m5.UnMerge()
                cell_m5.Clear()
                print("Successfully cleared M5")
            except Exception as e:
                print(f"Warning: Could not clear cell M5: {e}")

            # Format D6 based on test type
            print("\nFormatting D6...")
            try:
                if test_type.startswith("AB"):  # Airborne test
                    merged_range = print_sheet.Range("D6:R6")
                else:  # Impact test
                    merged_range = print_sheet.Range("D6:V6")
                    
                merged_range.NumberFormat = "@"  # Text format
                merged_range.HorizontalAlignment = -4131  # Left
                merged_range.VerticalAlignment = -4108    # Center
                merged_range.Font.Size = 9
            except Exception as e:
                print(f"Warning: Could not format D6 merged range: {e}")

            # Calculate performance value from Print sheet
            print("\nCalculating performance value...")
            perf_value = None
            if test_type == "airborne":
                try:
                    Dnt = print_sheet.Range("D49").Value
                    Ctr = print_sheet.Range("H49").Value
                    if Dnt != "--" and Ctr != "--":
                        if abs(Ctr) >= 10:
                            print_sheet.Range("H49").ColumnWidth = 2.63
                        print(f"Print D49 value: {Dnt}")
                        print(f"Print H49 value: {Ctr}")
                        # For airborne, add D49 and H49 (H49 should be negative)
                        perf_value = Dnt + Ctr 
                        print(f"Calculated airborne performance: ({Dnt} + {Ctr}) = {perf_value}")
                except Exception as e:
                    print(f"Error calculating airborne performance: {e}")
            else:  # impact
                try:
                    Dnt = print_sheet.Range("D49").Value
                    if Dnt != "--":
                        print(f"Print D49 value: {Dnt}")
                        perf_value = int(Dnt)
                        print(f"Performance value (D49): {perf_value}")
                except Exception as e:
                    print(f"Error calculating impact performance: {e}")
            
            # Clear old test number
            clear_range(print_sheet, "I53")

            # Set test number E53 value
            print("\nSetting E53 value...")
            try:
                cell_e53 = print_sheet.Range("E53")
                cell_e53.Value = f"{project_number} - {letter}"
                cell_e53.Font.Name = "Arial"
                cell_e53.Font.Size = 9
                print(f"Set E53 value to '{project_number} - {letter}'")
            except Exception as e:
                print(f"Warning: Could not set E53 value: {e}")

            # Set S53 text
            print("\nSetting S53 text...")
            cell = print_sheet.Range("S53")
            cell.ClearContents()  # Clear first
            cell.Value = "Nova Acoustics Ltd."
            cell.Font.Name = "Arial"
            cell.Font.Size = 9
            
            # Set D9 text with Arial 9
            print("\nSetting D9 text...")
            cell = print_sheet.Range("D9")
            cell.Value = "See Pages 1 & 2"
            cell.Font.Name = "Arial"
            cell.Font.Size = 9
            
            delete_range = "10:12"  # Delete entire rows to handle missmatched test file size on other computers
            print(f"Deleting rows {delete_range}")
            try:
                # Delete rows using right-click delete simulation
                for i in range(10, 12):
                    print_sheet.Rows(i).Delete(Shift=-4162)  # -4162 is xlUp constant
            except Exception as e:
                print(f"Warning: Could not delete rows {delete_range}: {e}")

            # Save workbook
            print("\nSaving workbook...")
            wb.Save()
            
            # Export to PDF
            print("\nExporting to PDF...")
            output_pdf = filepath.replace(".xlsx", "_Print.pdf")
            
            # Try up to 3 times to save the PDF
            for attempt in range(3):
                try:
                    print(f"\nAttempt {attempt + 1} of 3 to save PDF...")
                    print_sheet.ExportAsFixedFormat(0, output_pdf)
                    print(f"PDF saved to: {output_pdf}")
                    break
                except Exception as e:
                    if attempt == 2:  # Last attempt failed
                        print(f"Failed to save PDF after 3 attempts: {e}")
                        raise
                    time.sleep(1)  # Wait a second before retrying
            
            print("\nSaving and closing...")
            return perf_value, client_name, receiving_room, source_room, receiving_volume, source_volume, partition_area
            
        except Exception as e:
            print(f"Error processing workbook: {e}")
            return None
        finally:
            wb.Close()
            
    except Exception as e:
        print(f"Error opening workbook: {e}")
        return None

def get_test_types(num_tests):
    """Get test types from user for all tests at once."""
    while True:
        print("\nEnter test types as a comma-separated list")
        print("Use ABW/ABF for airborne tests, IPF for impact tests")
        print(f"Example: {','.join(['ABW' if i % 2 == 0 else 'IPF' for i in range(num_tests)])}")
        print("Your input: ", end='')
        
        test_types = input().strip().upper().split(',')
        
        # Validate length
        if len(test_types) != num_tests:
            print(f"Error: Please enter exactly {num_tests} test types!")
            continue
        
        # Validate each type
        valid_types = {'ABW', 'ABF', 'IPF'}
        invalid_types = [t for t in test_types if t not in valid_types]
        if invalid_types:
            print(f"Error: Invalid test type(s): {', '.join(invalid_types)}")
            print("Valid types are: ABW, ABF, IPF")
            continue
        
        return test_types

def get_kit_and_calibration():
    """Get kit selection and calibration values from user."""
    # Ask user to select kit
    print("\nPlease select which kit was used:")
    print("1. Kit 1")
    print("2. Kit 2")
    print("3. Kit 3")
    print("4. Kit 4")
    print("5. Kit 5")
    print("6. Kit 6")
    
    while True:
        try:
            kit_num = int(input("Enter kit number (1-6): "))
            if 1 <= kit_num <= 6:
                break
            print("Please enter a number between 1 and 6")
        except ValueError:
            print("Please enter a valid number")
    
    # Get calibration values
    while True:
        try:
            pre_cal = float(input("\nEnter pre-calibration value (e.g. 114.05): "))
            post_cal = float(input("Enter post-calibration value (e.g. 114.05): "))
            # Basic validation - calibration values are typically around 114 dB
            if 110 <= pre_cal <= 118 and 110 <= post_cal <= 118:
                break
            print("Calibration values should typically be between 110 and 118 dB")
            if input("Are you sure these values are correct? (y/n): ").lower() == 'y':
                break
        except ValueError:
            print("Please enter valid numbers with up to 2 decimal places")
    
    return kit_num, pre_cal, post_cal


def write_to_onsite_worksheet(excel_app, source_dir, test_data, project_number, test_types):
    """
    Write test data to the Onsite Worksheet.xlsx file.
    test_data is a list of tuples: (letter, test_type, perf_value, client_name, receiving_room, source_room)
    """
    try:
        # Copy template to project directory
        template_path = os.path.join(TEMPLATES_PATH, "Blank_Onsite_Worksheet.xlsx")
        if not os.path.exists(template_path):
            print(f"Error: Template not found at {template_path}")
            return False
            
        filepath = os.path.join(source_dir, f"{project_number}_Onsite_Worksheet.xlsx")
        shutil.copy2(template_path, filepath)
        
        print("\nWriting data to Onsite Worksheet...")
        wb = open_workbook_with_editing(excel_app, filepath)
        
        # Get the Sound Test Report sheet
        ws = wb.Sheets("Sound Test Report")
        
        # Write project number
        ws.Range("D7").Value = project_number
        print(f"Wrote project number '{project_number}' to cell D7")

        # Write previous job number if applicable
        associated_job = get_associated_job()
        if associated_job:
            ws.Range("D8").Value = associated_job
            print(f"Wrote associated job '{associated_job}' to cell D8")
        else:
            ws.Range("D8").Value = "N/A"
            print("Wrote 'N/A' to cell D8")
        
        # Write client name (use the first one since it should be the same for all tests)
        if test_data and len(test_data) > 0 and test_data[0][3]:
            ws.Range("D9").Value = test_data[0][3]
            print(f"Wrote client name '{test_data[0][3]}' to cell D9")
        
        print("\nFetching addresses from Insightly...")
        billing_address, site_address = get_project_details(project_number, test_data[0][3])
        
        # Trim addresses at postcode
        if billing_address:
            billing_address = trim_at_postcode(billing_address)
        if site_address:
            site_address = trim_at_postcode(site_address)
        
        # Write addresses to worksheet
        if billing_address:
            ws.Range("D10").Value = billing_address
            print(f"Wrote billing address to cell D10: {billing_address}")
        if site_address:
            ws.Range("D13").Value = site_address
            print(f"Wrote site address to cell D13: {site_address}")
        
        # Write test date from first test file
        if test_data and len(test_data) > 0:
            first_test = test_data[0]
            if first_test:
                # Get the first test letter from the test data
                first_letter = first_test[0]  # test[0] is the letter
                first_test_path = os.path.join(source_dir, f"{project_number} - {first_letter}.xlsx")
                if os.path.exists(first_test_path):
                    data_wb = excel_app.Workbooks.Open(first_test_path)
                    try:
                        data_sheet = data_wb.Sheets("Data")
                        test_date = data_sheet.Range("C6").Value
                        if test_date:
                            formatted_date = format_date(str(test_date))
                            ws.Range("D16").Value = formatted_date
                            print(f"Wrote test date '{formatted_date}' to cell D16")
                    finally:
                        data_wb.Close()
        
        # Get kit selection and calibration values
        kit_num, pre_cal, post_cal = get_kit_and_calibration()
        
        # Write kit number to Sound Test Report sheet
        ws.Range("D19").Value = f"Kit {kit_num}"
        print(f"Wrote kit number to cell D19: Kit {kit_num}")
        
        # Get the Calibration sheet
        cal_ws = wb.Sheets("Calibration")
        
        # Write calibration values based on kit number
        cal_ranges = {
            1: ("C10", "G10"),
            2: ("K10", "O10"),
            3: ("C22", "G22"),
            4: ("K22", "O22"),
            5: ("C33", "G33"),
            6: ("K33", "O33")
        }
        
        pre_cal_cell, post_cal_cell = cal_ranges[kit_num]
        cal_ws.Range(pre_cal_cell).Value = pre_cal
        cal_ws.Range(post_cal_cell).Value = post_cal
        print(f"Wrote calibration values to Calibration sheet: {pre_cal} (pre) and {post_cal} (post)")
        
        # Get property type from user
        property_type = get_property_type()
        ws.Range("D18").Value = property_type
        print(f"Wrote property type '{property_type}' to cell D18")
        
        # Set specific row heights for rows 26-37
        row_heights = [28, 14, 28, 14, 14, 56, 28, 14, 28, 14, 14, 42]  # in pixels
        for i, height in enumerate(row_heights):
            row = 26 + i  # Start at row 26
            ws.Rows(row).RowHeight = height * 0.75  # Convert pixels to points
        print("Set row heights for rows 26-37")

        # Write test data and set row heights
        start_row = 47  # Starting row for test data
        test_deviations, unique_deviations, deviation_mapping = get_deviations(wb, len(test_data))
        
        # Set row heights first
        for i in range(len(test_data)):
            row = start_row + i
            ws.Rows(row).RowHeight = 33 * 0.75  # 33 pixels = 24.75 points
        
        # Write deviation texts with sequential numbers in cell A23
        deviation_cell = ws.Range("A23")
        deviation_texts = []
        for orig_num in unique_deviations:
            text = format_deviation_text(orig_num)
            if text:
                new_num = deviation_mapping[orig_num]
                cell_text = f"{text}{new_num}"
                # Add to list for final joining
                deviation_texts.append(cell_text)
        
        # Join all deviation texts and write to cell
        if deviation_texts:
            # Format each deviation text with superscript numbers
            formatted_texts = []
            for text in deviation_texts:
                # Find the number at the end of the text
                base_text = text[:-1]  # Everything except the last character (the number)
                number = text[-1]      # The last character (should be the number)
                # Format with Unicode superscript
                formatted_texts.append(f"{to_superscript(number, include_separator=False)}{base_text}")
            
            # Join all formatted texts with normal commas and write to cell
            final_text = ", ".join(formatted_texts)
            deviation_cell.Value = final_text
            print(f"Wrote formatted deviations to cell A23: {final_text}")
            # No need for additional formatting since we're using ^N notation
        # If deviation test is empty, write N/A to cell
        else:
            deviation_cell.Value = "N/A"
            print("Wrote 'N/A' to cell A23")

        for i, test in enumerate(test_data):
            if test[0] is not None:  # test[0] is the letter
                row = start_row + i
                cell = ws.Cells(row, 1)  # Column A
                letter = test[0]
                
                # Get deviations for this test and convert to sequential numbers
                test_devs = test_deviations.get(letter, [])
                if test_devs:
                    # Convert original numbers to sequential numbers and join with commas
                    sequential_nums = [str(deviation_mapping[dev]) for dev in test_devs]
                    # Add spaces between numbers and separators
                    spaced_nums = '⸴ '.join(sequential_nums)
                    numbers_text = to_superscript(spaced_nums, include_separator=True)
                    cell.Value = f"{letter}{numbers_text}"
                else:
                    cell.Value = letter
        
        # Write test types to column B
        for i, test_type in enumerate(test_types):
            row = start_row + i
            ws.Cells(row, 2).Value = test_type  # Column B
        
        # Write source rooms to column C
        for i, test in enumerate(test_data):
            if test[5]:  # test[5] is source room
                row = start_row + i
                ws.Cells(row, 3).Value = test[5]  # Column C
        
        # Write receiving rooms to column E
        for i, test in enumerate(test_data):
            if test[4]:  # test[4] is receiving room
                row = start_row + i
                ws.Cells(row, 5).Value = test[4]  # Column E
        
        # Write performance values to column G
        for i, test in enumerate(test_data):
            if test[2] is not None:  # test[2] is performance value
                row = start_row + i
                ws.Cells(row, 7).Value = test[2]  # Column G
                final_row = row

        # Collect Test Failures
        test_failures = []
        for i, test in enumerate(test_data):
            if test[2] is not None:  # test[2] is performance value
                row = start_row + i
                if ws.Cells(row, 11).Value  == "Fail": # Column K is pass or fail
                    test_failures.append(test)
                final_row = row
        
        # Write test failures
        if test_failures:
            fws = wb.Sheets("Failure Checks")
            write_test_failures(test_failures, fws)

        # Import notes if available
        notes_content = import_notes_file(project_number, source_dir)
        if notes_content:
            notes_ws = wb.Sheets("General Testing Notes")
            notes_ws.Cells(2, "A").Value = notes_content
            notes_ws.Columns("A").ColumnWidth = 120
            print("Imported notes to General Testing Notes worksheet")
        
        '''# Delete rows after the last test up to row 74
        if test_data:
            last_test_row = start_row + len(test_data)
            if last_test_row < 74:
                #ws.Cells(75, "A").Value = "Table 1.0 - Sound Insulation Test Results"
                delete_range = f"{last_test_row + 1}:74"
                print(f"Deleting rows {delete_range}")
                ws.Range(delete_range).Delete()'''
        
        # Delete rows after the last test up to row 74
        if test_data:
            #last_test_row = start_row + len(test_data)
            if final_row < 147:
                delete_range = f"{final_row + 1}:147"  # Specify full column range A to M
                print(f"Deleting rows {delete_range}")
                try:
                    # Delete rows using right-click delete simulation
                    for i in range(final_row + 1, 146):
                        ws.Rows(final_row + 1).Delete(Shift=-4162)  # -4162 is xlUp constant
                        i += 1
                    #ws.Cells("A", last_test_row + 1).Value = "Table 1.0 - Sound Insulation Test Results"
                except Exception as e:
                    print(f"Warning: Could not delete rows {delete_range}: {e}")

        
        # Save the worksheet
        print("Saving Onsite Worksheet...")
        onsite_path = os.path.join(source_dir, f"{project_number}_Onsite_Worksheet.xlsx")
        wb.SaveAs(onsite_path)
        print(f"Saved Onsite Worksheet as: {os.path.basename(onsite_path)}")
        
        print("Do you want to manually review the onsite worksheet before exporting to pdf? (y/n)")
        answer = input("(y/n): ").strip().lower()
        if answer == "y":
            try:
                wb = manual_review(wb)
                print("Onsite worksheet has been saved, now will export as PDF.")
            except Exception as e:
                print(f"\nManual review error: {e}")
                print("Attempting to reopen workbook for PDF export...")
                # Reopen the workbook
                wb = excel_app.Workbooks.Open(onsite_path)
                ws = wb.Sheets("Sound Test Report")

        # Export Sound Test Report as doc1.pdf
        output_pdf = os.path.join(source_dir, "doc1.pdf")
        
        # Try to export, with retry if workbook was closed
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                ws.ExportAsFixedFormat(0, output_pdf)
                print(f"Exported Sound Test Report as: {os.path.basename(output_pdf)}")
                break
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"\nError exporting PDF: {e}")
                    print("Attempting to reopen workbook...")
                    try:
                        wb.Close()
                    except:
                        pass
                    # Reopen the workbook
                    wb = excel_app.Workbooks.Open(onsite_path)
                    ws = wb.Sheets("Sound Test Report")
                else:
                    raise
        
        # Close the workbook after all operations are complete
        try:
            wb.Close()
        except:
            print("Warning: Could not close workbook (may already be closed)")

        '''# Now check for failures
        check_for_failures(excel_app, source_dir, project_number)'''
        
        return True
    except Exception as e:
        print(f"Error writing to Onsite Worksheet: {e}")
        return False

def manual_review(workbook):
    """Open the worksheet for manual check, then save and export to PDF.
    
    Args:
        workbook: Workbook object to modify
    """
    
    try:
        # Show instructions to user
        print("\nCheck over all entries made to the onsite worksheet:")
        print("1. Press Enter to begin")
        print("2. Make alterations where needed")
        print("3. When finished, press Enter in this console")
        input("\nPress Enter to begin...")

        # Make Excel visible
        workbook.Application.Visible = True
        workbook.Application.WindowState = -4137  # xlMaximized
        workbook.Application.DisplayAlerts = False

        print("\nExcel is now open.")
        print("Make your changes, then come back here.")
        print("IMPORTANT: Do NOT close Excel - just press Enter here when done.")
        # Just wait for Enter - no y/n confirmation needed
        input("Press Enter when you have finished editing...")

        # Check if workbook is still open
        try:
            # Try to access workbook - will fail if closed
            _ = workbook.Name
            # Workbook is still open, so save and hide it
            workbook.Application.Visible = False
            workbook.Save()
            print("Workbook saved and closed.")
        except:
            # Workbook was closed manually - that's okay, assume user saved it
            print("\nWorkbook was closed manually. Assuming changes were saved.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
    return workbook

def import_notes_file(project_number, source_dir):
    """Find and read notes file content.
    Args:
        project_number: Project number to look for notes file
        source_dir: Directory to copy the notes file to
    Returns:
        str: The contents of the notes file if found, None otherwise
    """
    gdrive_path = r"G:\My Drive"
    notes_path = f"{project_number}_Notes.txt"
    dest = os.path.join(source_dir, notes_path)

    def check_notes_file(filepath):
        """Check if a notes file exists and ask user if it's correct."""
        if os.path.exists(filepath):
            print(f"\nFound notes file: {os.path.basename(filepath)}")
            response = input("Is this the correct notes file? (y/n): ").lower().strip()
            if response == 'y':
                return filepath
        return None

    # First try looking in the source directory with various naming patterns
    clean_number = project_number.replace('NP-', '')
    possible_filenames = [
        f"{project_number}notes.txt",
        f"{project_number} notes.txt",
        f"{project_number}-notes.txt",
        f"{project_number}_notes.txt",
        f"{clean_number}notes.txt",
        f"{clean_number} notes.txt",
        f"{clean_number}-notes.txt",
        f"{clean_number}_notes.txt"
    ]
    
    notes_path = None
    for filename in possible_filenames:
        filepath = os.path.join(gdrive_path, filename)
        notes_path = check_notes_file(filepath)
        if notes_path:
            break
            
    if not notes_path:
        print("\nNo notes file found automatically.")
        print("1. Import a notes file")
        print("2. Write notes directly")
        print("3. Skip notes")
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice == '1':
            print("\nPlease enter the full path to your notes file:")
            notes_path = input().strip()
            if not os.path.exists(notes_path):
                print("Error: File not found")
                return None
                
        elif choice == '2':
            print("\nEnter your notes (press Enter twice when done):")
            notes_lines = []
            while True:
                line = input()
                if line == "" and notes_lines and notes_lines[-1] == "":
                    notes_lines.pop()
                    break
                notes_lines.append(line)
            
            notes_content = '\n'.join(notes_lines)
            with open(dest, 'w') as f:
                f.write(notes_content)
            print(f"Notes saved to {dest}")
            return notes_content
            
        else:
            print("Skipping notes")
            return None

    # Only runs if we have a valid file path
    if notes_path and os.path.exists(notes_path):
        if not os.path.exists(dest):
            print(f"Copying {notes_path} to project directory...")
            shutil.copy2(notes_path, dest)
        else:
            print(f"File already exists in project directory: {dest}")

        with open(notes_path, 'r') as f:
            notes_content = f.read()
            print("Notes file read successfully")
            return notes_content

    return None



def setup_project_directory(project_number, num_tests):
    """
    Set up a new project directory with required template files.
    
    Args:
        project_number: The project number (e.g., 'NP-012345')
        num_tests: Number of tests we expect to find
        
    Returns:
        tuple: (project_dir_path, found_all_files)
    """
    try:
        # Define paths
        base_dir = DESKTOP_PATH + r"\SIT"
        
        # Create base SIT directory if it doesn't exist
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            print(f"Created SIT directory: {base_dir}")
            
        templates_dir = TEMPLATES_PATH
        print(F"Path to Templates {TEMPLATES_PATH}")
        project_dir = os.path.join(base_dir, project_number)
        print(F"Path to Project {project_dir}")
        
        # Delete existing directory if it exists
        if os.path.exists(project_dir):
            try:
                shutil.rmtree(project_dir)
                print(f"Deleted existing project directory: {project_dir}")
            except Exception as e:
                print(f"Warning: Could not delete existing project directory: {e}")
        
        # Create project directory
        print(f"Creating project directory: {project_dir}")
        os.makedirs(project_dir)
        
        # List of template files to copy
        template_files = [
            "Front Page.pdf",
            "Back Page.pdf",
            "Blank_Onsite_Worksheet.xlsx"
        ]
        
        # Copy each template file
        for template in template_files:
            source = os.path.join(templates_dir, template)
            if template == "Blank_Onsite_Worksheet.xlsx":
                # Rename the onsite worksheet with project number
                dest = os.path.join(project_dir, f"{project_number}_Onsite_Worksheet.xlsx")
            else:
                dest = os.path.join(project_dir, template)
            print(F"Source: {source}")
            print(F"Destination: {dest}")

            if os.path.exists(source):
                if not os.path.exists(dest):
                    print(f"Copying {template} to project directory...")
                    shutil.copy2(source, dest)
                else:
                    print(f"File already exists in project directory: {dest}")
            else:
                print(f"Warning: Template file not found: {source}")
        
        while True:
            # Find and copy test files from Google Drive
            test_files, found_all = find_test_files(project_number, num_tests)
            
            if not test_files and not found_all:
                print("\nNo test files found. What would you like to do?")
                print("1. Search again")
                print("2. Continue anyway")
                print("3. End program")
                
                choice = input("\nEnter your choice (1-3): ").strip()
                if choice == "1":
                    continue
                elif choice == "2":
                    break
                else:
                    return None, False
            
            elif not found_all:
                print("\nWhat would you like to do?")
                print("1. Search again")
                print("2. Continue with found files")
                print("3. End program")
                
                choice = input("\nEnter your choice (1-3): ").strip()
                if choice == "1":
                    continue
                elif choice == "2":
                    break
                else:
                    return None, False
            
            # Copy found files to project directory with standardized names
            for source_path, letter in test_files:
                # Use standardized name format
                new_name = f"{project_number} - {letter}.xlsx"
                dest = os.path.join(project_dir, new_name)
                
                if not os.path.exists(dest):
                    print(f"Copying and renaming: {os.path.basename(source_path)} -> {new_name}")
                    shutil.copy2(source_path, dest)
                else:
                    print(f"Test file already exists in project directory: {new_name}")
            
            return project_dir, True
        
        return project_dir, False
        
    except Exception as e:
        print(f"Error setting up project directory: {e}")
        return None, False

def write_test_failures(test_failures, fws):
    """Write failed test data to the Failure Checks worksheet."""
    
    # Define cell mappings for each failure (up to 5 failures)
    failure_test_ref_cells = ["B2", "B11", "B19", "B27", "B35"]
    source_room_volume_cells = ["B3", "B12", "B20", "B28", "B36"]
    receiving_room_volume_cells = ["B4", "B13", "B21", "B29", "B37"]
    partition_area_cells = ["B5", "B14", "B22", "B30", "B38"]
    notes_on_failure_cells = ["B8", "B16", "B24", "B32", "B40"]
    summary_of_client_advice_cells = ["B9", "B17", "B25", "B33", "B41"]
    
    # Write data for each failed test
    for i, test in enumerate(test_failures):
        if i >= 5:  # Only handle up to 5 failures
            print(f"Warning: More than 5 failures detected. Only first 5 will be written.")
            break
            
        # Extract test data
        # test structure: (letter, test_type, perf_value, client_name, receiving_room, source_room, receiving_volume, source_volume, partition_area)
        letter = test[0]
        receiving_volume = test[6]
        source_volume = test[7]
        partition_area = test[8]
        
        # Write test reference (e.g., "Test A")
        fws.Range(failure_test_ref_cells[i]).Value = f"Test {letter}"
        
        # Write source room volume
        fws.Range(source_room_volume_cells[i]).Value = source_volume
        
        # Write receiving room volume
        fws.Range(receiving_room_volume_cells[i]).Value = receiving_volume
        
        # Write partition area
        fws.Range(partition_area_cells[i]).Value = partition_area
        
        # Notes and advice cells are left empty for manual entry
    
    print(f"Wrote {len(test_failures)} failed test(s) to Failure Checks worksheet")


def find_test_files(project_number, expected_count):
    """
    Find test files for a project in Google Drive root folder.
    Files should be named like "NP-012345 - A.xlsx" or "NP-012345 - AA.xlsx"
    
    Args:
        project_number: The project number (e.g., 'NP-012345')
        expected_count: Number of test files we expect to find
        
    Returns:
        list: List of paths to test files found
        bool: True if all expected files were found
    """
    try:
        gdrive_path = r"G:\My Drive"
        test_files = []
        
        # Clean project number (remove NP- if present)
        clean_number = project_number.replace('NP-', '')
        
        print(f"\nSearching for {expected_count} test files in Google Drive root folder...")
        
        # Only search files in the root folder (no recursion)
        try:
            for file in os.listdir(gdrive_path):
                file_path = os.path.join(gdrive_path, file)
                if os.path.isfile(file_path) and file.endswith(".xlsx"):
                    # Match various possible formats:
                    # NP-012345 - A.xlsx, NP-012345 - AA.xlsx
                    # NP012345 - A.xlsx, NP012345 - AA.xlsx
                    # NP-012345-A.xlsx, NP-012345-AA.xlsx
                    # NP012345A.xlsx, NP012345AA.xlsx
                    basename = os.path.splitext(file)[0]
                    
                    # Try to extract the test letter(s)
                    test_letter = None
                    
                    if " - " in basename:
                        # Format: "NP-012345 - A" or "NP-012345 - AA"
                        parts = basename.split(" - ")
                        if len(parts) == 2:
                            potential_letter = parts[1].strip()
                            # Check if it's 1 or 2 letters
                            if len(potential_letter) in [1, 2] and potential_letter.isalpha():
                                test_letter = potential_letter.upper()
                    else:
                        # Format: "NP-012345-A", "NP012345A", "NP-012345-AA", "NP012345AA"
                        # Remove any hyphens and "NP" prefix
                        stripped = basename.replace('-', '').replace('NP', '')
                        # Extract trailing letters (1 or 2 characters)
                        if len(stripped) > 0:
                            # Try 2 letters first
                            if len(stripped) >= 2 and stripped[-2:].isalpha():
                                # Check if both are letters and the rest is the project number
                                potential_letter = stripped[-2:]
                                remaining = stripped[:-2]
                                if remaining == clean_number:
                                    test_letter = potential_letter.upper()
                            # Try 1 letter if 2-letter didn't match
                            if not test_letter and stripped[-1].isalpha():
                                potential_letter = stripped[-1]
                                remaining = stripped[:-1]
                                if remaining == clean_number:
                                    test_letter = potential_letter.upper()
                    
                    # If we found a letter and the number matches
                    if test_letter and (basename.startswith(f"NP-{clean_number}") or 
                                      basename.startswith(f"NP{clean_number}") or
                                      basename.startswith(clean_number)):
                        test_files.append((file_path, test_letter))
        except Exception as e:
            print(f"Error accessing Google Drive folder: {e}")
            return [], False
        
        # Sort files by test letter using parse_test_letter for proper ordering
        test_files.sort(key=lambda x: parse_test_letter(x[1]) if parse_test_letter(x[1]) is not None else 999)
        
        if test_files:
            print(f"\nFound {len(test_files)} test files:")
            for file_path, letter in test_files:
                print(f"  - {os.path.basename(file_path)} -> {project_number} - {letter}.xlsx")
            
            if len(test_files) < expected_count:
                print(f"\nWarning: Found fewer files than expected ({len(test_files)} vs {expected_count})")
                missing_letters = []
                found_letters = {letter.upper() for _, letter in test_files}
                
                # Check which letters are missing
                for i in range(expected_count):
                    letter = get_test_letter(i)  # A, B, C, ..., Z, AA, AB, etc.
                    if letter not in found_letters:
                        missing_letters.append(letter)
                
                if missing_letters:
                    print(f"Missing test files for: {', '.join(missing_letters)}")
                return test_files, False
            
            elif len(test_files) > expected_count:
                print(f"\nWarning: Found more files than expected ({len(test_files)} vs {expected_count})")
                return test_files, False
            
            return test_files, True
        
        else:
            print("No test files found in Google Drive root folder")
            return [], False
        
    except Exception as e:
        print(f"Error searching for test files: {e}")
        return [], False

def merge_pdfs(source_dir, project_number, num_tests):
    """Merge all PDFs into a single report."""
    try:
        # Create a list of PDFs in the correct order
        pdfs = []
        
        # Front page
        front_page = os.path.join(source_dir, "Front Page.pdf")
        if os.path.exists(front_page):
            pdfs.append(front_page)
            print("Adding Front Page.pdf")
        
        # Doc1 (Onsite Worksheet)
        doc1_pdf = os.path.join(source_dir, "doc1.pdf")
        if os.path.exists(doc1_pdf):
            pdfs.append(doc1_pdf)
            print("Adding doc1.pdf")
        
        # Test PDFs in order
        for i in range(num_tests):
            letter = get_test_letter(i)  # A, B, C, ..., Z, AA, AB, etc.
            test_pdf = os.path.join(source_dir, f"{project_number} - {letter}_Print.pdf")
            if os.path.exists(test_pdf):
                pdfs.append(test_pdf)
                print(f"Adding {project_number} - {letter}_Print.pdf")
        
        # Back page
        back_page = os.path.join(source_dir, "Back Page.pdf")
        if os.path.exists(back_page):
            pdfs.append(back_page)
            print("Adding Back Page.pdf")
        
        if not pdfs:
            print("No PDFs found to merge")
            return False
            
        # Merge PDFs
        output_pdf = os.path.join(source_dir, f"{project_number} - Sound Insulation Test Report - NOVA Acoustics Ltd.pdf")
        
        for attempt in range(3):
            try:
                print(f"\nAttempt {attempt + 1} of 3 to merge PDFs...")
                merger = PdfMerger()
                
                # Add all PDFs
                for pdf in pdfs:
                    merger.append(pdf)
                
                # Write merged PDF
                print(f"Writing merged PDF to: {os.path.basename(output_pdf)}")
                merger.write(output_pdf)
                merger.close()
                
                # Add page numbers (skip first and last pages)
                temp_pdf = os.path.join(source_dir, "temp_with_numbers.pdf")
                pages_to_number = list(range(1, len(pdfs)))  # Include all pages except the first
                add_page_numbers_to_pdf(output_pdf, temp_pdf, pages_to_number)
                
                # Replace original with numbered version
                os.replace(temp_pdf, output_pdf)
                
                print(f"Final report saved as: {os.path.basename(output_pdf)}")
                return True
                
            except PermissionError:
                if attempt < 2:
                    wait_time = (attempt + 1) * 2
                    print(f"Permission denied. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                if attempt < 2:
                    wait_time = (attempt + 1) * 2
                    print(f"Error: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise
                    
    except Exception as e:
        print(f"Error merging PDFs: {e}")
        return False

def create_page_number_overlay(page_num, total_num):
    """Create a PDF overlay with page numbers."""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)

    # Light grey font color
    can.setFillColor(HexColor("#B3B3B3"))  # Matches common light gray used in PDFs
    can.setFont("Arial", 8)

    # Bottom-left position, close to margin
    x = 40
    y = 20
    can.drawString(x, y, f"Page {page_num} of {total_num}.")

    can.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]

def add_page_numbers_to_pdf(input_path, output_path, pages_to_number):
    """Add page numbers to specified pages in a PDF."""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    numbered_page_index = 1  # Actual printed page number (starts at 1)
    total_numbered_pages = len(pages_to_number)

    for i, page in enumerate(reader.pages):
        if i in pages_to_number:
            overlay = create_page_number_overlay(numbered_page_index, total_numbered_pages)
            page.merge_page(overlay)
            numbered_page_index += 1
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

def organise_project_dir(project_dir, project_number):
    
    # Define directory paths
    Measurments_dir = os.path.join(project_dir, "Measurments")
    Reports_dir = os.path.join(project_dir, "Reports")
    Data_dir = os.path.join(DESKTOP_PATH, "SIT", "Data", project_number)
    output_pdf_string = f"{project_number} - Sound Insulation Test Report - NOVA Acoustics Ltd.pdf"
    output_pdf = os.path.join(project_dir, output_pdf_string) 

    try:
        # Create subdirectories if they don't exist
        os.makedirs(Reports_dir, exist_ok=True)
        os.makedirs(Measurments_dir, exist_ok=True)
        
        # Move all files except output_pdf to Reports folder
        for file in os.listdir(project_dir):
            file_path = os.path.join(project_dir, file)
            if os.path.isfile(file_path) and file_path != output_pdf:
                shutil.move(file_path, os.path.join(Reports_dir, file))
        
        # Copy all files from Data directory to Measurements directory
        if os.path.exists(Data_dir):
            for file in os.listdir(Data_dir):
                file_path = os.path.join(Data_dir, file)
                if os.path.isfile(file_path):
                    shutil.copy(file_path, os.path.join(Measurments_dir, file))
    
        print(f"Organized project directory: {project_dir}")
    
    except Exception as e:
        print(f"Error organizing project directory: {e}")

def main():
    try:
        # Get project number from user
        print("\nEnter the project number:")
        project_number = input().strip().upper()
        while not project_number or not project_number.startswith("NP-"):
            print("Error: Project number must start with 'NP-'!")
            project_number = input().strip().upper()
        
        # Get number of tests
        while True:
            try:
                print("\nEnter the number of tests:")
                num_tests = int(input().strip())
                if num_tests > 0:
                    break
                print("Error: Number must be greater than 0!")
            except ValueError:
                print("Error: Please enter a valid number!")
        
        # Get test types for all tests at once
        test_types = get_test_types(num_tests)
        
        # Set up project directory
        project_dir, found_all_files = setup_project_directory(project_number, num_tests)
        if not project_dir:
            print("Failed to set up project directory")
            return
        
        # Initialize Excel application
        excel_app = open_excel_app()
        
        try:
            test_data = []
            
            # Process each test
            for i in range(num_tests):
                # Determine test type based on code
                test_type = "airborne" if test_types[i] in ['ABW', 'ABF'] else "impact"
                
                # Process file
                letter = get_test_letter(i)  # A, B, C, ..., Z, AA, AB, etc.
                filename = f"{project_number} - {letter}.xlsx"
                filepath = os.path.join(project_dir, filename)
                
                if not os.path.exists(filepath):
                    print(f"File {filename} not found in {project_dir}!")
                    continue
                
                print(f"Processing {filename} as {test_type} test...")
                
                # Process the test file and add data
                result = process_excel_file(excel_app, filepath, test_type, project_number)
                if result:
                    test_data.append((letter, test_type, *result))
            
            # Write data to Onsite Worksheet
            if test_data:
                write_to_onsite_worksheet(excel_app, project_dir, test_data, project_number, test_types)
                
            # Merge PDFs into final report
            merge_pdfs(project_dir, project_number, num_tests)

            # Organise project directory
            organise_project_dir(project_dir, project_number)  

        finally:
            # Always close Excel
            excel_app.Quit()
            
    except Exception as e:
        print(f"An error occurred: {e}")
        try:
            excel_app.Quit()
        except:
            pass

if __name__ == "__main__":
    main()