import json
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import pandas as pd

# Set up Edge options
edge_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
edge_options.add_argument(f"--user-agent={user_agent}")
edge_options.add_argument("--headless")
edge_options.add_argument("--disable-gpu")  # Disable GPU acceleration
edge_options.add_argument("--no-sandbox")  
edge_options.page_load_strategy = 'eager'  
edge_options.add_argument('--blink-settings=imagesEnabled=false')

prefs = {
    "download.default_directory": "/Users/abrahamaustin/Downloads/Risk Project/backend/functionality/risk-score/nasdaq_download",
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
edge_options.add_experimental_option("prefs", prefs)

# Initialize the WebDriver

def scroll_into_view(driver, xpath, description):
    
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({ block: 'center', inline: 'center' });", element)
        time.sleep(1)
        return element
    except Exception as e:
        print(f"Error during {description}: {e}")
        return None

def click_element(element, description):
    try:
        element.click()
        time.sleep(3)
    except Exception as e:
        print(f"Error during {description}: {e}")

def fetchNasdaqCSV():
    driver = webdriver.Edge(options=edge_options)

    driver.get("https://www.nasdaq.com/market-activity/stocks/screener")
    driver.maximize_window()

    try:
        outer_scroll = scroll_into_view(driver, "//h3[text()='Country']", "outer scrolling to 'Country'")
        if outer_scroll is None:
            return

        inner_scroll = scroll_into_view(driver, '//*[@for="checkboxItemunited_states"]', "scrolling to 'United States' checkbox")
        if inner_scroll is None:
            return
        inner_scroll.click()
        time.sleep(3)

        apply_button = scroll_into_view(driver, '//button[@class="nasdaq-screener__form-button--apply"]', "scrolling to 'Apply' button")
        if apply_button is None:
            return
        click_element(apply_button, "clicking 'Apply' button")

        download_button = scroll_into_view(driver, '//button[@class="nasdaq-screener__form-button--download ns-download-1"]', "scrolling to 'Download' button")
        if download_button is None:
            return
        click_element(download_button, "clicking 'Download' button")

    finally:
        driver.quit()

def get_most_recent_csv(directory, prefix):
    # List all files in the directory
    files = os.listdir(directory)
    
    # Filter files that start with the given prefix and have .csv extension
    csv_files = [f for f in files if f.startswith(prefix) and f.endswith('.csv')]
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found with prefix '{prefix}'")
    
    # Get the full paths of the files
    csv_files_full_path = [os.path.join(directory, f) for f in csv_files]
    
    # Find the most recent file based on modification time
    most_recent_file = max(csv_files_full_path, key=os.path.getmtime)
    
    return most_recent_file

def cleanNasdaqCSV():
    recent_csv = get_most_recent_csv(prefs["download.default_directory"], "nasdaq")
    df = pd.read_csv(recent_csv)
    print("DataFrame created from the most recent CSV file:")
    print(df)
    
    columns_to_drop = ['Net Change', '% Change', 'Country', 'IPO Year', 'Volume']  

    # Check if each column exists before attempting to drop it
    columns_found = [col for col in columns_to_drop if col in df.columns]
    columns_not_found = [col for col in columns_to_drop if col not in df.columns]

    if columns_found:
        df.drop(columns=columns_found, inplace=True)
        print(f"Columns {columns_found} dropped successfully.")
    if columns_not_found:
        print(f"Columns {columns_not_found} not found in the DataFrame.")

    df.to_csv(recent_csv, index=False)
    print(f"Original CSV file '{recent_csv}' updated successfully.")

def fetchCIKs():
    driver = webdriver.Edge(options=edge_options)
    driver.get("https://www.sec.gov/files/company_tickers_exchange.json")
    driver.maximize_window()
    try:
        hidden_div = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@hidden='true']")))
        # Use JavaScript to get the content of the hidden <div> directly
        div_content = driver.execute_script("return arguments[0].innerText;", hidden_div)
        # Convert the content to a JSON object
        json_data = json.loads(div_content)
        # Construct the file path using prefs.default_directory
        json_file_path = os.path.join(prefs["download.default_directory"], "CIK_Data.json")
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        driver.quit()


def main():
    try:
        fetchNasdaqCSV()
    except Exception as e:
        print("Error: {e}")
    #cleanNasdaqCSV()
    fetchCIKs()

if __name__ == "__main__":
    main()