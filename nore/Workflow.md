# 🚀 Workflow การทำ Hackathon: Digitize NACC Asset Declaration

## 📋 ภาพรวม Workflow

```
┌──────────────────────┐
│  1. Test_doc_info    │ ← จุดเริ่มต้น
│  (รายชื่อ PDF)       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  2. อ่านไฟล์ PDF     │
│  จาก path/URL        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  3. PDF → Image      │
│  แปลงทุกหน้าเป็นรูป  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  4. OCR              │ ← Tesseract/PyTesseract
│  Image → Text        │   ดึงข้อความภาษาไทย
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  5. LLM Parsing      │ ← Ollama
│  Text → Structured   │   แยกหมวดหมู่ + Map Enum
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  6. Generate CSV     │ ← สร้าง 13 ไฟล์
│  13 Output Files     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  7. Validation       │ ← รัน validation_query.sql
│  Run SQL → Summary   │   สร้าง summary.csv
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  8. Submit           │ ← ส่ง Kaggle
│  Upload to Kaggle    │
└──────────────────────┘
```

---

## 📝 รายละเอียดแต่ละขั้นตอน

### 🔵 Step 1: เริ่มจาก Test_doc_info.csv

```python
import pandas as pd

# อ่านรายชื่อ PDF ทั้งหมด
doc_info = pd.read_csv("Test_doc_info.csv", encoding="utf-8-sig")

# Structure:
# ┌────────┬──────────────────────────────────┬─────────┬─────────┐
# │ doc_id │ doc_location_url                 │ type_id │ nacc_id │
# ├────────┼──────────────────────────────────┼─────────┼─────────┤
# │ 2098   │ จุติ_ไกรฤกษ์_ส.ส._กรณี....pdf   │    1    │  1970   │
# └────────┴──────────────────────────────────┴─────────┴─────────┘

# ได้ 9 ไฟล์ PDF ที่ต้องประมวลผล
```

**Output**: รายชื่อ PDF ทั้งหมด พร้อม nacc_id สำหรับ mapping

---

### 🔵 Step 2: อ่านไฟล์ PDF

```python
from pathlib import Path

for idx, row in doc_info.iterrows():
    pdf_filename = row['doc_location_url']
    nacc_id = row['nacc_id']
    
    # Path ของ PDF (ปรับตามโครงสร้างจริง)
    pdf_path = Path(f"./Test_pdf/{pdf_filename}")
    
    print(f"Processing: {pdf_filename}")
    print(f"  nacc_id: {nacc_id}")
```

**ที่ตั้งไฟล์**: ตามที่ Kaggle จัดให้ (อาจเป็น ZIP ต้อง extract ก่อน)

---

### 🔵 Step 3: PDF → Image

```python
import fitz  # PyMuPDF
from PIL import Image

def pdf_to_images(pdf_path):
    """แปลง PDF ทุกหน้าเป็น images"""
    
    pdf_document = fitz.open(pdf_path)
    images = []
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        
        # แปลงเป็น image (300 DPI สำหรับ OCR ที่ดี)
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        
        # แปลงเป็น PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    
    pdf_document.close()
    return images

# ใช้งาน
images = pdf_to_images(pdf_path)
print(f"  จำนวนหน้า: {len(images)} หน้า")
```

**Output**: List ของ images แต่ละหน้า

---

### 🔵 Step 4: OCR (Image → Text)

```python
import pytesseract
from PIL import Image

def ocr_image(image, lang='tha+eng'):
    """
    ทำ OCR บน image
    lang='tha+eng' = รองรับทั้งภาษาไทยและอังกฤษ
    """
    
    # Config สำหรับ OCR
    custom_config = r'--oem 3 --psm 6'
    
    # ดึง text ออกมา
    text = pytesseract.image_to_string(
        image, 
        lang=lang, 
        config=custom_config
    )
    
    return text.strip()

# ใช้งาน
all_text = []
for page_num, img in enumerate(images, 1):
    text = ocr_image(img)
    all_text.append({
        'page': page_num,
        'text': text
    })
    print(f"  Page {page_num}: {len(text)} characters")

# รวม text ทั้งหมด
full_text = "\n\n".join([page['text'] for page in all_text])
```

