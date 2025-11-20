# SvanPC-Pal

Professional automation utility for batch processing Svantek SvanPC++ noise measurement data.

## Overview

SvanPC-Pal streamlines the workflow for acoustic consultants working with Svantek noise measurement equipment. The tool automates the tedious process of opening measurement files, configuring display profiles, adjusting logger step intervals, and exporting data to Excel for analysis.

Originally developed to eliminate hours of manual data processing for building acoustics and occupational noise assessments, reducing multi-hour export tasks to minutes of automated processing.

## Key Features

### 🔄 Batch Automation
- **Unattended processing** of entire folders of .SVL measurement files
- **Multi-file handling** with automatic file discovery and iteration
- **Error resilience** with detailed logging of missing configurations

### 📊 Flexible Configuration
- **Four job type profiles**:
  - Noise at Work (NAW) - Occupational noise compliance
  - Breakin Octaves (Bo) - Building acoustics octave band analysis  
  - Breakin 1/3 Octaves (B1o) - Building acoustics narrow-band analysis
  - Spot 1/3 Octaves (Sp1o) - Short-duration spot measurements

- **Multiple logger step intervals**:
  - 10 seconds, 1 minute, 2 minutes, 15 minutes, 1 hour
  - Automatic selection per measurement profile

### 📈 Data Export
- **Excel workbook generation** with systematic naming:
  - Format: `{FileNumber}{JobType}{LoggerStep}.xlsx`
  - Example: `001Noise at Work(1m).xlsx`
- **Custom folder organization** with `/exported` subfolder creation
- **Overwrite handling** for iterative workflows

### 🖥️ UI Automation
- **Dual-backend approach** (win32 + UIA) for robust window control
- **Dynamic element detection** with scroll-until-found helpers
- **Error recovery** for unavailable UI elements
- **Excel instance management** with F12 save-as automation

## Technical Stack

**Languages:** Python 3.x  
**Key Libraries:**
- `pywinauto` - Windows application UI automation
- `pywinauto.mouse` - Coordinate-based clicking for table selection

**External Dependencies:**
- SvanPC++ (Svantek noise measurement software)
- Microsoft Excel (for data export)

**Platform:** Windows only (COM automation requirements)

## Installation

```bash
pip install -r requirements.txt
```

**Prerequisites:**
- Windows OS (7 or later)
- SvanPC++ installed at default path: `C:\Program Files (x86)\Svantek\SvanPC++\SvanPCplus95x.exe`
- Microsoft Excel installed

## Usage

### Basic Workflow

1. **Prepare your data:**
   - Place all .SVL measurement files in a single folder
   - Ensure files are named systematically (e.g., 001.SVL, 002.SVL)

2. **Run the script:**
   ```bash
   python SvanPC_Pal.py
   ```

3. **Follow prompts:**
   ```
   Enter the folder path containing your .SVL files:
   SOURCE_FOLDER: C:\Measurements\Project_XYZ
   
   Export folder is: C:\Measurements\Project_XYZ\exported
   
   1. Noise at Work
   2. Breakin (octaves)
   3. Breakin (one-octaves)
   4. Spot (one-octaves)
   Enter Job Type (1,2,3 or 4): 1
   ```

4. **Watch automation:**
   - SvanPC++ launches automatically
   - Each file is opened, configured, and exported
   - Progress printed to console
   - Excel workbooks saved to `/exported` subfolder

5. **Review completion report:**
   ```
   All files processed!
   Program completed in 127.45 seconds.
   
   All files exported with required logger step/config profiles.
   ```

### Configuration Profiles

**NAW Profile:**
- Single configuration, default logger step
- Optimized for occupational noise assessments

**Breakin Octave Profiles (Bo & B1o):**
- Five logger step variations per file:
  - Default, 1 minute, 2 minutes, 15 minutes, 1 hour
- Comprehensive time-series analysis
- Generates 5 Excel files per .SVL input

**Spot Profile (Sp1o):**
- Single 10-second logger step
- Quick spot measurement exports

## Project Context

Built for acoustic consulting workflows requiring:
- Rapid turnaround on building acoustics compliance testing
- Systematic data organization for regulatory reporting
- Elimination of repetitive manual export tasks
- Batch processing of field measurement data

**Typical Use Case:**  
Process 20 building acoustics test files × 5 logger steps = 100 Excel exports in ~5 minutes vs. 2+ hours manually.

## Architecture Highlights

### Dual-Backend Strategy
Uses both `win32` and `UIA` backends for maximum reliability:
- **win32**: Menu selection, file dialogs
- **UIA**: Modern UI element interaction, configurator panels

### Dynamic UI Handling
Implements scroll-until-found pattern for UI elements that may not be initially visible:
```python
def scroll_until_found(item_title, parent_pane, max_scrolls=30):
    # Scrolls through UI tree to locate configuration items
```

### Error Logging
Tracks logger step availability issues and reports at completion:
```python
logger_errors = []  # Populated during processing
# Final report includes any missing configurations
```

## Performance

- **Processing time**: ~6 seconds per file per logger step
- **Memory usage**: Minimal (delegates to SvanPC++ and Excel)
- **Reliability**: Error recovery for UI timing issues

## License

MIT License

---

**Author:** Q-types  
**Domain:** Acoustic Testing Automation  
**Application:** Building Acoustics & Occupational Noise Assessment
