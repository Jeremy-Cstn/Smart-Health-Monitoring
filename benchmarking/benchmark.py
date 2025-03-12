import datetime
import os
import pandas as pd
import numpy as np

# Directory where sensor CSV files are stored
DATA_FOLDER = "./data"

# Output folder for anomaly logs
LOG_FOLDER = "./logs"
os.makedirs(LOG_FOLDER, exist_ok=True)

# List of sampling frequencies to test
SAMPLING_FREQUENCIES = [1, 2, 5, 10]
FIXED_LOWER_BOUND = 60
FIXED_UPPER_BOUND = 100
HARD_LOWER_BOUND = 40
HARD_UPPER_BOUND = 120
PERCENTILES_IQR_LENGTH = 1000
ROLLING_AVG_RANGE = 500
NUMBER_PATIENTS = 10000
MIN_NUMBER_OF_READINGS = 2000
SEPARATE_LOWER_AND_UPPER = False


### **1️⃣ Percentile-Based Anomaly Detection**
def percentile_based_anomaly_detection(df, sampling_frequency):
    nr_initial_readings = int(PERCENTILES_IQR_LENGTH / sampling_frequency)
    if len(df) < nr_initial_readings:
        return []

    lower_bound = df.iloc[:nr_initial_readings]["heart_rate"].quantile(0.01)
    upper_bound = df.iloc[:nr_initial_readings]["heart_rate"].quantile(0.99)
    return detect_anomalies(df.iloc[nr_initial_readings:], lower_bound, upper_bound)


### **2️⃣ IQR-Based Anomaly Detection**
def iqr_based_anomaly_detection(df, sampling_frequency):
    nr_initial_readings = int(PERCENTILES_IQR_LENGTH / sampling_frequency)
    if len(df) < nr_initial_readings:
        return []
    Q1 = df.iloc[:nr_initial_readings]["heart_rate"].quantile(0.25)
    Q3 = df.iloc[:nr_initial_readings]["heart_rate"].quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return detect_anomalies(df.iloc[nr_initial_readings:], lower_bound, upper_bound)


### **3️⃣ Rolling Average + Standard Deviation-Based Anomaly Detection**
def rolling_average_anomaly_detection(df, sampling_frequency, N=ROLLING_AVG_RANGE):
    rolling_mean = df["heart_rate"].rolling(N, min_periods=10).mean()
    rolling_std = df["heart_rate"].rolling(N, min_periods=10).std()

    lower_bounds = rolling_mean - 2 * rolling_std
    upper_bounds = rolling_mean + 2 * rolling_std
    return detect_anomalies(df.iloc[10:], lower_bounds, upper_bounds)


### **4️⃣ Fixed Threshold-Based Anomaly Detection**
def fixed_threshold_anomaly_detection(df, sampling_frequency):
    return detect_anomalies(df, FIXED_LOWER_BOUND, FIXED_UPPER_BOUND)


# Mapping of policy names to their functions
ANOMALY_POLICIES = {
    "Percentile": percentile_based_anomaly_detection,
    "IQR": iqr_based_anomaly_detection,
    "Rolling Average": rolling_average_anomaly_detection,
    "Fixed Threshold": fixed_threshold_anomaly_detection
}


### **🚀 Anomaly Detection Function**
def detect_anomalies(df, lower_bounds, upper_bounds):
    """Detects anomalies based on hard lower and upper bounds only, ignoring adaptive bounds."""
    anomalies = []

    for index, row in df.iterrows():
        timestamp = row["observation_offset"]
        value = row["heart_rate"]

        # Check if lower_bound/upper_bound are scalars or Series
        lower_bound = lower_bounds.iloc[index] if isinstance(lower_bounds, pd.Series) else lower_bounds
        upper_bound = upper_bounds.iloc[index] if isinstance(upper_bounds, pd.Series) else upper_bounds

        # Check if the value is within the adaptive bounds but outside the hard bounds
        if (np.isfinite(lower_bound) and np.isfinite(upper_bound)):
            if (value < lower_bound or value > upper_bound) or (value < HARD_LOWER_BOUND or value > HARD_UPPER_BOUND):
                anomalies.append([timestamp, "heart_rate", value])

    return anomalies


### **📌 Helper Functions**
def load_sensor_data(file_path):
    """Loads a CSV file into a pandas DataFrame."""
    return pd.read_csv(file_path)


def detect_anomalies_for_file(file_path, sampling_frequency):
    """Applies all anomaly detection policies on the data for a given sampling frequency."""
    df = load_sensor_data(file_path)
    df_sampled = df.iloc[::sampling_frequency, :].reset_index(drop=True)
    patient_id = os.path.basename(file_path).split(".")[0]
    file_anomalies = []
    len_analyzed_readings = len(df_sampled)

    for policy_name, policy_function in ANOMALY_POLICIES.items():
        anomalies = policy_function(df_sampled, sampling_frequency)

        if policy_name == "Percentile" or policy_name == "IQR":
            len_analyzed_readings = int(len(df_sampled) - PERCENTILES_IQR_LENGTH / sampling_frequency)


        for anomaly in anomalies:
            entry = {
                "Patient ID": patient_id,
                "Timestamp": anomaly[0],
                "Sensor Type": anomaly[1],
                "Anomaly Value": anomaly[2],
                "Policy": policy_name,
                "Sampling Frequency": f"Sampling_{sampling_frequency}",
                "Breach Type": anomaly[3] if SEPARATE_LOWER_AND_UPPER else "Both"
            }
            file_anomalies.append(entry)

    return file_anomalies, len_analyzed_readings


