import csv
from pathlib import Path

def convert_mot_to_csv(mot_path: str, csv_path: str = None):
    mot_file = Path(mot_path)
    if not mot_file.exists():
        raise FileNotFoundError(f"{mot_file} not found")

    if csv_path is None:
        csv_path = mot_file.with_suffix(".csv")

    with mot_file.open("r") as f:
        lines = f.readlines()

    # Find the index of 'endheader'
    for i, line in enumerate(lines):
        if line.strip().lower() == 'endheader':
            header_end_index = i
            break
    else:
        raise ValueError("Missing 'endheader' in .mot file")

    # Column headers are immediately after 'endheader'
    column_names = lines[header_end_index + 1].strip().split('\t')
    data_lines = lines[header_end_index + 2:]

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(column_names)
        for line in data_lines:
            if line.strip():
                row = line.strip().split('\t')
                writer.writerow(row)

    print(f"✅ Converted: {mot_path} → {csv_path}")
    return csv_path



mot_files_dir = Path("angles_data/mot_files")
csv_files_dir = Path("angles_data/csv_files")

def convert_all_mot_files():

    for mot_file in mot_files_dir.glob("*.mot"):
        csv_file = csv_files_dir / (mot_file.stem + ".csv")
        convert_mot_to_csv(mot_file, csv_file)


if __name__ == "__main__":
    convert_all_mot_files()