**Output**: Text ภาษาไทยจากทุกหน้า PDF

---

### 🔵 Step 5: LLM Parsing (Text → Structured Data)

```python
import requests
import json

def parse_with_llm(ocr_text, nacc_id, section="personal_info"):
    """
    ส่ง OCR text ไปให้ LLM parse
    """
    
    # อ่าน enum types สำหรับ context
    enums = load_enum_context()  # ฟังก์ชันโหลด enum ทั้งหมด
    
    # สร้าง prompt
    prompt = f"""
คุณเป็น AI ที่เชี่ยวชาญในการแปลงเอกสารบัญชีทรัพย์สินของ ป.ป.ช. เป็นข้อมูลที่มีโครงสร้าง

NACC_ID: {nacc_id}

ข้อความจาก OCR:
{ocr_text}

กรุณาแยกข้อมูลส่วน "{section}" ออกมาเป็น JSON โดย:
1. ใช้ enum ID ที่ถูกต้องจากข้อมูลนี้:
{json.dumps(enums[section], ensure_ascii=False, indent=2)}

2. ห้ามเดา enum ID - ถ้าไม่แน่ใจให้ใส่ null
3. จัดรูปแบบวันที่เป็น YYYY-MM-DD

ตอบกลับเป็น JSON เท่านั้น ไม่ต้องมีคำอธิบาย
"""
    
    # เรียก Ollama API
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "typhoon",
            "prompt": prompt,
            "temperature": 0.1,
            "max_tokens": 4000,
            "stream": False
        }
    )
    
    result = response.json()
    
    # Clean up และ parse JSON
    json_text = result['response'].strip()
    json_text = json_text.replace("```json", "").replace("```", "").strip()
    
    parsed_data = json.loads(json_text)
    
    return parsed_data

# ใช้งาน - parse แต่ละ section
sections = [
    "personal_info",      # ข้อมูลส่วนตัว
    "spouse_info",        # ข้อมูลคู่สมรส
    "relatives",          # ข้อมูลญาติ
    "positions",          # ตำแหน่ง
    "income_statement",   # รายได้
    "expense_statement",  # รายจ่าย
    "tax_statement",      # ภาษี
    "assets_land",        # ที่ดิน
    "assets_building",    # สิ่งปลูกสร้าง
    "assets_vehicle",     # ยานพาหนะ
    "assets_other"        # ทรัพย์สินอื่น
]

parsed_results = {}
for section in sections:
    parsed_results[section] = parse_with_llm(
        ocr_text=full_text,
        nacc_id=nacc_id,
        section=section
    )
```

**Output**: ข้อมูลที่มีโครงสร้างแล้ว พร้อม enum ID ที่ถูกต้อง

---

### 🔵 Step 6: Generate CSV (13 ไฟล์)

```python
def generate_csv_files(parsed_results, nacc_id):
    """
    สร้าง CSV 13 ไฟล์จากข้อมูลที่ parse แล้ว
    """
    
    output_dir = Path(f"output_{nacc_id}")
    output_dir.mkdir(exist_ok=True)
    
    # 1. submitter_old_name.csv
    if parsed_results['personal_info'].get('old_names'):
        df_old_name = pd.DataFrame(parsed_results['personal_info']['old_names'])
        df_old_name.to_csv(
            output_dir / "submitter_old_name.csv",
            index=False,
            encoding="utf-8-sig"
        )
    
    # 2. submitter_position.csv
    df_position = pd.DataFrame(parsed_results['positions'])
    df_position.to_csv(
        output_dir / "submitter_position.csv",
        index=False,
        encoding="utf-8-sig"
    )
    
    # 3. spouse_info.csv
    if parsed_results['spouse_info']:
        df_spouse = pd.DataFrame([parsed_results['spouse_info']])
        df_spouse.to_csv(
            output_dir / "spouse_info.csv",
            index=False,
            encoding="utf-8-sig"
        )
    
    # ... สร้างต่อไปจนครบ 13 ไฟล์
    
    # 9. asset.csv (รวมทรัพย์สินทั้งหมด)
    all_assets = []
    all_assets.extend(parsed_results['assets_land'])
    all_assets.extend(parsed_results['assets_building'])
    all_assets.extend(parsed_results['assets_vehicle'])
    all_assets.extend(parsed_results['assets_other'])
    
    df_assets = pd.DataFrame(all_assets)
    df_assets.to_csv(
        output_dir / "asset.csv",
        index=False,
        encoding="utf-8-sig"
    )
    
    print(f"✅ สร้าง CSV 13 ไฟล์เสร็จแล้ว ใน {output_dir}/")

# ใช้งาน
generate_csv_files(parsed_results, nacc_id)
```

