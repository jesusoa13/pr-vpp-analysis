# %%
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from datetime import datetime
import os
import re

# ========== CONFIG ==========
OUTPUT_PATH = "/Users/jesusortiz/Documents/projects/02_energy/01_data/02_tesla_data/tesla_powerwall_summary.parquet"
URL = "https://www.tesla.com/puerto-rico"
WAIT_SECONDS = 10
STAT_LABEL_ORDER = [
    "Powerwalls in Puerto Rico VPPs",
    "Powerwalls in Backup Mode",
    "Powerwalls in VPP Event",
    "Battery Power"
]
BATTERY_PREFIX = "Battery Power"
# ============================

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_powerwall_stats(driver):
    stats = {}
    tesla_reported_time = None

    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(WAIT_SECONDS)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]

        # Grab Tesla-reported time
        for line in lines:
            match = re.search(r'Live as of: (\d{1,2}:\d{2}\s*[APMapm]{2})', line)
            if match:
                tesla_time = match.group(1).strip()
                try:
                    tesla_dt = datetime.strptime(tesla_time, "%I:%M %p")
                    tesla_reported_time = tesla_dt
                except ValueError:
                    pass
                break

        i = 0
        found_index = None
        while i < len(lines) - 1:
            value_line = lines[i]
            label_line = lines[i + 1]

            if re.match(r'^[\d,]+$', value_line) and label_line == STAT_LABEL_ORDER[0]:
                value = int(value_line.replace(',', ''))
                stats[label_line] = value
                found_index = i
                break
            i += 1

        if found_index is not None:
            i = found_index + 2
            expected = 1
            while i < len(lines) - 1 and expected < len(STAT_LABEL_ORDER):
                value_line = lines[i]
                label_line = lines[i + 1]

                # Battery stat
                if expected == 3 and BATTERY_PREFIX in label_line:
                    match = re.match(r'^([\d,]*\.?\d+)\s*MW$', value_line)
                    if match:
                        mw_value = float(match.group(1).replace(',', ''))
                        stats[label_line] = mw_value
                        break
                else:
                    if re.match(r'^[\d,]+$', value_line) and label_line == STAT_LABEL_ORDER[expected]:
                        value = int(value_line.replace(',', ''))
                        stats[label_line] = value
                        expected += 1
                        i += 2
                        continue
                i += 1

        return stats, tesla_reported_time

    except Exception as e:
        print(f"❌ Error extracting stats: {e}")
        return {}, None

def main():
    print("🔋 Running Tesla Powerwall Statistics Scraper")

    driver = setup_driver()
    try:
        driver.get(URL)
        stats, tesla_dt = extract_powerwall_stats(driver)

        if not stats:
            print("❌ No statistics were extracted!")
            return

        now = datetime.now()
        date_str = now.date().isoformat()
        hour_run = now.hour
        minute_run = now.minute

        tesla_hour = tesla_dt.hour if tesla_dt else None
        tesla_minute = tesla_dt.minute if tesla_dt else None

        data = []
        for variable, value in stats.items():
            unit = 'MW' if isinstance(value, float) else 'count'
            data.append({
                'variable': variable.replace('·', '-').strip(),
                'value': value,
                'unit': unit,
                'date_collected': date_str,
                'hour_run': hour_run,
                'minute_run': minute_run,
                'tesla_hour_reported': tesla_hour,
                'tesla_minute_reported': tesla_minute
            })

        df = pd.DataFrame(data)

        # Ensure consistent column order
        df = df[['variable', 'value', 'unit', 'date_collected', 
                 'hour_run', 'minute_run', 'tesla_hour_reported', 
                 'tesla_minute_reported']]

        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

        if os.path.exists(OUTPUT_PATH):
            existing_df = pd.read_parquet(OUTPUT_PATH)
            mask = (
                (existing_df["date_collected"] == date_str) &
                (existing_df["hour_run"] == hour_run) &
                (existing_df["minute_run"] == minute_run) &
                (existing_df["variable"].isin(df["variable"]))
            )
            existing_df = existing_df[~mask]
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df.to_parquet(OUTPUT_PATH, index=False)
        else:
            df.to_parquet(OUTPUT_PATH, index=False)

        print(f"✅ Data collected for {date_str} {hour_run:02d}:{minute_run:02d} saved to {OUTPUT_PATH}")
        print(df.head().to_string(index=False))

    except Exception as e:
        print(f"❌ Error during scraping: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()


