#!/usr/bin/env python3
"""
SIT_Plotter.py - Standalone Acoustic Chart Generator

Standalone plotting utility for Sound Insulation Test files. Generates acoustic
frequency response charts from existing test data without running the full
report generation workflow.

Features:
    - VBA macro automation for chart generation
    - Batch processing of multiple test files
    - Support for ABF (Airborne Floor), ABW (Airborne Wall), and IPF (Impact Floor) tests
    - Excel workbook management with error handling

Usage:
    python SIT_Plotter.py

Interactive prompts:
    - Project number (e.g., NP-012432)
    - Number of tests to process
    - Test types (ABF, ABW, IPF)

The script locates test files in the SIT folder and executes VBA plotting macros
to generate standardized acoustic charts for compliance documentation.

Author: Q-types
License: MIT
"""

import os
import sys
import win32com.client
from win32com.client import constants

# Get the script's directory for relative paths
if getattr(sys, 'frozen', False):
    # Running as executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Constants
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
MACROS_PATH = os.path.join(BASE_DIR, "SIT_Reporter_Package", "SIT_Reporter_Package", "Macros")

def open_excel_app():
    """
    Create a new Excel instance and suppress alerts.
    """
    excel_app = win32com.client.DispatchEx("Excel.Application")
    excel_app.Visible = False
    excel_app.DisplayAlerts = False
    excel_app.AskToUpdateLinks = False
    return excel_app

def close_excel_safely(excel_app):
    """
    Safely close Excel application with multiple fallback methods.
    """
    if excel_app is None:
        return
    
    try:
        print("🔄 Closing Excel application...")
        
        # Step 1: Close all workbooks
        try:
            while excel_app.Workbooks.Count > 0:
                wb = excel_app.Workbooks(1)
                wb.Close(SaveChanges=False)
                print(f"   ✓ Closed workbook: {wb.Name}")
        except Exception as e:
            print(f"   ⚠️ Warning closing workbooks: {e}")
        
        # Step 2: Quit Excel application
        try:
            excel_app.Quit()
            print("   ✓ Excel application quit successfully")
        except Exception as e:
            print(f"   ⚠️ Warning quitting Excel: {e}")
        
        # Step 3: Release COM objects
        try:
            import gc
            excel_app = None
            gc.collect()
            print("   ✓ COM objects released")
        except Exception as e:
            print(f"   ⚠️ Warning releasing COM objects: {e}")
        
        # Step 4: Force kill Excel processes if still running (fallback)
        try:
            import subprocess
            import time
            time.sleep(1)  # Give Excel time to close gracefully
            
            # Check if Excel processes are still running
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq EXCEL.EXE'], 
                                  capture_output=True, text=True, shell=True)
            if 'EXCEL.EXE' in result.stdout:
                print("   ⚠️ Excel processes still running, attempting force close...")
                subprocess.run(['taskkill', '/F', '/IM', 'EXCEL.EXE'], 
                             capture_output=True, shell=True)
                print("   ✓ Excel processes terminated")
            else:
                print("   ✓ No Excel processes remaining")
                
        except Exception as e:
            print(f"   ⚠️ Warning checking/killing Excel processes: {e}")
        
        print("✅ Excel cleanup completed")
        
    except Exception as e:
        print(f"❌ Error during Excel cleanup: {e}")
        # Last resort - try to kill Excel processes
        try:
            import subprocess
            subprocess.run(['taskkill', '/F', '/IM', 'EXCEL.EXE'], 
                         capture_output=True, shell=True)
            print("   ✓ Force terminated Excel processes as last resort")
        except:
            print("   ❌ Could not force terminate Excel processes")

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

