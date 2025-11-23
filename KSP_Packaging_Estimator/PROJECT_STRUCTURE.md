# Project Structure Documentation

## Directory Layout

```
KSP_Packaging_Estimator/
├── README.md                      # Main project documentation
├── PORTFOLIO_NOTES.md             # Portfolio-specific context
├── PROJECT_STRUCTURE.md           # This file - architecture guide
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git exclusions
│
├── gui2.py                        # Main GUI application (346 lines)
├── KSP_Functions.py               # Core calculation engine (482 lines)
├── Preprocess_Final.py            # Excel-to-CSV converter (174 lines)
├── Logic_to_Loc.py                # Equation migration tool (194 lines)
├── csv_to_sql.py                  # CSV database loader (45 lines)
├── feadback.py                    # Feedback collection utility (45 lines)
├── run_ksp_estimator.sh           # Launch script
│
├── Variables_EQ_GPT.csv           # Pricing model data (80+ variables)
├── Variables_GPT.csv              # Base variables (pre-equation)
├── database.sql                   # Database schema definition
│
├── invoices/                      # Generated PDF outputs
│   └── .gitkeep
└── feedback/                      # Feedback templates
    └── feedback_template.xlsx
```

---

## Module Descriptions

### 1. `gui2.py` - GUI Application Layer

**Purpose:** User interface for estimate generation and retrieval

**Key Components:**
```python
launch_gui()                    # Main application entry point
├── load_initial_data()         # Startup data loading
├── load_recent_estimate()      # Load last quote
├── generate()                  # Generate estimate button handler
├── retrieve()                  # Retrieve estimate button handler
├── create_scrollable_frame()   # UI helper for scrolling
├── add_variables_to_generate_tab()   # Populate input fields
└── add_variables_to_retrieve_tab()   # Display historical data
```

**UI Structure:**
- Tabbed interface (Generate / Retrieve)
- Scrollable frames for 80+ variables
- Input validation and error messages
- Color-coded status feedback

**Integration Points:**
- Calls `KSP_Functions` for all business logic
- Updates GUI based on calculation results
- Handles user input validation

---

### 2. `KSP_Functions.py` - Business Logic Layer

**Purpose:** Core calculation engine and data operations

**Function Categories:**

#### Calculation Functions
```python
estimate_total(df)              # Extract final cost
update_totals(df)               # Calculate line item costs
update_multiplier(df)           # Recalculate dependent variables
update_enquiry(df, updates)     # Apply customer changes
update_dataframe(df, updates)   # Master calculation orchestrator
```

#### Data Loading
```python
load_data()                     # Load pricing model from CSV
```

#### Database Operations
```python
save_entire_database_with_metadata()    # Store complete estimate
save_estimate_metadata()                # Store summary data
retrieve_estimate_data()                # Load full estimate
retrieve_estimate_meta()                # Load summary only
get_next_estimate_number()              # Generate ID
get_most_recent_estimate_number()       # Find latest
confirm_sale()                          # Convert estimate to sale
```

#### Output Generation
```python
create_invoice()                # Generate PDF invoice
generate_estimate()             # Complete workflow
```

**Data Flow:**
```
1. load_data() → DataFrame with 80+ variables
2. update_enquiry() → Apply customer inputs
3. update_multiplier() → Recalculate dependencies
4. update_totals() → Calculate costs
5. estimate_total() → Extract final price
6. create_invoice() → Generate PDF
7. save_*() → Persist to database
```

---

### 3. `Preprocess_Final.py` - Data Pipeline

**Purpose:** Convert Excel pricing model to Python-compatible format

**Process:**
```
Excel Spreadsheet (FactoryConstants GPT.xlsx)
    ↓
excel_to_loc()         # Convert cell refs (A1 → df.loc["row","col"])
    ↓
adjust_loc_for_transpose()  # Handle DataFrame orientation
    ↓
Variables_GPT.csv      # Intermediate output
    ↓
(Manual validation)
    ↓
Variables_EQ_GPT.csv   # Final pricing model
```

**Key Functions:**
```python
excel_to_loc(equation, df)           # Main conversion function
├── Handles: B2, C3 → df.loc references
├── Converts: SUM(A1:B10) → .sum()
├── Converts: ROUNDUP() → np.ceil()
└── Converts: ROUNDDOWN() → np.floor()

adjust_loc_for_transpose(equation)   # Swap row/col for transposed DF
```

**Regex Patterns:**
- `([A-Z]+)(\d+)` - Cell references
- `SUM\(([A-Z]+\d+):([A-Z]+\d+)\)` - Range sums
- `ROUNDUP\((.+?),` - Excel functions

---

### 4. `Logic_to_Loc.py` - Equation Migration

**Purpose:** Alternative approach to equation conversion

**Contains:**
- `new_equations[]` - 84 total cost equations
- `new_mult_equations[]` - 84 multiplier equations

