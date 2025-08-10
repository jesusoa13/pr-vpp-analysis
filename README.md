# ⚡ Puerto Rico Energy Scrapers & VPP Analysis

Automated half-hour scrapers for LUMA and Tesla energy data on macOS, plus a polars notebook that builds presentation-grade charts:
* Daily stacked supply (Base / Peak / Renewable / VPP Discharge)
* Peak-hour waterfall (zoom-in composition)

> **Why**: quantify how Tesla’s Virtual Power Plant contributes to Puerto Rico’s supply mix—especially at the evening peak.

## 📄 What's included

* **Scrapers** (every 30 minutes):

    * **Tesla:** Powerwall stats + B**attery Power – Discharging**

    * **LUMA:** Supply by generation plant and source_tab (Base / Pico / Renovable)

* **Notebook:** type-clean, de-duplicate intrahour rows (earliest minute per hour), aggregate by hour, and plot.

* **Outputs:** clean PNG/SVG charts, saved to `06_outputs/02_plots/`.

## 🗂️ Folder Structure

```css
02_energy/
├─ 01_data/
│  ├─ 01_luma_data/
│  │  └─ luma_system_summary.parquet
│  └─ 02_tesla_data/
│     └─ tesla_powerwall_summary.parquet
├─ 02_scripts/
│  ├─ 01_luma_data.py
│  ├─ 02_tesla_data.py
│  ├─ KeepAwake/                # optional macOS helper
│  └─ run_energy_scrapers.sh
├─ 03_notebooks/
│  └─ 01_supply_vpp_daily.ipynb
├─ 04_logs/
│  └─ energy_scraper.log
├─ 05_docs/
├─ 06_outputs/
│  ├─ 01_tables/
│  └─ 02_plots/
│     ├─ supply_stack_YYYY-MM-DD.png
│     ├─ supply_stack_YYYY-MM-DD.svg
│     ├─ peak_waterfall_YYYY-MM-DD_HH00.png
│     └─ peak_waterfall_YYYY-MM-DD_HH00.svg
├─ requirements.txt
└─ README.md
```

## ⚙️ Setup & Installation

### 1. Clone & environment

```bash 
# from your projects folder
git clone <your-repo-url> 02_energy
cd 02_energy

# use your base conda env or create a new one
conda activate base
pip install -r requirements.txt
```

**Requirements**
```shell
polars>=1.0
pandas>=2.2
numpy>=1.26
matplotlib>=3.8
selenium>=4.20
webdriver-manager>=4.0
pyarrow>=16.0
```

> Tip: If you prefer conda, create an `environment.yml`. Keep Selenium/WebDriver pinned if Chrome updates frequently.

## 🚀 Run the Scrapers

✅ **Manual Run**

Use this command any time:

```bash
~/path/to/your/projects/02_energy/02_scripts/run_energy_scrapers.sh >> ~/path/to/your/projects/02_energy/04_logs/energy_scraper.log 2>&1
```

Expected results:
* Timestamped entries in `04_logs/energy_scraper.log`

* Updated `.parquet` files with no duplicate entries.

## ⏱️ Automating with Cron

1. **Open the crontab editor**
```bash
crontab - e
```

2. **Add the following line to run the scraper every 30 minutes**
```bash
0,30 * * * * /bin/bash /path/to/your/projects/02_energy/02_scripts/run_energy_scrapers.sh >> /path/to/your/projects/02_energy/04_logs/energy_scraper.log 2>&1
```
Replace the path accordingly

3. **Save and exit**
    
    * Press `Esc`

    * Type `:wq`

    * Hit `Enter`

**To verify:**
```bash
crontab -l
```

To remove later:
```bash
crontab -e
```

(Then move to the line and type `dd` to delete and save with `:wq`)

## 💻 Preventing macOS from Sleeping 

To keep your Mac awake in the background:
```bash
caffeinate -dimsu &
```

**Or create a `.app`:**

1. Open `Script Editor`

2. Paste: 
    ```
    applescript
    
    do shell script "caffeinate -dimsu &"
    ```

3. Save as: `KeepMacAwake.app` in inside the project folder.

4. Enable it via:  

    **System Settings > Login Items > Open at Login**

You’ll see it running in the menu bar as a  gear icon ⛭

## 📓 Notebook: analysis & charts
Open:
```bash
03_notebooks/01_supply_vpp_daily.ipynb
```
Then notebook:
* Excludes the startup date (2025-08-03) and today for partial hours.

* Builds a long table with hourly supply by source_tab + VPP discharge.

* Produces two charts, saved under 06_outputs/02_plots/:

    * supply_stack_YYYY-MM-DD.(png|svg)

    * peak_waterfall_YYYY-MM-DD_HH00.(png|svg)

    **Chart examples (filenames will match your analysis day)**

> Visual style: light grey for Base, dark blue for Peak, dark orange for Renewable, accent for VPP; white background; no chart junk.

## 📝 Notes on method
* **Intrahour handling:** keep the **earliest minute** per hour to avoid double-counting (scrapers run every 30 minutes).

* **Coverage check:** both sources must have at least one record per hour in the shared window; **today** is ignored.

* **Harmonization:** LUMA `source_tab` names mapped to English; Tesla `"Battery Power – Discharging"` mapped to **VPP Discharge**.

* **Rounding:** values shown as whole MW for clarity.

## 🛠️ Troubleshooting

**No new logs or data?**
* Ensure the Mac is not asleep
* Confirm cron is active (`crontab -l`)
* Try a manual run and check for log updates
* Inspect `energy_scraper.log` for errors
* Add diagnostic prints like `python --version` or `which python` inside the script

## 🔒 Data & License
* Data from public dashboards; this repo is **not affiliated** with LUMA or Tesla.

## 👨🏽‍💻 Author
Maintained by Jesús Ortiz

*Last updated: August 9, 2025*