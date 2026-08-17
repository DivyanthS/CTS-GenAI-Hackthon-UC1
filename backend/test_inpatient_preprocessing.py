from services.preprocessing.inpatient import preprocess_inpatient


INPUT_PATH = "data/inpatient_raw.csv"


df = preprocess_inpatient(INPUT_PATH)

print("=== INPATIENT PREPROCESSING RESULT ===")
print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nColumns:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nRemaining missing values:")
print(df.isna().sum().sum())

print("\nInpatient preprocessing test PASSED")