**Example Transformations:**
```python
# Before (Excel)
=B2*C2

# After (Python)
df.loc["MECHANISM (number)", "Multiplier"] * df.loc["MECHANISM (number)", "COST/RATE (£)"]
```

**Usage:**
- Used for initial migration
- Provides backup/reference for formula logic
- Can regenerate Variables_EQ_GPT.csv if needed

---

### 5. Supporting Files

#### `csv_to_sql.py`
Utility to load Variables CSV into SQL database (alternative to CSV approach)

#### `feadback.py`
Collects user feedback on estimate accuracy for continuous improvement

#### `run_ksp_estimator.sh`
Bash launcher script:
```bash
#!/bin/bash
source ~/opt/anaconda3/bin/python
python3 gui2.py
```

#### `database.sql`
SQLite schema definitions:
- `variables` table (pricing model)
- `detailed_estimates` table (full estimate data)
- `estimate_metadata` table (quick lookups)
- `Sales` table (confirmed orders)
- `Sales_Metadata` table (sale tracking)

---

## Data Model

### Variables CSV Structure

| Column | Type | Purpose |
|--------|------|---------|
| Feature | String (Index) | Variable name/identifier |
| Multiplier | Float | Current value |
| Equation for Multiplier | String | Python code to calculate |
| Updated Multiplier | Boolean | Customer override flag |
| Factory Set Constant | Boolean | Fixed by factory |
| Customer Dependant Variable | Boolean | Calculated from customer input |
| Customer Variable | Boolean | Direct customer input |
| COST/RATE (£) | Float | Base cost or hourly rate |
| TOTAL (£) | Float | Calculated total cost |
| Equation for TOTAL (£) | String | Python code to calculate |

### Database Schema

#### `estimate_metadata` Table
```sql
CREATE TABLE estimate_metadata (
    estimate_number INTEGER PRIMARY KEY,
    company_name TEXT,
    job_description TEXT,
    date TEXT,
    time TEXT,
    final_estimate REAL
);
```

#### `detailed_estimates` Table
```sql
CREATE TABLE detailed_estimates (
    estimate_number INTEGER PRIMARY KEY,
    company_name TEXT,
    job_description TEXT,
    estimate_data TEXT  -- CSV string of full DataFrame
);
```

---

## Calculation Flow

### Step-by-Step Process

```
┌─────────────────────────────────────────┐
│  1. USER INTERACTION                    │
│  - Enter company name, job description  │
│  - Modify customer variables            │
│  - Click "Generate Estimate"            │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  2. LOAD BASE DATA                      │
│  KSP_Functions.load_data()              │
│  - Read Variables_EQ_GPT.csv            │
│  - Create DataFrame (80+ rows)          │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  3. APPLY CUSTOMER INPUTS               │
│  update_enquiry(inquiry_updates, df)    │
│  - Update customer variables            │
│  - Set Updated Multiplier = 1           │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  4. RECALCULATE MULTIPLIERS             │
│  update_multiplier(df)                  │
│  - For each variable:                   │
│    - If Updated Multiplier == 0:        │
│      - Execute Equation for Multiplier  │
│  - Dependencies resolved automatically  │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  5. CALCULATE TOTALS                    │
│  update_totals(df)                      │
│  - Iterate REVERSE (bottom to top)      │
│  - For each line item:                  │
│    - Execute Equation for TOTAL (£)     │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  6. EXTRACT FINAL ESTIMATE              │
│  estimate_total(df)                     │
│  - Get total from key row               │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  7. GENERATE OUTPUTS                    │
│  - create_invoice() → PDF               │
│  - save_estimate_metadata() → DB        │
│  - save_entire_database_with_metadata() │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│  8. USER FEEDBACK                       │
│  - Display success message              │
│  - Show estimate number                 │
│  - Invoice path notification            │
└─────────────────────────────────────────┘
```

---

## Key Algorithms

### 1. Dependency Resolution

**Problem:** Variables depend on each other in complex ways

**Solution:** Two-pass calculation
```python
# Pass 1: Update multipliers (forward iteration)
for index, row in df.iterrows():
    if not manually_updated:
        df.at[index, "Multiplier"] = eval(equation)

# Pass 2: Update totals (reverse iteration)
for index, row in df.iloc[::-1].iterrows():
    df.at[index, "TOTAL (£)"] = eval(equation)
```

**Why reverse for totals?**
- Some totals are sums of other totals
- Bottom rows often aggregate top rows
- Ensures dependencies are resolved

### 2. Formula Parsing

**Excel Formula:**
```
=SUM(B2:B10)*ROUNDUP(C5,0)
```

**Conversion Steps:**
1. Remove leading `=`
2. Convert `B2:B10` → `df.loc["row2":"row10", "col"]`
3. Convert `SUM()` → `.sum()`
4. Convert `ROUNDUP(C5,0)` → `np.ceil(df.loc["row5","col"])`