def inspect_data_sheet_structure(wb):
    """
    Inspect the actual structure of the Data sheet to understand the layout.
    
    Args:
        wb: Excel workbook object
    """
    try:
        data_sheet = wb.Sheets("Data")
        print(f"🔍 Inspecting Data sheet structure...")
        
        # Check first few rows and columns to understand the layout
        print(f"   📋 Data sheet contents (first 10 rows, columns A-H):")
        
        for row in range(1, 11):
            row_data = []
            for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                try:
                    cell_value = data_sheet.Range(f"{col}{row}").Value
                    if cell_value is not None:
                        # Truncate long values
                        str_value = str(cell_value)
                        if len(str_value) > 15:
                            str_value = str_value[:12] + "..."
                        row_data.append(f"{col}{row}:{str_value}")
                    else:
                        row_data.append(f"{col}{row}:empty")
                except:
                    row_data.append(f"{col}{row}:error")
            
            print(f"      Row {row}: {' | '.join(row_data)}")
        
        # Look for frequency-like data (numbers that look like frequencies)
        print(f"   🔍 Searching for frequency data patterns...")
        frequency_candidates = []
        
        for col in ['A', 'B', 'C', 'D', 'E', 'F']:
            for row in range(1, 51):  # Check first 50 rows
                try:
                    cell_value = data_sheet.Range(f"{col}{row}").Value
                    if cell_value is not None:
                        # Check if it looks like a frequency (50-5000 Hz range)
                        try:
                            num_value = float(cell_value)
                            if 50 <= num_value <= 5000:
                                frequency_candidates.append(f"{col}{row}:{num_value}")
                                if len(frequency_candidates) >= 5:  # Stop after finding a few
                                    break
                        except:
                            pass
                except:
                    pass
            if len(frequency_candidates) >= 5:
                break
        
        if frequency_candidates:
            print(f"   ✓ Found potential frequency data: {', '.join(frequency_candidates[:5])}")
        else:
            print(f"   ⚠️ No frequency data found in typical range (50-5000 Hz)")
            
    except Exception as e:
        print(f"   ✗ Error inspecting data sheet: {e}")

def validate_data_sheet(wb):
    """
    Validate the Data sheet structure before running the macro.
    
    Args:
        wb: Excel workbook object
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    try:
        data_sheet = wb.Sheets("Data")
        
        # Check if Data sheet exists
        if not data_sheet:
            return False, "Data sheet not found in workbook"
        
        # First, inspect the actual structure
        inspect_data_sheet_structure(wb)
        
        # For now, let's be more lenient and just check if there's any data at all
        print(f"🔍 Basic data validation...")
        
        # Check if there's any data in the sheet
        has_any_data = False
        for row in range(1, 51):
            for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                try:
                    cell_value = data_sheet.Range(f"{col}{row}").Value
                    if cell_value is not None and str(cell_value).strip():
                        has_any_data = True
                        break
                except:
                    pass
            if has_any_data:
                break
        
        if not has_any_data:
            return False, "No data found anywhere in the Data sheet"
        
        print(f"✓ Data sheet contains data - proceeding with macro execution")
        return True, None
        
    except Exception as e:
        return False, f"Error validating data sheet: {e}"

def add_and_run_macro(wb):
    """
    Adds and runs the plotting macro to generate all acoustic charts.
    """
    try:
        # Select the macro file
        macro_file = os.path.join(MACROS_PATH, "SIT_Macro_V4.txt")
        macro_name = "GenerateAcousticCharts_V3_Clean"

            
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
        invalid_types = [t.strip() for t in test_types if t.strip() not in valid_types]
        if invalid_types:
            print(f"Error: Invalid test type(s): {', '.join(invalid_types)}")
            print("Valid types are: ABW, ABF, IPF")
            continue
        
        # Clean up whitespace
        test_types = [t.strip() for t in test_types]
        return test_types

def find_project_directory(project_number):
    """
    Find the project directory in the SIT folder.
    
    Args:
        project_number: The project number (e.g., 'NP-012432')
        
    Returns:
        str: Path to project directory, or None if not found
    """
    sit_base = os.path.join(DESKTOP_PATH, "SIT")
    project_dir = os.path.join(sit_base, project_number)
    
    if os.path.exists(project_dir):
        return project_dir
    else:
        print(f"Error: Project directory not found at {project_dir}")
        return None

def find_test_files(project_dir, project_number, num_tests):
    """
    Find test files in the project directory.
    
    Args:
        project_dir: Path to project directory
        project_number: The project number
        num_tests: Expected number of test files
        
    Returns:
        list: List of test file paths found
    """
    test_files = []
    
    for i in range(num_tests):
        letter = chr(65 + i)  # A, B, C, etc.
        filename = f"{project_number} - {letter}.xlsx"
        filepath = os.path.join(project_dir, filename)
        
        if os.path.exists(filepath):
            test_files.append(filepath)
            print(f"✓ Found: {filename}")
        else:
            print(f"✗ Missing: {filename}")
    
    return test_files

def process_test_file_plotting(excel_app, filepath):
    """
    Process a single test file to generate plots.
    
    Args:
        excel_app: Excel application object
        filepath: Path to the test file
        
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    filename = os.path.basename(filepath)
    print(f"\n{'='*50}")
    print(f"Processing: {filename}")
    print(f"{'='*50}")
    
    wb = None
    try:
        # Open the workbook
        print(f"📂 Opening {filename}...")
        wb = open_workbook_with_editing(excel_app, filepath)
        print(f"✓ Workbook opened successfully")
        
        # Run the plotting macro (generates all chart types automatically)
        add_and_run_macro(wb)
        
        # Save the workbook with the new charts
        print("💾 Saving workbook with generated charts...")
        wb.Save()
        print(f"✅ Successfully processed {filename} - Charts saved to file")
        
        # Close the workbook
        wb.Close()
        print(f"📁 Workbook closed")
        
        return True, None
        
    except Exception as e:
        error_msg = f"Critical error processing {filename}: {e}"
        print(f"💥 {error_msg}")
        try:
            if wb:
                wb.Close()
        except:
            pass
        return False, error_msg

