# Sound Insulation Test Report Writer

Professional automation suite for generating Sound Insulation Test (SIT) reports for acoustic testing compliance.

## Overview

This project automates the end-to-end process of creating professional sound insulation test reports, from data processing to final PDF generation. Originally developed for NOVA Acoustics Ltd to streamline acoustic testing workflows and ensure consistent, compliant documentation.

## Project Files

- **SIT_Report_Writer_V9.py** - Main report writer application (Latest version)
- **SIT_Plotter.py** - Standalone acoustic chart plotting utility
- **pdf_merge.py** - PDF merging and page numbering utility

## Key Features

### 📊 Data Processing
- **Excel automation** via win32com for test data extraction
- **CRM integration** with Insightly API for project metadata
- **Multi-test support** for Airborne (ABF/ABW) and Impact (IPF) sound tests

### 📈 Chart Generation
- **Automated acoustic charts** using VBA macros
- **Frequency response visualization** for sound insulation performance
- **Compliance markers** for building regulations

### 📄 PDF Report Assembly
- **Multi-page report merging** with proper sequencing
- **Automatic page numbering** (excluding cover pages)
- **Professional formatting** with custom fonts and styling
- **Superscript deviation markers** for test results

### 🔧 Workflow Automation
- **Template-based generation** for consistency
- **Error handling and retry logic** for robust operation
- **Desktop output organization** for easy access

## Technical Stack

**Languages:** Python 3.x  
**Key Libraries:**
- `win32com.client` - Excel/Word automation
- `PyPDF2` - PDF manipulation
- `reportlab` - PDF generation
- `python-docx` - Word document processing
- `requests` - API integration

## Installation

```bash
pip install -r requirements.txt
```

**Note:** Requires Windows OS for Microsoft Office automation (win32com)

## Configuration

Set your Insightly API key as an environment variable:
```bash
set INSIGHTLY_API_KEY=your_api_key_here
```

## Usage

### Generate Complete Report
```python
python SIT_Report_Writer_V9.py
```

### Generate Charts Only
```python
python SIT_Plotter.py
```

### Merge Existing PDFs
```python
python pdf_merge.py
```

## Project Context

Built for acoustic testing workflows requiring:
- Fast turnaround on compliance documentation
- Consistent formatting across hundreds of reports
- Integration with existing CRM and file systems
- Batch processing capabilities

## License

MIT License

---

**Author:** Q-types  
**Domain:** Acoustic Testing Automation
