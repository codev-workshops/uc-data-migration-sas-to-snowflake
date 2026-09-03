import pandas as pd
import random
from datetime import datetime, timedelta
#import pyreadstat

# Input CSV file
input_file = "../sample_data/SASViya_Sample_Files/creditscores.csv"
output_file1 = "../sample_data/customers.csv"
output_file2 = "../sample_data/creditscore.csv"

# Load the CSV file
df = pd.read_csv(input_file)  # Assuming tab-separated, change if comma

# Function to generate email
def generate_email(name):
    domains = ["example.com", "gmail.com", "live.org", "outlook.net"]
    first_name, last_name = name.split()[0], name.split()[-1]
    email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"
    return email

# Function to generate birth date from age
def generate_birth_date(age):
    today = datetime.today()
    birth_year = today.year - age
    # Random month and day for birthdate
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Simplify to avoid invalid dates
    return datetime(birth_year, month, day).strftime("%Y-%m-%d")

# Transform the data
customers_df = pd.DataFrame()
customers_df['customer_id'] = range(1001, 1001 + len(df))
customers_df['first_name'] = df['Customer_Name'].apply(lambda x: x.split()[0])
customers_df['last_name'] = df['Customer_Name'].apply(lambda x: x.split()[-1])
customers_df['email'] = df['Customer_Name'].apply(generate_email)
customers_df['Street_Address'] = df['Street_Address']
customers_df['City'] = df['City']
customers_df['State'] = df['State']
customers_df['Zipcode'] = df['Zipcode']
customers_df['birth_dt'] = df['Age'].apply(generate_birth_date)
customers_df['Age'] = df['Age']

# Save to CSV
customers_df.to_csv(output_file1, index=False)

creditscore_df = pd.DataFrame()
creditscore_df['customer_id'] = range(1001, 1001 + len(df))
creditscore_df['income'] = df['Income']
creditscore_df['payment_history'] = df['Payment_History']
creditscore_df['number_of_open_credit_cards'] = df['Number_of_Open_Credit_Cards']
creditscore_df['credit_score'] = df['Credit_Score']
creditscore_df['total_debt']= df['Total_Debt']

# Save to CSV
creditscore_df.to_csv(output_file2, index=False)

# Save to SAS7BDAT
#pyreadstat.write_sas7bdat(customers_df, "transformed_customers.sas7bdat")

print("Files saved: transformed_customers.csv and transformed_customers.sas7bdat")
