import sqlite3
import pandas as pd

# Load CSV file
df = pd.read_csv('/Users/q/Desktop/Variables_EQ_GPT.csv')
df.set_index(df.columns[0], inplace=True)  
df.index.name = 'feature'  
df.reset_index(inplace=True)  # This will only add 'feature' as a column if not already present

# Print columns and count for verification
print("Columns before renaming:", df.columns)
print("Number of columns before renaming:", len(df.columns))

# Define the expected columns without "feature" if it’s already included
expected_columns = [
    "variable_name", "multiplier", "equation_for_multiplier",
    "updated_multiplier", "factory_set_constant", "customer_dependant_variable",
    "customer_variable", "cost_rate", "total", "equation_for_total"
]

# Check if the column length matches the expected columns
if len(df.columns) == len(expected_columns):
    df.columns = expected_columns
elif len(df.columns) == len(expected_columns) + 1:  # If 'feature' is included
    df.columns = ["feature"] + expected_columns
else:
    raise ValueError(f"Unexpected number of columns. Expected {len(expected_columns) + 1} but got {len(df.columns)}.")

# Connect to SQLite and insert data into the 'variables' table
conn = sqlite3.connect('estimator.db')
df.to_sql('variables', conn, if_exists='replace', index=False)

print("Data successfully inserted into the 'variables' table!")

# Close the connection
conn.close()