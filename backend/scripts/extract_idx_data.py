import pandas as pd
import glob
import os

input_dir = r"c:\Users\Russel\industrial-benchmark\backend\data\idx_reports"
output_dir = r"c:\Users\Russel\industrial-benchmark\backend\data\processed"

os.makedirs(output_dir, exist_ok=True)
os.makedirs(r"c:\Users\Russel\industrial-benchmark\backend\scripts", exist_ok=True)

files = glob.glob(os.path.join(input_dir, "*.xlsx"))
print(f"Found {len(files)} files to process.")

# Variables to extract
vars_1000000 = [
    "Nama entitas", "Kode entitas", "Sektor", "Subsektor", "Industri", "Subindustri"
]

vars_1210000 = [
    "Aset", "Aset lancar", "Aset tidak lancar", 
    "Liabilitas", "Liabilitas jangka pendek", "Liabilitas jangka panjang", 
    "Ekuitas", "Kas dan setara kas", "Piutang usaha", "Persediaan"
]

vars_1321000 = [
    "Penjualan dan pendapatan usaha", "Beban pokok penjualan dan pendapatan",
    "Jumlah laba kotor", "Laba (rugi) sebelum pajak penghasilan",
    "Laba (rugi) tahun berjalan"
]

vars_1410000 = [
    "Posisi ekuitas", "Laba (rugi)", "Total komprehensif"
]

def extract_sheet_data(filepath, sheet_name, variables, is_1000000=False, is_1410000=False):
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
        extracted = {}
        
        if is_1410000:
            # For 1410000, find the "Ekuitas" column index first
            ekuitas_col = None
            for row_idx in range(min(15, len(df))):
                for col_idx in range(len(df.columns)):
                    val = str(df.iloc[row_idx, col_idx]).strip()
                    if val.lower() == 'ekuitas':
                        ekuitas_col = col_idx
                        break
                if ekuitas_col is not None:
                    break
            
            if ekuitas_col is None:
                # fallback, just take column len-2 (often English is len-1)
                ekuitas_col = len(df.columns) - 2

            for var in variables:
                val = None
                # First try exact match
                for row_idx in range(len(df)):
                    cell_val = str(df.iloc[row_idx, 0]).strip()
                    if cell_val.lower() == var.lower():
                        val = df.iloc[row_idx, ekuitas_col]
                        break
                # Fallback to startswith
                if val is None:
                    for row_idx in range(len(df)):
                        cell_val = str(df.iloc[row_idx, 0]).strip()
                        if cell_val.lower().startswith(var.lower()):
                            val = df.iloc[row_idx, ekuitas_col]
                            break
                extracted[var] = val
                
        else:
            for var in variables:
                val = None
                # First try exact match
                for row_idx in range(len(df)):
                    cell_val = str(df.iloc[row_idx, 0]).strip()
                    if cell_val.lower() == var.lower():
                        val = df.iloc[row_idx, 1] # Usually column 1 has the current year value
                        break
                # Fallback to startswith
                if val is None:
                    for row_idx in range(len(df)):
                        cell_val = str(df.iloc[row_idx, 0]).strip()
                        if cell_val.lower().startswith(var.lower()):
                            val = df.iloc[row_idx, 1]
                            break
                extracted[var] = val
                
        return extracted
    except Exception as e:
        # Silently return Nones if sheet doesn't exist or other error
        return {var: None for var in variables}

all_1000000 = []
all_1210000 = []
all_1321000 = []
all_1410000 = []

for i, filepath in enumerate(files):
    if i % 50 == 0:
        print(f"Processing file {i+1}/{len(files)}...")
        
    filename = os.path.basename(filepath)
    ticker = filename.replace('.xlsx', '')
    
    # 1000000
    data_1000000 = extract_sheet_data(filepath, '1000000', vars_1000000, is_1000000=True)
    data_1000000['File'] = filename
    data_1000000['Ticker'] = ticker
    all_1000000.append(data_1000000)
    
    # 1210000
    data_1210000 = extract_sheet_data(filepath, '1210000', vars_1210000)
    data_1210000['File'] = filename
    data_1210000['Ticker'] = ticker
    all_1210000.append(data_1210000)
    
    # 1321000
    data_1321000 = extract_sheet_data(filepath, '1321000', vars_1321000)
    data_1321000['File'] = filename
    data_1321000['Ticker'] = ticker
    all_1321000.append(data_1321000)
    
    # 1410000
    data_1410000 = extract_sheet_data(filepath, '1410000', vars_1410000, is_1410000=True)
    data_1410000['File'] = filename
    data_1410000['Ticker'] = ticker
    all_1410000.append(data_1410000)

df_1000000 = pd.DataFrame(all_1000000)
df_1210000 = pd.DataFrame(all_1210000)
df_1321000 = pd.DataFrame(all_1321000)
df_1410000 = pd.DataFrame(all_1410000)

# Reorder columns to have Ticker and File first
def reorder_cols(df):
    cols = df.columns.tolist()
    cols = ['Ticker', 'File'] + [c for c in cols if c not in ['Ticker', 'File']]
    return df[cols]

df_1000000 = reorder_cols(df_1000000)
df_1210000 = reorder_cols(df_1210000)
df_1321000 = reorder_cols(df_1321000)
df_1410000 = reorder_cols(df_1410000)

df_1000000.to_csv(os.path.join(output_dir, 'benchmark_1000000.csv'), index=False)
df_1210000.to_csv(os.path.join(output_dir, 'benchmark_1210000.csv'), index=False)
df_1321000.to_csv(os.path.join(output_dir, 'benchmark_1321000.csv'), index=False)
df_1410000.to_csv(os.path.join(output_dir, 'benchmark_1410000.csv'), index=False)

print(f"Extraction completed successfully! Check the output directory: {output_dir}")