**Output**: 13 ไฟล์ CSV ในโฟลเดอร์ `output_{nacc_id}/`

### รายชื่อ 13 ไฟล์:
1. ✅ submitter_old_name.csv
2. ✅ submitter_position.csv
3. ✅ spouse_info.csv
4. ✅ spouse_old_name.csv
5. ✅ spouse_position.csv
6. ✅ relative_info.csv
7. ✅ statement.csv
8. ✅ statement_detail.csv
9. ✅ asset.csv
10. ✅ asset_building_info.csv
11. ✅ asset_land_info.csv
12. ✅ asset_vehicle_info.csv
13. ✅ asset_other_asset_info.csv

---

### 🔵 Step 7: Validation (Run SQL)

```python
import sqlite3

def validate_and_create_summary(output_dir):
    """
    รัน validation_query.sql เพื่อสร้าง summary.csv
    """
    
    # สร้าง in-memory SQLite database
    conn = sqlite3.connect(':memory:')
    
    # โหลด CSV ทั้ง 13 ไฟล์เข้า SQLite
    csv_files = {
        'submitter_old_name': 'submitter_old_name.csv',
        'submitter_position': 'submitter_position.csv',
        'spouse_info': 'spouse_info.csv',
        'spouse_old_name': 'spouse_old_name.csv',
        'spouse_position': 'spouse_position.csv',
        'relative_info': 'relative_info.csv',
        'statement': 'statement.csv',
        'statement_detail': 'statement_detail.csv',
        'asset': 'asset.csv',
        'asset_building_info': 'asset_building_info.csv',
        'asset_land_info': 'asset_land_info.csv',
        'asset_vehicle_info': 'asset_vehicle_info.csv',
        'asset_other_asset_info': 'asset_other_asset_info.csv'
    }
    
    for table_name, csv_file in csv_files.items():
        csv_path = output_dir / csv_file
        if csv_path.exists():
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    # อ่าน validation_query.sql
    with open('validation_query.sql', 'r', encoding='utf-8') as f:
        sql_query = f.read()
    
    # รัน query
    df_summary = pd.read_sql_query(sql_query, conn)
    
    # บันทึก summary.csv
    df_summary.to_csv(
        output_dir / "summary.csv",
        index=False,
        encoding="utf-8-sig"
    )
    
    conn.close()
    
    print(f"✅ สร้าง summary.csv เสร็จแล้ว")
    return df_summary

# ใช้งาน
summary = validate_and_create_summary(output_dir)
```

**Output**: summary.csv สำหรับ submit

---

### 🔵 Step 8: Submit to Kaggle

```python
def prepare_submission():
    """
    รวม summary จากทุก nacc_id เป็นไฟล์เดียว
    """
    
    all_summaries = []
    
    # อ่าน summary จากทุก output directory
    for output_dir in Path('.').glob('output_*'):
        summary_file = output_dir / 'summary.csv'
        if summary_file.exists():
            df = pd.read_csv(summary_file, encoding='utf-8-sig')
            all_summaries.append(df)
    
    # รวมทั้งหมด
    final_summary = pd.concat(all_summaries, ignore_index=True)
    
    # บันทึก
    final_summary.to_csv(
        'submission_summary.csv',
        index=False,
        encoding='utf-8-sig'
    )
    
    print(f"✅ สร้าง submission_summary.csv เสร็จแล้ว ({len(final_summary)} rows)")

# ใช้งาน
prepare_submission()
```

