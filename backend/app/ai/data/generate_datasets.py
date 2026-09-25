"""Deterministic Synthetic Dataset Generator for FinMate AI Models.

Produces:
1. Transaction Classification: Training and Evaluation CSVs.
2. Monthly Expense Forecasting: Training and Evaluation CSVs.

Academic Context:
CIT 19MAM54 AI Systems Engineering - Phase 3.
Real user data is strictly separated from synthetic training data.
"""

import csv
import os
import random
from typing import List, Tuple

# Set fixed seed for 100% reproducibility
SEED = 42
random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAIN_DIR = os.path.join(BASE_DIR, "training")
EVAL_DIR = os.path.join(BASE_DIR, "evaluation")

os.makedirs(TRAIN_DIR, exist_ok=True)
os.makedirs(EVAL_DIR, exist_ok=True)

CATEGORIES_DATA = {
    "Food": {
        "merchants": [
            "Swiggy order", "Zomato online delivery", "McDonald's drive-thru", "Starbucks coffee",
            "Cafe Coffee Day cappuccino", "Chai Point tea & snacks", "Domino's Pizza delivery",
            "Paradise Biryani takeaway", "Haldiram's dinner", "Subway club sub", "KFC crispy chicken",
            "Blinkit grocery essentials", "Zepto quick grocery", "BigBasket daily veggies",
            "Local vegetable market", "Dunkin Donuts breakfast", "Burger King combo meal",
            "Pind Balluchi family dinner", "Mainland China lunch", "Sagar Ratna south indian meal"
        ],
        "types": ["expense"],
        "min_amt": 80,
        "max_amt": 3500,
    },
    "Shopping": {
        "merchants": [
            "Amazon retail purchase", "Flipkart order electronics", "Myntra fashion apparel",
            "Zara clothing store", "H&M cotton shirt", "Ajio footwear", "Nykaa cosmetics order",
            "Croma electronics accessory", "Vijay Sales home appliance", "Reliance Digital headphones",
            "Decathlon sports gear", "IKEA home decor", "Uniqlo winter wear", "Shoppers Stop casuals",
            "Lifestyle sunglasses purchase", "Tanishq silver jewellery", "Apple Store USB cable",
            "Titan watch showroom", "Puma running shoes", "Woodland leather wallet"
        ],
        "types": ["expense"],
        "min_amt": 400,
        "max_amt": 25000,
    },
    "Transport": {
        "merchants": [
            "Uber premier cab ride", "Ola autos commute", "Rapido bike taxi", "Namma Metro card recharge",
            "Delhi Metro smart card", "Indian Oil fuel pump petrol", "Bharat Petroleum diesel fill",
            "Shell India premium fuel", "FASTag toll recharge NH48", "IRCTC railway train ticket",
            "IndiGo flight ticket booking", "Air India domestic flight", "RedBus intercity bus seat",
            "Auto rickshaw meter payment", "Airport parking payment", "HPCL petrol station refill",
            "Chalo bus card recharge", "Zoomcar rental deposit", "Cycle service station", "Car wash express"
        ],
        "types": ["expense"],
        "min_amt": 50,
        "max_amt": 8500,
    },
    "Entertainment": {
        "merchants": [
            "Netflix 4K UHD monthly subscription", "Spotify premium family plan", "BookMyShow cinema tickets",
            "Amazon Prime annual membership", "YouTube Premium family bundle", "Disney+ Hotstar super plan",
            "SonyLIV entertainment pass", "PVR Cinemas IMAX weekend tickets", "Steam games online store",
            "PlayStation Plus quarterly network", "Audible audiobooks monthly credit", "Apple Music individual",
            "JioCinema premium subscription", "Comic con pass booking", "Standup comedy open mic ticket",
            "Inox multiplex popcorn combo", "Museum entry tickets", "Smaaash gaming arcade pass"
        ],
        "types": ["expense"],
        "min_amt": 149,
        "max_amt": 2400,
    },
    "Utilities": {
        "merchants": [
            "Bescom monthly electricity bill", "Tata Power consumer bill payment", "Airtel Xstream fiber broadband",
            "Jio Fiber monthly plan recharge", "Indane LPG cooking gas cylinder refill", "Bharat Gas refill booking",
            "BWSSB water supply bill", "Mahanagar Gas piped natural gas", "Airtel prepaid 84 days recharge",
            "Jio true 5G unlimited recharge", "Vi cellular monthly bill", "Tata Play DTH recharge",
            "Society apartment maintenance levy", "Municipal waste management fee", "Solar rooftop service fee"
        ],
        "types": ["expense"],
        "min_amt": 299,
        "max_amt": 5500,
    },
    "Healthcare": {
        "merchants": [
            "Apollo Pharmacy prescription medicines", "Medplus healthcare drugs", "Practo doctor video consult",
            "Dr Lal PathLabs full blood test", "SRL Diagnostics lipid profile panel", "Manipal Hospital OPD consultation",
            "Fortis Healthcare physician visit", "Dentist clinic dental cleaning", "Netmeds online medicine order",
            "Tata 1mg healthcare vitamin supplements", "Eye care optical glasses lens", "Skin clinic consultation fee",
            "Physiotherapy rehabilitation session", "Vaccination clinic booster dose"
        ],
        "types": ["expense"],
        "min_amt": 150,
        "max_amt": 12000,
    },
    "Education": {
        "merchants": [
            "Coursera annual specialization pass", "Udemy python machine learning course", "College semester tuition fee",
            "Oxford University Press textbooks", "Cambridge IELTS exam registration fee", "GRE exam test fee payment",
            "Allen Career Institute coaching fees", "Byju's learning tablet subscription", "EdX certificate fee",
            "Local library membership renewal", "Stationery depot notebooks and pens", "Coding boot camp enrollment"
        ],
        "types": ["expense"],
        "min_amt": 499,
        "max_amt": 45000,
    },
    "Rent": {
        "merchants": [
            "Monthly apartment house rent transfer", "Flat landlord rent direct NEFT", "Stanza Living student PG rent",
            "Coliving monthly rental stay", "House deposit monthly installment", "Office studio monthly rent"
        ],
        "types": ["expense"],
        "min_amt": 8000,
        "max_amt": 35000,
    },
    "Investment": {
        "merchants": [
            "Zerodha Broking equity fund transfer", "Groww Mutual Fund monthly SIP", "Tata Silver ETF purchase order",
            "SBI Nifty 50 Index Fund direct", "Public Provident Fund PPF annual deposit", "National Pension System NPS tier 1",
            "Sovereign Gold Bond tranche investment", "Mirae Asset Large Cap Fund SIP", "Parag Parikh Flexi Cap Fund",
            "Axis Small Cap Fund monthly debit", "Fixed deposit creation ICICI bank", "Kisan Vikas Patra post office"
        ],
        "types": ["expense"],
        "min_amt": 1000,
        "max_amt": 50000,
    },
    "Salary": {
        "merchants": [
            "Monthly tech payroll salary credit", "Corporate employer net salary deposit", "Infosys Technologies monthly salary",
            "Tata Consultancy Services salary", "Wipro Limited payroll disbursement", "Accenture payroll direct credit",
            "Quarterly performance appraisal bonus", "Annual festival performance incentive", "Reimbursement medical claim credit"
        ],
        "types": ["income"],
        "min_amt": 35000,
        "max_amt": 180000,
    },
    "Freelance": {
        "merchants": [
            "Upwork Escrow freelance earnings credit", "Fiverr international gig payment", "Client UI design consulting invoice",
            "Technical writing freelance retainer", "Software development milestone payout", "Independent code audit consulting fee",
            "Content marketing retainer wire transfer", "Guest lecture honorarium credit"
        ],
        "types": ["income"],
        "min_amt": 5000,
        "max_amt": 75000,
    },
    "Other": {
        "merchants": [
            "ATM cash withdrawal transaction", "Bank account annual debit card maintenance", "Cheque clearing charge fee",
            "Friend loan repayment cash transfer", "Birthday cash gift received", "Donation to PM CARES relief fund",
            "Charity contribution CRY foundation", "Credit card annual renewal surcharge"
        ],
        "types": ["expense", "income"],
        "min_amt": 100,
        "max_amt": 10000,
    },
}