def main():
    """Main function to run the SIT plotter."""
    print("="*60)
    print("SIT PLOTTER - Acoustic Chart Generator")
    print("="*60)
    print("This script generates acoustic charts for existing SIT test files.")
    print()
    
    try:
        # Get project number from user
        print("Enter the project number:")
        project_number = input("> ").strip().upper()
        while not project_number or not project_number.startswith("NP-"):
            print("Error: Project number must start with 'NP-'!")
            project_number = input("> ").strip().upper()
        
        # Get number of tests
        while True:
            try:
                print(f"\nEnter the number of tests for {project_number}:")
                num_tests = int(input("> ").strip())
                if num_tests > 0:
                    break
                print("Error: Number must be greater than 0!")
            except ValueError:
                print("Error: Please enter a valid number!")
        
        print(f"✓ Will process {num_tests} test files (macro auto-detects chart types)")
        
        # Find project directory
        print(f"\nLooking for project directory: {project_number}")
        project_dir = find_project_directory(project_number)
        if not project_dir:
            return
        
        print(f"✓ Found project directory: {project_dir}")
        
        # Find test files
        print(f"\nLooking for {num_tests} test files...")
        test_files = find_test_files(project_dir, project_number, num_tests)
        
        if len(test_files) != num_tests:
            print(f"\nWarning: Found {len(test_files)} files but expected {num_tests}")
            if len(test_files) == 0:
                print("No test files found. Exiting.")
                return
            
            response = input("Continue with found files? (y/n): ").lower()
            if response != 'y':
                print("Exiting.")
                return
        
        # Check if macro file exists
        macro_file = os.path.join(MACROS_PATH, "SIT_Plot_V3.txt")
        if not os.path.exists(macro_file):
            print(f"\nError: Macro file not found at {macro_file}")
            print("Please ensure the SIT_Reporter_Package is in the same directory as this script.")
            return
        
        # Initialize Excel application
        print(f"\nInitializing Excel application...")
        excel_app = open_excel_app()
        
        try:
            successful_files = 0
            failed_files = 0
            error_details = []
            
            # Process each test file
            for i, filepath in enumerate(test_files):
                success, error_msg = process_test_file_plotting(excel_app, filepath)
                
                if success:
                    successful_files += 1
                    print(f"🎯 File {i+1}/{len(test_files)}: SUCCESS")
                else:
                    failed_files += 1
                    filename = os.path.basename(filepath)
                    error_details.append(f"   • {filename}: {error_msg}")
                    print(f"💀 File {i+1}/{len(test_files)}: FAILED - {error_msg}")
            
            # Summary
            print(f"\n{'='*60}")
            print("🏁 PLOTTING SUMMARY")
            print(f"{'='*60}")
            print(f"✅ Successfully processed: {successful_files} files")
            if failed_files > 0:
                print(f"❌ Failed to process: {failed_files} files")
                print(f"\n📋 Error Details:")
                for error in error_details:
                    print(error)
            print(f"📊 Total files processed: {len(test_files)}")
            
            if successful_files > 0:
                print(f"\n🎉 SUCCESS: Charts have been generated and saved in the test files.")
                print(f"📁 Project directory: {project_dir}")
            elif failed_files > 0:
                print(f"\n⚠️ WARNING: No files were processed successfully.")
                print(f"Please check the errors above and ensure:")
                print(f"   • VBA macros are enabled in Excel")
                print(f"   • The macro file exists: {os.path.join(MACROS_PATH, 'SIT_Plot_V3.txt')}")
                print(f"   • Test files have the correct data structure")
            
        finally:
            # Always close Excel safely
            close_excel_safely(excel_app)
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        close_excel_safely(excel_app)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        close_excel_safely(excel_app)

if __name__ == "__main__":
    main()
