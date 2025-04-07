import pandas as pd

# Manually typed user data
data = {
    "Account Number": ['1234567890', '9876543210', '4567891230', '7894561230', '3216549870',
                       '1597534680', '8523697410', '7539518520', '4561237890', '9517538520'],
    "User Name": ['John Doe', 'Alice Smith', 'Robert Brown', 'Emily Davis', 'Michael Johnson',
                  'Sophia Wilson', 'David Lee', 'Olivia Martinez', 'James Taylor', 'Emma White'],
    "Sort Code": [469812, 235769, 784523, 125698, 896745, 523698, 698741, 357159, 789654, 412365],
    "Bank Balance": [2500.75, 3200.50, 1800.00, 4100.30, 520.60, 6789.99, 1450.25, 380.00, 9200.45, 1300.75],
    "Last 3 Transactions": [
        "[100.50, -50.75, 200.00]",
        "[250.00, -80.25, 35.60]",
        "[500.00, -20.00, -75.30]",
        "[900.00, -40.50, -30.75]",
        "[150.25, -60.00, -20.50]",
        "[320.40, -50.60, -200.00]",
        "[480.00, -150.25, -35.00]",
        "[650.75, -75.00, -25.50]",
        "[720.50, -80.30, -100.00]",
        "[830.00, -120.00, -90.50]"
    ]
}

# Convert to DataFrame
df = pd.DataFrame(data)

# Save to Excel
df.to_excel("bank_data.xlsx", index=False)

print("Excel file created successfully!")
