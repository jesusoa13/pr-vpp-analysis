# %%
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime, timedelta
import time
import os

# ========== CONFIG ==========
OUTPUT_PATH = "/Users/jesusortiz/Documents/projects/02_energy/01_data/01_luma_data/luma_system_summary.parquet"
URL = "https://lumapr.com/resumen-del-sistema/"
WAIT_SECONDS = 7
# ============================

print("\U0001F4A1 Starting LUMA System Summary Scraper")

# Start headless browser
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(URL)
time.sleep(WAIT_SECONDS)

tabs = [
    ("Suministro Base", '//*[contains(text(), "Suministro Base")]'),
    ("Suministros Pico", '//*[contains(text(), "Suministros Pico")]'),
    ("Suministro Renovable", '//*[contains(text(), "Suministro Renovable")]')
]

all_data = []
for label, xpath in tabs:
    try:
        tab_element = WebDriverWait(driver, WAIT_SECONDS).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        tab_element.click()
        time.sleep(2)

        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = page_text.splitlines()

        keywords = [
            'Demanda Actual', 'Demanda Próxima', 'Reserva Actual', 'Demanda Pico', 'Reserva Pico',
            'Suministro Base', 'Suministros Pico', 'Suministro Renovable',
            'San Juan', 'Palo Seco', 'Aguirre', 'Costa Sur', 'Eco Eléctrica', 'AES',
            'Mayaguez', 'Cambalache', 'Turbina de Gas', 'Ciclo Combinado Aguirre',
            'Palo Seco TM', 'San Juan TM', 'Solar', 'Viento', 'Gas de Vertedero', 'Hydroeléctrico'
        ]

        tab_data = []
        i = 0
        while i < len(lines):
            if lines[i] in keywords:
                label_text = lines[i]
                if i + 1 < len(lines) and lines[i + 1] == 'MW':
                    val1 = lines[i + 2] if i + 2 < len(lines) else None
                    val2 = lines[i + 3] if i + 3 < len(lines) else None
                    tab_data.append([label_text, val1, val2, label])
                    i += 4
                elif i + 1 < len(lines) and 'MW' in lines[i + 1]:
                    val = lines[i + 1].replace('MW', '').strip()
                    if label_text in ['Demanda Pico', 'Reserva Pico']:
                        tab_data.append([label_text, None, val, label])
                    else:
                        tab_data.append([label_text, val, None, label])
                    i += 2
                else:
                    i += 1
            else:
                i += 1

        all_data.extend(tab_data)

    except Exception as e:
        print(f"\u26a0\ufe0f Error processing tab {label}: {e}")
        continue

driver.quit()

now = datetime.now()
date_str = now.date().isoformat()
hour_run = now.hour
minute_run = now.minute

# Create DataFrame
df = pd.DataFrame(all_data, columns=["variable", "max_amount", "act_amount", "source_tab"])
df["date_collected"] = date_str
df["hour_run"] = hour_run
df["minute_run"] = minute_run

# Clean and prioritize data
df["max_amount"] = pd.to_numeric(df["max_amount"], errors="coerce")
df["act_amount"] = pd.to_numeric(df["act_amount"], errors="coerce")

df["source_tab_priority"] = df["source_tab"].map({
    "Suministro Base": 0,
    "Suministros Pico": 1,
    "Suministro Renovable": 2
})
df = (
    df
    .sort_values(["variable", "source_tab_priority"])
    .drop_duplicates(subset=["date_collected", "hour_run", "variable"], keep="first")
    .drop(columns="source_tab_priority")
)

# ========== SAVE LOGIC ==========
if os.path.exists(OUTPUT_PATH):
    existing_df = pd.read_parquet(OUTPUT_PATH)
    
    # Add fallback for legacy data
    if "source_tab" not in existing_df.columns:
        existing_df["source_tab"] = "Suministro Base"

    mask = (
        (existing_df["date_collected"] == date_str) &
        (existing_df["hour_run"] == hour_run) &
        (existing_df["minute_run"] == minute_run) &
        (existing_df["variable"].isin(df["variable"]))
    )
    existing_df = existing_df[~mask]

    combined_df = pd.concat([existing_df, df], ignore_index=True)

    # Preserve source_tab priority for visual clarity
    combined_df["source_tab_priority"] = combined_df["source_tab"].map({
        "Suministro Base": 0,
        "Suministros Pico": 1,
        "Suministro Renovable": 2
    })

    combined_df = combined_df.sort_values(["variable", "source_tab_priority"])
    combined_df = combined_df.drop(columns="source_tab_priority")
    combined_df.to_parquet(OUTPUT_PATH, index=False)
else:
    df.to_parquet(OUTPUT_PATH, index=False)

print(f"✅ LUMA data collected and saved for {date_str} at hour {hour_run}")
print(df.head().to_string(index=False))



