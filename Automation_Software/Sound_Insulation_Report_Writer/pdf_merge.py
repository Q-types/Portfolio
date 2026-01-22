"""
PDF Merge Utility for Sound Insulation Test Reports

Merges multiple PDF documents into a single professional report with automated
page numbering and proper sequencing.

Features:
    - Multi-PDF merging with custom ordering
    - Automatic page numbering (excluding cover pages)
    - Custom font rendering with Arial
    - Retry logic for file access issues
    - Professional formatting with light gray page numbers

Page Order:
    1. Front Page (cover)
    2. Doc1 (Onsite Worksheet)
    3. Test PDFs (A, B, C, etc.)
    4. Back Page

Author: Q-types
License: MIT
"""

import os
import time
import sys
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from io import BytesIO

# Register Arial font for reportlab
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
except:
    # Fallback if arial.ttf is not found
    pass

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
            letter = chr(65 + i)  # A, B, C, etc.
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

def main():
    source_dir = input("Input source folder ",)
    project_number = input("Input project number ",)
    num_tests = int(input("Input number of tests ",))
    merge_pdfs(source_dir, project_number, num_tests)

if __name__ == "__main__":
    main()