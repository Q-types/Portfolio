"""KSP Packaging Estimator - GUI Application

Provides a user-friendly Tkinter-based interface for generating and retrieving
packaging cost estimates. The application features two main tabs:

1. Generate Estimate Tab:
   - Input customer details (company name, job description)
   - Adjust pricing variables (customer, factory, and dependent variables)
   - Generate estimates with PDF invoice creation
   - Automatic database persistence

2. Retrieve Estimate Tab:
   - Load historical estimates by number
   - View most recent estimate
   - Display all variables and final costs
   - Review customer and job details

Author: [Your Name]
Company: KSP & Buckingham Screen Print
Date: 2024
"""

from KSP_Functions import load_data, generate_estimate, get_next_estimate_number, retrieve_estimate_data, retrieve_estimate_meta, get_most_recent_estimate_number
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import pandas as pd
import docx
import re


def launch_gui():
    """Launch the main GUI application window.
    
    Initializes the Tkinter interface with tabbed navigation, scrollable frames,
    and all necessary UI components for estimate generation and retrieval.
    Loads initial data from either the most recent quote or backup CSV.
    """
    
    def load_recent_estimate():
        """Retrieve and load the most recent estimate data and metadata."""
        try:
            # Get the most recent estimate number
            most_recent_estimate = get_most_recent_estimate_number()
            if not most_recent_estimate:
                result_label_retrieve.config(text="No estimates found in the database.", fg="red")
                return

            # Retrieve metadata and variable data
            metadata = retrieve_estimate_meta(most_recent_estimate)
            variable_data = retrieve_estimate_data(most_recent_estimate)

            # Update metadata labels
            company_name_label.config(text=f"Company Name: {metadata['company_name']}")
            job_description_label.config(text=f"Job Description: {metadata['job_description']}")
            date_label.config(text=f"Date: {metadata['date']}")
            time_label.config(text=f"Time: {metadata['time']}")
            final_estimate_label.config(text=f"Final Estimate: £{metadata['final_estimate']:.2f}")

            # Display variable data in the retrieve tab
            row = 8
            row = add_variables_to_retrieve_tab(retrieve_content, customer_variables, "Customer Variables", row, variable_data)
            row = add_variables_to_retrieve_tab(retrieve_content, customer_dependant_variables, "Customer Dependant Variables", row, variable_data)
            add_variables_to_retrieve_tab(retrieve_content, factory_set_constants, "Factory Set Constants", row, variable_data)

            result_label_retrieve.config(
                text=f"Most recent estimate #{most_recent_estimate} retrieved successfully.", fg="green"
            )
        except Exception as e:
            result_label_retrieve.config(text=f"Error: {e}", fg="red")
            
            
    def load_initial_data():
        """Prompt the user to load data from backup or most recent quote."""
        # Ask user if they want to load the last quote or backup
        choice = messagebox.askyesno(
            "Load Data",
            "Do you want to load the most recent quote?\n\nSelect 'No' to load backup data."
        )
        if choice:
            # Load the most recent quote
            most_recent_estimate = get_most_recent_estimate_number()
            if most_recent_estimate:
                try:
                    df = retrieve_estimate_data(most_recent_estimate)
                    print(f"Loaded data from the most recent quote #{most_recent_estimate}")
                    return df
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load recent quote: {e}")
            else:
                messagebox.showwarning("No Quotes Found", "No previous quotes found. Loading backup data.")
        # Default to loading backup data
        return load_data()
    
    df = load_initial_data()
    


    '''def auto_update_constants(materials_file, machine_file, df):
        """
        Updates the Factory Set Constants for material costs and machine times.

        Args:
            materials_file (str): Path to the Word/PDF file containing material costs.
            machine_file (str): Path to the Excel file containing machine constants.
            df (pd.DataFrame): The existing DataFrame.

        Returns:
            pd.DataFrame: Updated DataFrame with new constants.
        """

        # ---- Step 1: Update Material Costs (from Word) ----
        def extract_material_costs_from_docx(filepath):
            doc = docx.Document(filepath)
            material_costs = {}
            for paragraph in doc.paragraphs:
                match = re.match(r"^(.*?):\s*£?([\d.]+)$", paragraph.text.strip())
                if match:
                    material, cost = match.groups()
                    material_costs[material] = float(cost)
            return material_costs

        # ---- Step 2: Update Machining Constants (from Excel) ----
        def extract_machine_constants_from_excel(filepath):
            machine_constants = pd.read_excel(filepath, sheet_name="Sheet1", index_col=0)
            return machine_constants["Multiplier"].to_dict()

        # Extract updated values
        material_costs = extract_material_costs_from_docx(materials_file)
        machine_constants = extract_machine_constants_from_excel(machine_file)

        # Update the Factory Set Constants in the DataFrame
        updated_df = df.copy()
        for feature, new_value in material_costs.items():
            if feature in updated_df.index:
                updated_df.at[feature, "Multiplier"] = new_value

        for feature, new_value in machine_constants.items():
            if feature in updated_df.index:
                updated_df.at[feature, "Multiplier"] = new_value

        print("Factory Set Constants updated successfully.")
        return updated_df
    # Prompt the user to update constants
    root = tk.Tk()
    root.withdraw()  # Hide the root window temporarily
    response = messagebox.askyesno(
        "Auto-Update Constants",
        "Do you want to update material costs and machine constants?"
    )

    if response:
        materials_file = "path/to/material_costs.docx"  # Update path
        machine_file = "path/to/machine_constants.xlsx"  # Update path
        try:
            df = auto_update_constants(materials_file, machine_file, df)
            messagebox.showinfo("Success", "Factory Set Constants updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update constants: {e}")

    root.destroy()'''    
    # Filter variables by category
    factory_set_constants = df[df["Factory Set Constant"] == 1]
    customer_dependant_variables = df[df["Customer Dependant Variable"] == 1]
    customer_variables = df[df["Customer Variable"] == 1]

    # Initialize dictionaries for inputs and current labels
    inputs = {}
    current_labels = {}

    # Function to handle the "Generate Estimate" button click
    def generate():
        try:
            # Get company name and job description
            company_name = company_name_entry.get().strip()
            job_description = job_desc_entry.get().strip()

            # Validate inputs
            if not company_name:
                result_label_generate.config(text="Error: Company Name cannot be empty.", fg="red")
                return
            if not job_description:
                result_label_generate.config(text="Error: Job Description cannot be empty.", fg="red")
                return

            # Collect inquiry updates
            inquiry_updates = {}
            for var, entry in inputs.items():
                value = entry.get().strip()
                if value:  # If the input is not blank
                    try:
                        inquiry_updates[var] = float(value)
                    except ValueError:
                        result_label_generate.config(text=f"Invalid value for {var}. Please enter a number.", fg="red")
                        return

            # Generate the estimate
            estimate_number = get_next_estimate_number()
            generate_estimate(company_name, job_description, estimate_number, inquiry_updates)

            # Display success message
            result_label_generate.config(
                text=f"Estimate #{estimate_number} generated successfully!\nInvoice created in the 'invoices' folder.",
                fg="green"
            )
        except Exception as e:
            result_label_generate.config(text=f"Error: {e}", fg="red")

    # Function to handle the "Retrieve Estimate" button click
    def retrieve():
        try:
            estimate_number = estimate_number_entry.get().strip()
            if not estimate_number.isdigit():
                result_label_retrieve.config(text="Error: Please enter a valid estimate number.", fg="red")
                return

            # Retrieve the metadata
            metadata = retrieve_estimate_meta(int(estimate_number))

            # Update metadata labels
            company_name_label.config(text=f"Company Name: {metadata['company_name']}")
            job_description_label.config(text=f"Job Description: {metadata['job_description']}")
            date_label.config(text=f"Date: {metadata['date']}")
            time_label.config(text=f"Time: {metadata['time']}")
            final_estimate_label.config(text=f"Final Estimate: £{metadata['final_estimate']:.2f}")

            # Retrieve variable data
            variable_data = retrieve_estimate_data(int(estimate_number))

            # Display variable data in the retrieve tab
            row = 8
            row = add_variables_to_retrieve_tab(retrieve_content, customer_variables, "Customer Variables", row, variable_data)
            row = add_variables_to_retrieve_tab(retrieve_content, customer_dependant_variables, "Customer Dependant Variables", row, variable_data)
            add_variables_to_retrieve_tab(retrieve_content, factory_set_constants, "Factory Set Constants", row, variable_data)

            result_label_retrieve.config(text=f"Estimate #{estimate_number} retrieved successfully.", fg="green")
        except Exception as e:
            result_label_retrieve.config(text=f"Error: {e}", fg="red")
    
    # Create scrollable window
    def create_scrollable_frame(parent):
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        return scrollable_frame
      
    # Initialize the Tkinter window
    root = tk.Tk()
    root.title("Estimate Generator")

    # Create notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Create frames for each tab
    generate_tab = tk.Frame(notebook)
    retrieve_tab = tk.Frame(notebook)
    notebook.add(generate_tab, text="Generate Estimate")
    notebook.add(retrieve_tab, text="Retrieve Estimate")

    # Add scrollable frames to each tab
    generate_content = create_scrollable_frame(generate_tab)
    retrieve_content = create_scrollable_frame(retrieve_tab)

    # Generate Estimate Tab
    tk.Label(generate_content, text="Company Name").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    company_name_entry = tk.Entry(generate_content, width=30)
    company_name_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(generate_content, text="Job Description").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    job_desc_entry = tk.Entry(generate_content, width=30)
    job_desc_entry.grid(row=1, column=1, padx=10, pady=5)

    # Function to add variables to the GUI for Generate Tab
    def add_variables_to_generate_tab(parent, variables, header, start_row):
        tk.Label(parent, text=header, font=("Helvetica", 14)).grid(row=start_row, column=0, columnspan=3, pady=10)
        row = start_row + 1
        for var in variables.index:
            multiplier = variables.loc[var, "Multiplier"]

            # Variable name
            tk.Label(parent, text=var).grid(row=row, column=0, sticky="w", padx=10, pady=2)

            # Input box for new multiplier
            entry = tk.Entry(parent, width=10)
            entry.grid(row=row, column=1, padx=10, pady=2)
            inputs[var] = entry

            # Current multiplier
            current_label = tk.Label(parent, text=f"Current: {multiplier:.5f}")
            current_label.grid(row=row, column=2, sticky="w", padx=10, pady=2)
            current_labels[var] = current_label  # Save reference to the label
            row += 1
        return row

    # Add variables to the Generate Estimate tab
    current_row = 2
    current_row = add_variables_to_generate_tab(generate_content, customer_variables, "Customer Variables", current_row)
    current_row = add_variables_to_generate_tab(generate_content, customer_dependant_variables, "Customer Dependant Variables", current_row)
    current_row = add_variables_to_generate_tab(generate_content, factory_set_constants, "Factory Set Constants", current_row)

    # Generate Estimate button
    generate_button = tk.Button(generate_content, text="Generate Estimate", command=generate)
    generate_button.grid(row=current_row, column=0, columnspan=3, pady=10)

    # Result label for Generate Estimate tab
    result_label_generate = tk.Label(generate_content, text="", fg="green")
    result_label_generate.grid(row=current_row + 1, column=0, columnspan=3, pady=10)

    # Retrieve Estimate Tab
    tk.Label(retrieve_content, text="Estimate Number").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    estimate_number_entry = tk.Entry(retrieve_content, width=10)
    estimate_number_entry.grid(row=0, column=1, padx=10, pady=5)

    retrieve_button = tk.Button(retrieve_content, text="Retrieve Estimate", command=retrieve)
    retrieve_button.grid(row=1, column=0, padx=10, pady=5)

    load_recent_button = tk.Button(retrieve_content, text="Load Recent", command=load_recent_estimate)
    load_recent_button.grid(row=1, column=1, padx=10, pady=5)

    # Labels for displaying metadata
    company_name_label = tk.Label(retrieve_content, text="Company Name:")
    company_name_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)

    job_description_label = tk.Label(retrieve_content, text="Job Description:")
    job_description_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=5)

    date_label = tk.Label(retrieve_content, text="Date:")
    date_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=5)

    time_label = tk.Label(retrieve_content, text="Time:")
    time_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=5)

    final_estimate_label = tk.Label(retrieve_content, text="Final Estimate:")
    final_estimate_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=10, pady=5)

    # Function to add variables to the GUI for Retrieve Tab
    def add_variables_to_retrieve_tab(parent, variables, header, start_row, variable_data):
        tk.Label(parent, text=header, font=("Helvetica", 14)).grid(row=start_row, column=0, columnspan=3, pady=10)
        row = start_row + 1
        for var in variables.index:
            # Safely get value from retrieved data
            value = variable_data.loc[var, "Multiplier"] if var in variable_data.index else "N/A"

            # Display variable name and retrieved value
            tk.Label(parent, text=f"{var}: {value}").grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
            row += 1
        return row

    # Result label for Retrieve Estimate tab
    result_label_retrieve = tk.Label(retrieve_content, text="", fg="green")
    result_label_retrieve.grid(row=7, column=0, columnspan=2, pady=10)

    # Run the Tkinter event loop
    root.mainloop()


# Launch the GUI
if __name__ == "__main__":
    launch_gui()