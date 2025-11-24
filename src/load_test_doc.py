from pathlib import Path
import csv
from typing import Dict, List
from tabulate import tabulate

def load_test_phase_csvs(
    base_dir: str | Path = Path("./test phase 1/test phase 1 input"),
    encoding: str = "utf-8-sig",
) -> Dict[str, List[dict]]:
    """
    อ่านชุดข้อมูล 3 ไฟล์แล้วคืนค่าเป็น dict:
      - doc_info: Test_doc_info.csv
      - nacc_detail: Test_nacc_detail.csv
      - submitter_info: Test_submitter_info.csv
    """
    base_path = Path(base_dir)

    csv_files = {
        "doc_info": base_path / "Test_doc_info.csv",
        "nacc_detail": base_path / "Test_nacc_detail.csv",
        "submitter_info": base_path / "Test_submitter_info.csv",
    }

    datasets: Dict[str, List[dict]] = {}
    for name, csv_path in csv_files.items():
        with csv_path.open(encoding=encoding, newline="") as fh:
            datasets[name] = list(csv.DictReader(fh))

    return datasets

if __name__ == "__main__":
    # 👤 submitter_info (ผู้ยื่น) 
    #         ↓
    # 📝 nacc_detail (การยื่นแต่ละครั้ง)
    #         ↓
    # 📄 doc_info (เอกสาร PDF)

    tables = load_test_phase_csvs()
    for name, rows in tables.items():
        print(f"\n{'='*60}")
        print(f"📋 {name}: {len(rows)} rows")
        print(f"{'='*60}")
        if rows:
            # แสดงข้อมูลเป็นตาราง
            headers = list(rows[0].keys())
            table_data = [[row.get(h, '') for h in headers] for row in rows]  # แสดงทั้งหมด
            print(tabulate(table_data, headers=headers, tablefmt="grid"))

