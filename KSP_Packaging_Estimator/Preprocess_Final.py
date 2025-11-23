import pandas as pd
import re

def excel_to_loc(equation, df):
    """
    Converts Excel-style equations to use pandas .loc references, 
    and replaces Excel functions with Python equivalents.
    """
    # Remove the leading '=' if present
    equation = equation.lstrip('=')
    
    # Match patterns like 'B2', 'C3', etc.
    pattern = r'([A-Z]+)(\d+)'
    
    # Convert Excel-style cell references to DataFrame .loc references
    def replace_match(match):
        col_letter = match.group(1) 
        row_number = int(match.group(2)) - 2  # Apply offset to row number
    
        # Convert column letter to the corresponding column name, applying offset
        col_index = sum((ord(char) - 65 + 1) * (26 ** idx) for idx, char in enumerate(reversed(col_letter))) - 2
        if col_index < len(df.columns):
            col_name = df.columns[col_index]
        else:
            return match.group(0)  # Leave the original if no valid match found
    
        # Convert row number to corresponding index label
        if row_number < len(df.index):
            row_name = df.index[row_number]
        else:
            return match.group(0)  # Leave the original if no valid match found
    
        return f'df.loc["{row_name}", "{col_name}"]'
    
    # Substitute Excel-style cell references with df.loc references
    equation = re.sub(pattern, replace_match, equation)
    
    # Replace Excel-style functions with pandas equivalents
    # Adjust to place .ceil() and .floor() correctly at the end
    equation = re.sub(r"ROUNDUP\((.+?),", r"(\1).ceil(", equation)
    equation = re.sub(r"ROUNDDOWN\((.+?),", r"(\1).floor(", equation)
    equation = re.sub(r"ROUND\((.+?),", r"round(\1,", equation)
    
    # Handle specific replacement for SUM that needs adjustment
    specific_sum_pattern = r'SUM\(df\.loc\["TOTAL \(£\)", "MECHANISM \(number\)"\]:df\.loc\["TOTAL \(£\)", "PACKING MATERIALS PER PALLETE \(number\)"\]\)'
    equation = re.sub(specific_sum_pattern, 'df.loc["TOTAL (£)", "MECHANISM (number)":"TOTAL (£)"].sum()', equation)
    
    # Replace SUM(A1:B10) with df.loc-based sum considering the offsets
    # Match patterns like "SUM(A1:B10)" and convert to a .loc-based sum for the DataFrame
    sum_pattern = r'SUM\(([A-Z]+\d+):([A-Z]+\d+)\)'
    
    def replace_sum(match):
        start_ref = match.group(1)
        end_ref = match.group(2)

        # Extract row and column names using replace_match method
        start_converted = replace_match(re.match(pattern, start_ref))
        end_converted = replace_match(re.match(pattern, end_ref))

        # Extract the row or column names from the transformed match
        start_col = start_converted.split('"')[3]
        end_col = end_converted.split('"')[3]
        start_row = start_converted.split('"')[1]
        end_row = end_converted.split('"')[1]

        # Correct the syntax to ensure proper sum functionality
        if start_row == end_row:
            # Summing across a row range, fix the column range for pandas
            return f'df.loc["{start_row}", "{start_col}":"{end_col}"].sum()'
        else:
            # Summing across a column range, fix the row range for pandas
            return f'df.loc["{start_row}":"{end_row}", "{start_col}"].sum()'
    
    # Adjust sum pattern using the replace_sum function
    equation = re.sub(sum_pattern, replace_sum, equation)

    return equation