**Result:**
```python
df.loc["row2":"row10", "col"].sum() * np.ceil(df.loc["row5", "col"])
```

### 3. Dynamic Equation Execution

```python
# Store equations as strings in DataFrame
equation = 'df.loc["QUANTITY", "Multiplier"] * 1.05'

# Execute with eval() in controlled scope
result = eval(equation)

# Update DataFrame
df.at[index, "Multiplier"] = result
```

**Safety considerations:**
- DataFrame (`df`) is only object in scope
- No user input directly executed
- Equations pre-validated during preprocessing

---

## Extension Points

### Adding New Variables

1. Update Excel source file
2. Run `Preprocess_Final.py`
3. Validate output CSV
4. Restart application (auto-loads new variables)

### Adding New Features

**New calculation type:**
- Add function to `KSP_Functions.py`
- Call from `update_dataframe()` workflow
- Test with sample data

**New UI component:**
- Add to `gui2.py`
- Follow existing pattern (labels, entries, buttons)
- Connect to backend functions

**New database table:**
- Add schema to `database.sql`
- Create CRUD functions in `KSP_Functions.py`
- Update `save_*/retrieve_*` functions

---

## Testing Strategy

### Validation Approach

1. **Historical Comparison**
   - Run 50+ old estimates through new system
   - Compare outputs to Excel results
   - Acceptable variance: <£0.01

2. **Boundary Testing**
   - Test with minimum quantities
   - Test with maximum quantities
   - Test with zero values

3. **Edge Cases**
   - Division by zero handling
   - Missing customer inputs
   - Invalid data types

4. **Integration Testing**
   - Generate estimate → Check PDF
   - Save to database → Retrieve
   - Customer override → Verify persistence

### Test Data

Located in example inquiry:
```python
inquiry_updates = { 
    "QUANTITY REQUIRED BY CUSTOMER (number)": 15000,
    "MECHANISM (number)": 0.17,
    "MITRE CORNERS OF OUTER SHEET 40mm (hours)": 0.033333333,
    "FLAT SIZE Length (mm)": 565,
    "FLAT SIZE Width (mm)": 165
}
```

---

## Performance Considerations

### Current Performance
- **Estimate generation:** <1 second
- **Database save:** <0.5 seconds
- **PDF generation:** <2 seconds
- **Total workflow:** <5 seconds

### Bottlenecks
- PDF generation (ReportLab)
- DataFrame eval() operations (80+ evals)
- Database writes (serializing DataFrame)

### Optimization Opportunities
- Cache frequently accessed data
- Compile equations instead of eval()
- Batch database operations
- Use numpy vectorization where possible

---

## Security Considerations

### Current State
- ✅ No external network access
- ✅ Local SQLite database
- ✅ File system access controlled
- ⚠️ Uses `eval()` for equations

### Recommendations for Production Enhancement
- Replace `eval()` with AST-based parser
- Add user authentication
- Implement audit logging
- Encrypt sensitive data
- Add role-based permissions

---

## Deployment Notes

### Requirements
- Python 3.8+
- MacOS/Linux/Windows
- 50MB disk space (excluding database)
- No internet connection required

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python3 gui2.py
```

### First Run
- Prompts to load from recent quote or backup
- Creates `estimates.sql` if not exists
- Creates `invoices/` directory if not exists

---

## Maintenance

### Regular Tasks
- Backup `estimates.sql` weekly
- Review invoice output quality
- Update material costs in Variables CSV
- Monitor disk space (database growth)

### Updates
- Material costs: Update Variables CSV
- Machine rates: Update Variables CSV
- New calculations: Modify equations in CSV
- UI changes: Edit `gui2.py`

---

## Troubleshooting

### Common Issues

**Issue:** "Cannot load Variables_EQ_GPT.csv"
- **Solution:** Ensure CSV is in same directory as scripts

**Issue:** Database locked
- **Solution:** Close other instances of application

**Issue:** PDF generation fails
- **Solution:** Check `invoices/` directory permissions

**Issue:** Incorrect calculations
- **Solution:** Verify Variables CSV equations

---

## Future Architecture Considerations

### Web Application Version
```
Current: Desktop (Tkinter)
Future: Web (Flask/Django + React)
Benefits: Multi-user, remote access, cloud database
```

### Microservices Version
```
API Gateway
├── Calculation Service (FastAPI)
├── Database Service (PostgreSQL)
├── PDF Service (Celery + ReportLab)
└── Auth Service (JWT)
```

### ML Enhancement
```
Current: Rule-based pricing
Future: ML-predicted pricing + rule validation
Model: Historical estimates → Price prediction
```

---

*Document Version: 1.0*  
*Last Updated: 2024*  
*Maintained by: [Your Name]*