def generate_classification_datasets():
    print("[*] Generating Transaction Classification Datasets...")
    samples = []
    
    # Generate variations per category
    for cat, cfg in CATEGORIES_DATA.items():
        merchants = cfg["merchants"]
        types = cfg["types"]
        min_amt = cfg["min_amt"]
        max_amt = cfg["max_amt"]
        
        # Build 130 variations per category (130 * 12 = 1,560 total records)
        for i in range(130):
            base_desc = random.choice(merchants)
            t_type = random.choice(types)
            amt = round(random.uniform(min_amt, max_amt), 2)
            
            # Add synthetic noise/variations
            variant_choice = i % 5
            if variant_choice == 0:
                desc = f"{base_desc} Ref #{random.randint(10000, 99999)}"
            elif variant_choice == 1:
                desc = f"{base_desc} INR {amt:.2f}"
            elif variant_choice == 2:
                desc = f"UPI/{base_desc.lower().replace(' ', '')}/{random.randint(100000, 999999)}"
            elif variant_choice == 3:
                desc = f"POS {base_desc.upper()}"
            else:
                desc = base_desc
                
            samples.append((desc, f"{amt:.2f}", t_type, cat))
            
    # Shuffle deterministically
    random.shuffle(samples)
    
    # 80/20 train/eval split (1248 train / 312 eval)
    split_idx = int(len(samples) * 0.80)
    train_samples = samples[:split_idx]
    eval_samples = samples[split_idx:]
    
    train_path = os.path.join(TRAIN_DIR, "transactions_train.csv")
    eval_path = os.path.join(EVAL_DIR, "transactions_eval.csv")
    
    for path, data_subset in [(train_path, train_samples), (eval_path, eval_samples)]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["description", "amount", "transaction_type", "category"])
            for row in data_subset:
                writer.writerow(row)
                
    print(f"[+] Saved {len(train_samples)} training rows to {train_path}")
    print(f"[+] Saved {len(eval_samples)} evaluation rows to {eval_path}")