def adjust_loc_for_transpose(equation):
    """
    Adjusts .loc references in the equation to account for DataFrame transposition, including handling .sum() patterns.
    """
    # Match patterns like 'df.loc["row_name", "col_name"]'
    loc_pattern = r'df\.loc\["([^"]+)",\s*"([^"]+)"\]'
    
    # Match patterns like 'df.loc["row_name":"row_name_end", "col_name"].sum()' for sum adjustment
    sum_pattern = r'df\.loc\["([^"]+)"\s*:\s*"([^"]+)",\s*"([^"]+)"\]\.sum\(\)'
    
    # Swap row and column names in .loc references
    def swap_loc_match(match):
        row_name = match.group(1)
        col_name = match.group(2)
        return f'df.loc["{col_name}", "{row_name}"]'
    
    # Swap row names in .sum() references
    def swap_sum_match(match):
        row_name_start = match.group(1)
        row_name_end = match.group(2)
        col_name = match.group(3)
        return f'df.loc["{col_name}", "{row_name_start}":"{row_name_end}"].sum()'
    
    # Apply swapping for general .loc references
    equation = re.sub(loc_pattern, swap_loc_match, equation)
    
    # Apply swapping for .sum() references
    equation = re.sub(sum_pattern, swap_sum_match, equation)
    
    return equation

# Load Excel data and set paths 
file_path = '/Users/q/Documents/Work/KSP/FactoryConstants GPT.xlsx'
output_file_path = '/Users/q/PythonScript/Python/DataAnalysis/KSP/Variables_GPT.csv'
df = pd.read_excel(file_path)

# Set the first column as index
df.set_index(df.columns[0], inplace=True)

# Set Index and column names
df.columns.name = 'Variable Name'
df.index.name = 'Feature'

# Apply the conversion function to relevant rows by iterating over the DataFrame's index
for row_label in ['Equation for Multiplier', 'Equation for TOTAL (£)']:
    if row_label in df.index:
        # Access the values of the row as a Series and apply the conversion function
        df.loc[row_label] = df.loc[row_label].apply(
            lambda x: excel_to_loc(x, df) if pd.notna(x) else x
        )
        
# Swap row and column refrences for transposing df
for column in ['Equation for Multiplier', 'Equation for TOTAL (£)']:
    if column in df.columns:
        df[column] = df[column].apply(
            lambda x: adjust_loc_for_transpose(x) if pd.notna(x) and x.lower() != 'nan' else x
        )
# Transpose df        
df = df.transpose()

# Loop over the DataFrame rows to update missing values in 'Equation for Multiplier'
for index, row in df.iterrows():
    # Use the index (which corresponds to 'Variable Name') for updating equations
    variable_name = index  # Since 'Variable Name' is the index

    # If 'Equation for Multiplier' is NaN or the string 'nan', fill it with a reference using .loc
    if pd.isna(row['Equation for Multiplier']) or row['Equation for Multiplier'] == 'nan':
        df.at[variable_name, 'Equation for Multiplier'] = f'df.loc["{variable_name}", "Multiplier"]'
        
    # If 'Equation for TOTAL (£)' is NaN or the string 'nan', fill it with a reference using .loc
    if pd.isna(row['Equation for TOTAL (£)']) or row['Equation for TOTAL (£)'] == 'nan':
        df.at[variable_name, 'Equation for TOTAL (£)'] = f'df.loc["{variable_name}", "TOTAL (£)"]'


df.to_csv(output_file_path)

# Convert 'Multiplier', 'COST/RATE (£)', and 'TOTAL (£)' columns to floats
df['Multiplier'] = pd.to_numeric(df['Multiplier'], errors='coerce').fillna(0.0)
df['COST/RATE (£)'] = pd.to_numeric(df['COST/RATE (£)'], errors='coerce').fillna(0.0)
df['TOTAL (£)'] = pd.to_numeric(df['TOTAL (£)'], errors='coerce').fillna(0.0)

# Ensure the equation columns are treated as strings
df['Equation for Multiplier'] = df['Equation for Multiplier'].apply(str)
df['Equation for TOTAL (£)'] = df['Equation for TOTAL (£)'].apply(str)

df = df.iloc[:,:9]
# Save DataFrame as CSV file
df.to_csv(output_file_path)

#%%

print(df.head())

# %%

