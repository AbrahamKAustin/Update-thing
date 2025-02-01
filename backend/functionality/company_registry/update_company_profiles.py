import json
import time
import os
import pandas as pd
import psycopg2
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

download_default_directory = os.getenv('DOWNLOAD_DEFAULT_DIRECTORY')
edge_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
edge_options.add_argument(f"--user-agent={user_agent}")
edge_options.add_argument("--headless")
edge_options.add_argument("--disable-gpu")
edge_options.add_argument("--no-sandbox")
edge_options.page_load_strategy = 'eager'
edge_options.add_argument('--blink-settings=imagesEnabled=false')

prefs = {
    "download.default_directory": download_default_directory,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
edge_options.add_experimental_option("prefs", prefs)


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
        # Scroll to the country selector and select United States
        outer_scroll = scroll_into_view(driver, "//h3[text()='Country']", "scrolling to 'Country'")
        if outer_scroll is None:
            return
        inner_scroll = scroll_into_view(driver, '//*[@for="checkboxItemunited_states"]', "scrolling to 'United States' checkbox")
        if inner_scroll is None:
            return
        inner_scroll.click()
        time.sleep(3)
        # Click the apply button
        apply_button = scroll_into_view(driver, '//button[@class="nasdaq-screener__form-button--apply"]', "scrolling to 'Apply' button")
        if apply_button is None:
            return
        click_element(apply_button, "clicking 'Apply' button")
        # Download the CSV file
        download_button = scroll_into_view(driver, '//button[@class="nasdaq-screener__form-button--download ns-download-1"]', "scrolling to 'Download' button")
        if download_button is None:
            return
        click_element(download_button, "clicking 'Download' button")
    finally:
        driver.quit()


def get_most_recent_file(directory, prefix, extension):
    files = os.listdir(directory)
    matching_files = [f for f in files if f.startswith(prefix) and f.endswith(extension)]
    if not matching_files:
        raise FileNotFoundError(f"No files found with prefix '{prefix}' and extension '{extension}'")
    matching_files_full_path = [os.path.join(directory, f) for f in matching_files]
    most_recent_file = max(matching_files_full_path, key=os.path.getmtime)
    return most_recent_file


def cleanNasdaqCSV():
    recent_csv = get_most_recent_file(prefs["download.default_directory"], "nasdaq", ".csv")
    df = pd.read_csv(recent_csv)
    
    # Drop unwanted columns
    columns_to_drop = ['Net Change', '% Change', 'Country', 'IPO Year', 'Volume', 'Last Sale']
    columns_found = [col for col in columns_to_drop if col in df.columns]
    if columns_found:
        df.drop(columns=columns_found, inplace=True)
    else:
        raise Exception("Expected columns not found in the DataFrame.")
    
    return df


def fetchCIKs():
    driver = webdriver.Edge(options=edge_options)
    driver.get("https://www.sec.gov/files/company_tickers_exchange.json")
    driver.maximize_window()
    try:
        hidden_div = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@hidden='true']")))
        div_content = driver.execute_script("return arguments[0].innerText;", hidden_div)
        json_data = json.loads(div_content)
        json_file_path = os.path.join(prefs["download.default_directory"], "CIK_Data.json")
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()


def main():
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    DATABASE_HOST = os.getenv('DATABASE_HOST')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    
    try:
        fetchNasdaqCSV()
        cleanedNasdaqDF = cleanNasdaqCSV()
    except Exception as e:
        print(f"Error during CSV fetching/cleaning: {e}")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=DATABASE_HOST,
            database=POSTGRES_DB
        )
        print("Connection established")
        cursor = conn.cursor()

        # Get existing companies (only ticker)
        query = "SELECT ticker FROM company_reference"
        cursor.execute(query)
        databaseDF = pd.DataFrame(cursor.fetchall(), columns=['Symbol'])

        # Normalize ticker symbols and identify new entries
        cleanedNasdaqDF['Symbol'] = cleanedNasdaqDF['Symbol'].str.strip().str.upper()
        differenceDF = cleanedNasdaqDF[~cleanedNasdaqDF['Symbol'].isin(databaseDF['Symbol'])]

        # Process new entries by merging with CIK data
        if not differenceDF.empty:
            fetchCIKs()
            with open(get_most_recent_file(prefs["download.default_directory"], "CIK", ".json")) as f:
                json_data = json.load(f)
            fields = json_data.get("fields", [])
            data = json_data.get("data", [])
            if not fields or not data:
                raise ValueError("JSON data is missing 'fields' or 'data'.")
            try:
                cikDF = pd.DataFrame(data, columns=fields)
                print("CIK DataFrame created successfully.")
            except ValueError as e:
                print(f"Error creating CIK DataFrame: {e}")

            # Normalize ticker symbols for merging
            differenceDF['Symbol'] = differenceDF['Symbol'].str.strip().str.upper()
            cikDF['ticker'] = cikDF['ticker'].str.strip().str.upper()

            cikDF['cik'] = cikDF['cik'].astype(str).str.zfill(10)


            # Merge CIK data with Nasdaq data for new entries
            merged_df = differenceDF.merge(cikDF, left_on='Symbol', right_on='ticker', how='inner')
            completeData = merged_df.drop(columns=['ticker', 'name'])

            try:
                insert_query = """
                INSERT INTO company_reference (ticker, name, market_cap, sector, industry, cik, exchange)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker) DO NOTHING;
                """
                data_to_insert = [
                    (
                        row['Symbol'],
                        row['Name'],
                        row['Market Cap'],
                        row['Sector'],
                        row['Industry'],
                        row['cik'],
                        row['exchange']
                    )
                    for index, row in completeData.iterrows()
                ]
                cursor.executemany(insert_query, data_to_insert)
                conn.commit()
                print("New company entries inserted successfully.")
            except psycopg2.Error as e:
                print(f"Database error during insertion: {e}")
            except Exception as e:
                print(f"Error during insertion: {e}")
        else:
            print("No new entries found.")

    except Exception as e:
        print(f"Could not establish connection: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()