def generate_forecasting_datasets():
    print("[*] Generating Monthly Expense Forecasting Datasets...")
    # Base monthly budget simulation for 48 consecutive months (4 years: 2022 to 2025)
    # 36 months training (2022-01 to 2024-12)
    # 12 months evaluation (2025-01 to 2025-12)
    
    base_expense = 32000.0
    records = []
    
    # Seasonal multipliers by month index (0=Jan, 11=Dec)
    # Festive spikes in Oct/Nov (Diwali/Navratri), summer travel in May, school fees in June
    seasonality = [0.95, 0.92, 0.98, 1.02, 1.10, 1.15, 1.00, 0.98, 1.05, 1.25, 1.20, 1.18]
    
    year_start = 2022
    total_months = 48
    
    raw_monthly_totals = []
    
    for m_idx in range(total_months):
        year = year_start + (m_idx // 12)
        month = (m_idx % 12) + 1
        month_str = f"{year}-{month:02d}"
        
        # Secular inflation growth of ~6% per year
        inflation_factor = 1.0 + (m_idx * 0.005)
        seasonal_factor = seasonality[month - 1]
        noise = random.uniform(-1200.0, 1500.0)
        
        monthly_total = round(base_expense * inflation_factor * seasonal_factor + noise, 2)
        raw_monthly_totals.append((month_str, year, month, monthly_total))
        
    # Feature engineering for time series:
    # lagged features: lag_1, lag_2, lag_3, rolling_avg_3
    # We require 3 initial periods to form lag_3, yielding 45 usable rows
    engineered = []
    for i in range(3, len(raw_monthly_totals)):
        month_str, yr, m_num, current_exp = raw_monthly_totals[i]
        lag_1 = raw_monthly_totals[i - 1][3]
        lag_2 = raw_monthly_totals[i - 2][3]
        lag_3 = raw_monthly_totals[i - 3][3]
        rolling_3 = round((lag_1 + lag_2 + lag_3) / 3.0, 2)
        
        engineered.append({
            "month_period": month_str,
            "year": yr,
            "month_num": m_num,
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_3": lag_3,
            "rolling_avg_3": rolling_3,
            "total_expense": current_exp
        })
        
    # Chronological split: 33 months train (2022-04 to 2024-12), 12 months eval (2025-01 to 2025-12)
    # Strict chronological partition without shuffling prevents future leakage!
    train_data = [r for r in engineered if r["year"] <= 2024]
    eval_data = [r for r in engineered if r["year"] >= 2025]
    
    train_path = os.path.join(TRAIN_DIR, "expenses_monthly_train.csv")
    eval_path = os.path.join(EVAL_DIR, "expenses_monthly_eval.csv")
    
    fieldnames = ["month_period", "year", "month_num", "lag_1", "lag_2", "lag_3", "rolling_avg_3", "total_expense"]
    
    for path, data_subset in [(train_path, train_data), (eval_path, eval_data)]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in data_subset:
                writer.writerow(r)
                
    print(f"[+] Saved {len(train_data)} time-series training months to {train_path}")
    print(f"[+] Saved {len(eval_data)} time-series evaluation months to {eval_path}")


if __name__ == "__main__":
    generate_classification_datasets()
    generate_forecasting_datasets()
    print("[+] All synthetic datasets created successfully!")