**Output**: `submission_summary.csv` พร้อม submit ใน Kaggle

---

## 🎯 โครงสร้างโค้ดแนะนำ

```
project/
├── main.py                      # Script หลัก
├── config.py                    # Configuration
├── modules/
│   ├── pdf_processor.py         # PDF → Image
│   ├── ocr_engine.py            # OCR → Text
│   ├── llm_parser.py            # LLM Parsing
│   ├── csv_generator.py         # Generate CSV
│   └── validator.py             # Validation
├── data/
│   ├── Test_doc_info.csv
│   ├── Test_nacc_detail.csv
│   ├── Test_submitter_info.csv
│   ├── Test_pdf/               # PDF files
│   └── enum_types/             # Enum CSV files
├── output_1970/                # Output สำหรับ nacc_id=1970
│   ├── submitter_old_name.csv
│   ├── ...
│   └── summary.csv
├── output_2448/                # Output สำหรับ nacc_id=2448
└── submission_summary.csv      # ไฟล์สำหรับ submit
```

---

## ⚡ Quick Start

```python
# Main Pipeline
def process_all_documents():
    """
    ประมวลผล PDF ทั้งหมด
    """
    
    # 1. โหลดข้อมูล
    doc_info = pd.read_csv("Test_doc_info.csv", encoding="utf-8-sig")
    nacc_detail = pd.read_csv("Test_nacc_detail.csv", encoding="utf-8-sig")
    submitter_info = pd.read_csv("Test_submitter_info.csv", encoding="utf-8-sig")
    
    # 2. วนลูปทุก PDF
    for idx, doc_row in doc_info.iterrows():
        pdf_filename = doc_row['doc_location_url']
        nacc_id = doc_row['nacc_id']
        
        print(f"\n{'='*80}")
        print(f"Processing {idx+1}/{len(doc_info)}: {pdf_filename}")
        print(f"{'='*80}")
        
        # 3. PDF → Images
        images = pdf_to_images(f"./Test_pdf/{pdf_filename}")
        
        # 4. OCR
        full_text = ""
        for img in images:
            text = ocr_image(img)
            full_text += text + "\n\n"
        
        # 5. LLM Parsing
        parsed_results = parse_all_sections(full_text, nacc_id)
        
        # 6. Generate CSV
        generate_csv_files(parsed_results, nacc_id)
        
        # 7. Validate
        validate_and_create_summary(Path(f"output_{nacc_id}"))
    
    # 8. Create final submission
    prepare_submission()
    
    print("\n✅ ประมวลผลเสร็จสิ้น!")

# รัน!
if __name__ == "__main__":
    process_all_documents()
```

---

## ✅ สรุป

**ใช่แล้วครับ! Flow คือ:**

1. ✅ เริ่มจาก `Test_doc_info.csv` → ได้รายชื่อ PDF
2. ✅ อ่าน PDF → แปลงเป็น Images
3. ✅ OCR (Tesseract) → ได้ Text
4. ✅ LLM Parsing → ได้ Structured Data พร้อม Enum ID
5. ✅ Generate CSV → ได้ 13 ไฟล์
6. ✅ Run validation_query.sql → ได้ summary.csv
7. ✅ Submit to Kaggle

**คีย์สำคัญ:**
- 📌 ใช้ `nacc_id` เป็นตัวเชื่อม
- 📌 ใช้ enum ID ที่ถูกต้อง (ห้ามเดา!)
- 📌 UTF-8-sig encoding สำหรับภาษาไทย
- 📌 Temperature=0.1 สำหรับ LLM ให้ consistent