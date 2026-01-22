"""
SvanPC-Pal: Automated Noise Measurement Data Export Tool

Professional automation utility for batch processing Svantek SvanPC++ noise measurement
data files. Automates the complete workflow from file loading to Excel export with
configurable measurement profiles and logger step settings.

Features:
    - Batch processing of .SVL (Svantek Logger) files
    - Multi-profile support (NAW, Breakin Octaves, Breakin 1/3 Octaves, Spot measurements)
    - Configurable logger step intervals (10s, 1m, 2m, 15m, 1h)
    - Automated Excel export with custom naming conventions
    - Windows UI automation via pywinauto
    - Error handling and logging for missing configurations
    - Time tracking and completion reporting

Supported Job Types:
    1. Noise at Work (NAW) - Occupational noise assessments
    2. Breakin (octaves) - Building acoustics octave band analysis
    3. Breakin (one-octaves) - Building acoustics 1/3 octave band analysis
    4. Spot (one-octaves) - Short-duration spot measurements

Workflow:
    1. User selects source folder containing .SVL files
    2. User selects job type and measurement profile
    3. Script launches SvanPC++ and processes each file
    4. For each file, applies configured profile and logger steps
    5. Exports data to Excel with systematic naming
    6. Generates completion report with any configuration errors

Technical Stack:
    - pywinauto: Windows UI automation (win32 and UIA backends)
    - SvanPC++: Svantek noise measurement software integration

Author: Q-types
License: MIT
"""

import os
import sys
import time
from pywinauto.application import Application
from pywinauto import mouse

# Dictionaries for future expansion (some entries left as placeholders)
job_type_dict = {
    "1":"Noise at Work",
    "2":"Breakin (octaves)",
    "3":"Breakin (one-octaves)",
    "4":"Spot (one-octaves)"
    }
config_profile_dict = {
    "1":"NAW",
    "2":"Bo",
    "3":"B1o",
    "4":"Sp1o"
    }


NAW_profile_logger_config_dict = {
    "NAW": "default"
    }

Bo_profile_logger_config_dict = {
    "Bo-A": ["default", "def"], 
    "Bo-B": [r"^1\s*m\s*\(Factor\s*=\s*600\)$",   "1m"],
    "Bo-C": [r"^2\s*m\s*\(Factor\s*=\s*1200\)$",  "2m"],
    "Bo-D": [r"^15\s*m\s*\(Factor\s*=\s*9000\)$", "15m"],
    "Bo-E": [r"^1\s*h\s*\(Factor\s*=\s*36000\)$", "1h"]
}

B1o_profile_logger_config_dict = {
    "B1o-A": ["default", "def"], 
    "B1o-B": [r"^1\s*m\s*\(Factor\s*=\s*600\)$",   "1m"],
    "B1o-C": [r"^2\s*m\s*\(Factor\s*=\s*1200\)$",  "2m"],
    "B1o-D": [r"^15\s*m\s*\(Factor\s*=\s*9000\)$", "15m"],
    "B1o-E": [r"^1\s*h\s*\(Factor\s*=\s*36000\)$", "1h"]
}

Sp1o_profile_logger_config_dict = { 
    "Sp1o": [r"^10\s*s\s*\(Factor\s*=\s*100\)$",  "10s"]
}

Bo_profile_logger_config_name = {
    "Bo-A": "(def)", 
    "Bo-B": "(1m)", 
    "Bo-C": "(2m)", 
    "Bo-D": "(15m)", 
    "Bo-E": "(1hr)"
}

B1o_profile_logger_config_name = {
    "Bo-A": "(def)", 
    "Bo-B": "(1m)", 
    "Bo-C": "(2m)", 
    "Bo-D": "(15m)", 
    "Bo-E": "(1hr)"
}

Sp1o_profile_logger_config_name = { 
    "Sp1o": ("10s")
}

Profile_config_logger_dict = {
    "NAW": NAW_profile_logger_config_dict,
    "Bo": Bo_profile_logger_config_dict,
    "B1o": B1o_profile_logger_config_dict,
    "Sp1o": Sp1o_profile_logger_config_dict
}