def create_configuration_summary():
    """Creates a DataFrame summarizing the current configuration parameters."""
    config_params = {
        "Parameter": [
            "FIXED_LOWER_BOUND", "FIXED_UPPER_BOUND", "HARD_LOWER_BOUND", "HARD_UPPER_BOUND",
            "PERCENTILES_IQR_LENGTH", "ROLLING_AVG_RANGE", "NUMBER_PATIENTS", "MIN_NUMBER_OF_READINGS",
            "SEPARATE_LOWER_AND_UPPER"
        ],
        "Value": [
            FIXED_LOWER_BOUND, FIXED_UPPER_BOUND, HARD_LOWER_BOUND, HARD_UPPER_BOUND,
            PERCENTILES_IQR_LENGTH, ROLLING_AVG_RANGE, NUMBER_PATIENTS, MIN_NUMBER_OF_READINGS, SEPARATE_LOWER_AND_UPPER
        ]
    }
    return pd.DataFrame(config_params)


def run_tests():
    """Runs anomaly detection tests on all CSV files with different sampling frequencies."""
    csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    all_anomalies = []
    total_readings = {}

    for sampling_frequency in SAMPLING_FREQUENCIES:
        print(f"\n🔎 Running tests with sampling frequency = {sampling_frequency}...\n")
        i = 0
        for file_name in csv_files:
            if i >= NUMBER_PATIENTS:
                break
            file_path = os.path.join(DATA_FOLDER, file_name)
            if pd.read_csv(file_path).shape[0] < MIN_NUMBER_OF_READINGS:
                continue
            file_anomalies, num_readings = detect_anomalies_for_file(file_path, sampling_frequency)
            all_anomalies.extend(file_anomalies)

            # Accumulate total readings per sampling frequency
            key = f"Sampling_{sampling_frequency}"
            total_readings[key] = total_readings.get(key, 0) + num_readings
            i = i + 1
        print(f'finished simulating {i} patients')

    # Create DataFrame from collected anomalies
    anomalies_df = pd.DataFrame(all_anomalies)

    # Create summary DataFrame with anomalies per 1000 readings
    if SEPARATE_LOWER_AND_UPPER:
        # Group by Policy, Sampling Frequency, and Breach Type
        summary_df = anomalies_df.groupby(["Policy", "Sampling Frequency", "Breach Type"]).size().reset_index(
            name="Count")
    else:
        # Group by Policy and Sampling Frequency only
        summary_df = anomalies_df.groupby(["Policy", "Sampling Frequency"]).size().reset_index(name="Count")

    # Calculate anomalies per 1000 readings
    summary_df["Anomalies per 1000 Readings"] = summary_df.apply(
        lambda row: (row["Count"] / total_readings[row["Sampling Frequency"]]) * 1000,
        axis=1
    )

    # Pivot the summary table to have algorithms as rows and sampling frequencies as columns
    if SEPARATE_LOWER_AND_UPPER:
        # Include Breach Type in the pivot
        pivot_summary = summary_df.pivot_table(
            index=["Policy", "Breach Type"],
            columns="Sampling Frequency",
            values="Anomalies per 1000 Readings",
            aggfunc="sum"
        ).reset_index()
    else:
        # Exclude Breach Type in the pivot
        pivot_summary = summary_df.pivot(
            index="Policy",
            columns="Sampling Frequency",
            values="Anomalies per 1000 Readings"
        ).reset_index()

    # Rename columns for clarity
    pivot_summary.columns.name = None
    pivot_summary = pivot_summary.rename(columns={
        "Policy": "Algorithm",
        **{f"Sampling_{freq}": f"Sampling {freq}" for freq in SAMPLING_FREQUENCIES}
    })

    # Ensure the columns are ordered as 1, 2, 5, 10
    column_order = ["Algorithm", "Breach Type"] if SEPARATE_LOWER_AND_UPPER else ["Algorithm"]
    column_order += [f"Sampling {freq}" for freq in SAMPLING_FREQUENCIES]
    pivot_summary = pivot_summary[column_order]

    # Create configuration summary
    config_summary = create_configuration_summary()

    # Save to Excel
    output_path = os.path.join(LOG_FOLDER, f"anomaly_results{datetime.datetime.now()}.xlsx")
    with pd.ExcelWriter(output_path) as writer:
        # anomalies_df.to_excel(writer, sheet_name="Anomaly Details", index=False)
        pivot_summary.to_excel(writer, sheet_name="Summary", index=False)
        config_summary.to_excel(writer, sheet_name="Configuration", index=False)

    print("\n✅ Anomaly detection tests completed!")
    print(f"📊 Results saved to: {output_path}")


if __name__ == "__main__":
    run_tests()