profile_label_dict = {
    "Bo": Bo_profile_logger_config_name,
    "B1o": B1o_profile_logger_config_name,
    "Sp1o": Sp1o_profile_logger_config_name
}

logger_errors = [] 

def main():
    # Prompt user for SOURCE_FOLDER in console
    print("Enter the folder path containing your .SVL files:")
    SOURCE_FOLDER = input("SOURCE_FOLDER: ").strip()
    if not os.path.isdir(SOURCE_FOLDER):
        print(f"Error: '{SOURCE_FOLDER}' is not a valid directory. Exiting.")
        sys.exit(1)


    # Build new subfolder: "Exported"
    EXPORT_FOLDER = os.path.join(SOURCE_FOLDER, "exported")
    # Create the subfolder if it doesn't exist
    if not os.path.isdir(EXPORT_FOLDER):
        os.mkdir(EXPORT_FOLDER)

    print(f"Export folder is: {EXPORT_FOLDER}")



   # JOB index
    for key, value in job_type_dict.items():
        print(f"{key}. {value}")
    while True:
        n = input("Enter Job Type (1,2,3 or 4): ").strip()
        if n in job_type_dict.keys():
            break
        else:
            print(f"Error: '{n}' is not a valid entry. Please choose one from {list(job_type_dict.keys())}.\n")
    
    
    start_time = time.time()

    # ---------------------------------------------------------------------------
    # CONFIGURATION
    # ---------------------------------------------------------------------------
    SVANPC_EXE = r"C:\Program Files (x86)\Svantek\SvanPC++\SvanPCplus95x.exe"

    # HELPER: Scroll until a TreeItem is found, using the "Line down" approach
    def scroll_until_found(item_title, parent_pane, max_scrolls=30):
        line_down_btn = parent_pane.child_window(title="Line down", control_type="Button", auto_id="DownButton")
        if not line_down_btn.exists(timeout=3):
            print("Cannot find 'Line down' button! No scrolling possible.")
            return False

        for i in range(max_scrolls):
            print(f"Scroll attempt {i + 1}")
            candidate = parent_pane.child_window(title=item_title, control_type="TreeItem")
            if candidate.exists():
                print(f"Found {item_title} on scroll {i + 1}")
                return True
            line_down_btn.click_input()
            time.sleep(0.5)
        print(f"Failed to find {item_title} after {max_scrolls} scrolls")
        return False
    
    # HELPER: Scroll until a list item is found, using the "Down button" approach
    def down_until_found(item_title, parent_pane, max_scrolls=20):
        window = parent_pane.child_window()

        for i in range(max_scrolls):
            print(f"Scroll attempt {i + 1}")
            candidate = parent_pane.child_window(title=item_title, control_type="ListItem")
            if candidate.exists():
                print(f"Found {item_title} on scroll {i + 1}")
                return True
            window.type_keys('{Down}')
            time.sleep(0.5)
        print(f"Failed to find {item_title} after {max_scrolls} scrolls")
        return False


    # ---------------------------------------------------------------------------
    # LAUNCH SVANPC++ (win32)
    # ---------------------------------------------------------------------------
        # Launch SvanPC++ (win32)
    app_win32 = Application(backend="win32").start(SVANPC_EXE)
    time.sleep(2)
    main_window_win32 = app_win32.window(title_re=r"SvanPC\+\+.*")
    main_window_win32.wait("visible", timeout=20)

    # Also connect with UIA
    process_id = main_window_win32.element_info.process_id
    app_uia = Application(backend="uia").connect(process=process_id)
    main_window_uia = app_uia.window(title_re=r"SvanPC\+\+.*")
    main_window_uia.wait("visible", timeout=20)

    # Repeated UI references
    configurator_pane = main_window_uia.child_window(
        title="Configurator", 
        control_type="Pane"
        )
    table_btn = main_window_uia.child_window(
        title="Table", 
        control_type="MenuItem"
        )
    plot_btn = main_window_uia.child_window(
        title="Plot", 
        control_type="MenuItem"
        )
    send_to_excel_btn = main_window_uia.child_window(
        title="Send to MS Excel", 
        control_type="MenuItem"
        )
    ok_button = main_window_uia.child_window(
        title="OK", 
        control_type="Button"
        )

    # In toolbar:
    main_toolbar_pane = main_window_uia.child_window(
        title="ToolBar", 
        control_type="Pane", 
        found_index=0
        )
    logger_step_btn = main_toolbar_pane.child_window(
        title="Change logger step", 
        control_type="Button",
        found_index = 0        
        )
    logger_step_alt_button = main_window_uia.child_window(
        title_re=r".*ms$",
        control_type="Button",
        found_index = 0
        )
    logger_step_alt2_btn = main_window_uia.child_window(
        title="Change logger step", 
        control_type="Button",
        found_index = 0
        )
    set_logger_step_btn = main_window_uia.child_window(
        title="Logger step", 
        control_type="ComboBox"
        )

    # Change configurator settings when True
    repeat = True

    # ---------------------------------------------------------------------------
    # ITERATE OVER EACH .SVL
    # ---------------------------------------------------------------------------
 
    for file_name in os.listdir(SOURCE_FOLDER):
        if not file_name.lower().endswith(".svl"):
            continue
        
        base_name = os.path.splitext(file_name)[0]  # e.g. "001" if file_name="001.SVL"
        svl_path = os.path.join(SOURCE_FOLDER, file_name)
        print(f"\nProcessing: {svl_path}")
    
        # Set wrapper and open file
        wrapper = app_win32.window(title_re=r"SvanPC\+\+.*").wrapper_object()
        wrapper.menu_select("File->Open...")

        # Then handle the "Open" dialog
        svan_open_dialog = app_win32.window(title_re="Open.*")
        svan_open_dialog.wait("visible", timeout=10)
        svan_open_dialog.type_keys(svl_path + "{ENTER}")
        svan_open_dialog.wait_not("visible", timeout=10)

        # ---------------------------------------------------------------------------
        # ITERATE OVER EACH PROFILE AND LOGGER STEP
        # ---------------------------------------------------------------------------
    
        for profile_key, logger_list in Profile_config_logger_dict[
            config_profile_dict[n]
            ].items():
   
            # If logger step not found, change to false to skip file export
            l = True
                
            # Name logger_value and logger_label
            logger_value = logger_list[0]
            logger_label = logger_list[1]

            # Re-acquire the main UIA window
            main_window_uia = app_uia.window(title_re=r"SvanPC\+\+.*")
            #main_window_uia.wait("visible", timeout=10)

            # Build an Excel path using the .xlsx extension
            excel_path = os.path.join(
                EXPORT_FOLDER, base_name + 
                job_type_dict[n] + 
                logger_label.strip() + 
                ".xlsx"
                )
            print(f"Export Path: {excel_path}")

            # SELECT CHART 
            plot_btn.wait("visible", timeout=7)
            plot_btn.click_input()

            # Load configurator settings
            if repeat:
                load_config_settings_button = configurator_pane.child_window(
                    title="Load settings", 
                    control_type="Button"
                    )
                if not load_config_settings_button.exists():
                    # Press Alt+V
                    main_window_uia.type_keys('%v')  # '%' is the pywinauto syntax for Alt
                    main_window_uia.type_keys('{ENTER}')
                try: 
                    load_config_settings_button.click_input()
                except Exception as e:
                    print("Error finding configurtor profile button:", e)

                profile_set = main_window_uia.child_window(
                    title=profile_key, 
                    control_type="ListItem"
                    )
                if not profile_set.exists():
                    down_until_found(profile_key, main_window_uia)
                try:
                    profile_set.select()
                except Exception as e:
                    print("Error finding configurtor profile:", e)

                if len(Profile_config_logger_dict[config_profile_dict[n]])==1:
                    default_btn = main_window_uia.child_window(
                        title="Set default view settings", 
                        control_type="Button"
                        )
                    default_btn.click_input()
                    repeat = False
                else:
                    selected_btn = main_window_uia.child_window(
                        title="Apply selected settings", 
                        control_type="Button"
                        )
                    selected_btn.click_input()

                close_btn = main_window_uia.child_window(
                    title="Close", 
                    control_type="Button", 
                    found_index=1
                    )
                close_btn.click_input()

            # If logger_value != "default", change the logger step
            if logger_value != "default":
                # 1) Click the "Change logger step" button
                if logger_step_btn.exists():
                    logger_step_btn.click_input()
                elif logger_step_alt_button.exists():
                    logger_step_alt_button.click_input()
                else:
                    logger_step_alt2_btn.click_input()

                # 2) Expand the "Logger step" combo
                set_logger_step_btn.wait("exists ready", timeout=5)
                set_logger_step_btn.click_input()
                
                # 3) Click logger list item
                log_list_item = main_window_uia.child_window(
                    title_re=logger_value, 
                    control_type="ListItem"
                    )
                try:
                    log_list_item.wait("visible", timeout=2).click_input()
                    # Press enter to confirm
                    ok_button.click_input()
                    
                except Exception as e:
                    # If not found or not clickable, add an error and continue
                    logger_error_str = f"Logger step '{logger_value}' not found for file '{excel_path}': {e}"
                    print(logger_error_str)
                    logger_errors.append(logger_error_str)

                    # Attempt pressing Esc on the combo item or the combo box
                    set_logger_step_btn.wrapper_object().type_keys('{ESC}')
                    # Press enter to confirm
                    ok_button.click_input()

                    # Return to continue
                    l = False
                    

            if l:
                # SELECT DATA (Table -> click -> Ctrl+A)
                table_btn.click_input()

                # Mouse click on table area
                rect = table_btn.rectangle()
                mouse.click(
                    button="left", 
                    coords=(rect.left + 50, rect.top + 50)
                    )

                # Ctrl+A to select all
                main_window_uia.type_keys('^a')

                # Export to excel workbook
                if not send_to_excel_btn.exists():
                    #scroll_until_found("Send to MS Excel", main_window_uia)
                    main_window_uia = Application(backend="uia").connect(process=process_id)
                send_to_excel_btn.click_input()

                # Click OK button
                if ok_button.exists(timeout=3):
                    ok_button.click_input()
                    ok_button.wait_not("visible", timeout=5)

                # Connect to the opened Excel instance (win32):
                excel_app = Application(backend="win32").connect(class_name="XLMAIN", found_index=0)
                excel_window = excel_app.top_window()
                excel_window.wait("visible", timeout=10)

                # Press F12 => "Save As"
                excel_window.type_keys('{F12}')
                
                excel_save_dialog = excel_app.window(title_re="Save As.*")
                excel_save_dialog.wait("visible", timeout=10)

                # Type the new Excel path + Enter
                excel_save_dialog.type_keys(excel_path + "{ENTER}")

                # Confirm save dialog
                excel_confirm_save_dialog = excel_app.window(
                    title_re="Confirm Save As.*"
                    )
                
                # Overwrite confirm
                if excel_confirm_save_dialog.exists():
                    excel_confirm_save_dialog.type_keys('{TAB}')
                    excel_confirm_save_dialog.type_keys('{ENTER}')

                # Wait for the dialog to go away
                excel_confirm_save_dialog.wait_not(
                    "visible", 
                    timeout=3
                    )
                excel_save_dialog.wait_not(
                    "visible", 
                    timeout=2
                    )
                
                # Delete all data in excel sheet
                excel_window.type_keys('^a')
                excel_window.type_keys('{DELETE}')
                excel_window.type_keys('{UP}')

            # Connect to SvanPC++
            main_window_win32 = Application(backend="win32").connect(process=process_id)
            main_window_uia = Application(backend="uia").connect(process=process_id)

            
            
    # Try to close excel
    excel_app = Application(backend="win32").connect(
        class_name="XLMAIN", 
        found_index=0
        )
    excel_window = excel_app.top_window()
    excel_window.wait(
        "visible", 
        timeout=10
        )
    excel_window.type_keys('%{F4}')
            
    # Finally connect and exit SvanPC++
    wrapper = app_win32.window(title_re=r"SvanPC\+\+.*").wrapper_object()
    wrapper.menu_select("File->Exit")

    end_time = time.time()
    elapsed = end_time - start_time
    print("")
    print("All files processed!")
    print(f"Program completed in {elapsed:.2f} seconds.")
    print("")
    if logger_errors == []:
        print("All files exported with required logger step/config profiles.")
    else:
        print("The following files did not have all logger steps available:")
        print("")
        print(logger_errors)

if __name__ == "__main__":
    main()
