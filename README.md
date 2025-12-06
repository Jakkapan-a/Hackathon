# ระบบแปลงเอกสาร ป.ป.ช. (NACC Asset Declaration Parser)

ระบบแปลงเอกสารบัญชีแสดงรายการทรัพย์สินและหนี้สินของ ป.ป.ช. จาก PDF เป็นข้อมูล CSV

## สารบัญ

- [การติดตั้ง](#การติดตั้ง)
  - [ดาวน์โหลดโปรเจกต์](#ดาวน์โหลดโปรเจกต์)
  - [ติดตั้งไลบรารี](#ติดตั้งไลบรารี)
  - [ตั้งค่าระบบ](#ตั้งค่าระบบ)
- [โครงสร้างโฟลเดอร์](#โครงสร้างโฟลเดอร์)
- [การวางไฟล์](#การวางไฟล์)
- [การใช้งาน](#การใช้งาน)
- [ขั้นตอนการทำงาน](#ขั้นตอนการทำงาน)
- [ไฟล์ผลลัพธ์](#ไฟล์ผลลัพธ์)
- [การแก้ไขปัญหา](#การแก้ไขปัญหา)

---

## การติดตั้ง

### ดาวน์โหลดโปรเจกต์

**วิธีที่ 1: ใช้ Git Clone**
```bash
# เปิด Command Prompt หรือ Terminal
# ไปยังโฟลเดอร์ที่ต้องการเก็บโปรเจกต์
cd D:\Projects

# Clone โปรเจกต์จาก GitHub
git clone <repository-url>

# เข้าไปในโฟลเดอร์โปรเจกต์
cd Hackathon2
```

**วิธีที่ 2: ดาวน์โหลดไฟล์ ZIP**
1. ไปที่หน้า GitHub ของโปรเจกต์
2. กดปุ่ม "Code" > "Download ZIP"
3. แตกไฟล์ ZIP ไปยังโฟลเดอร์ที่ต้องการ
4. เปิด Command Prompt แล้วเข้าไปในโฟลเดอร์

### ติดตั้งไลบรารี

#### ขั้นตอนที่ 1: สร้าง Virtual Environment (แนะนำ)

**สำหรับ Windows:**
```bash
# สร้าง virtual environment
python -m venv venv

# เปิดใช้งาน virtual environment
venv\Scripts\activate
```

**สำหรับ Linux/Mac:**
```bash
# สร้าง virtual environment
python3 -m venv venv

# เปิดใช้งาน virtual environment
source venv/bin/activate
```

#### ขั้นตอนที่ 2: ติดตั้ง Python Packages

```bash
pip install -r requirements.txt
```

#### ขั้นตอนที่ 3: ติดตั้ง Poppler (สำหรับแปลง PDF เป็นรูปภาพ)

**สำหรับ Windows:**
1. ดาวน์โหลด Poppler จาก https://github.com/osber/poppler/releases
2. แตกไฟล์ไปที่ `C:\tools\poppler-24.08.0\`
3. เพิ่ม `C:\tools\poppler-24.08.0\Library\bin` ใน PATH:
   - คลิกขวาที่ "This PC" > Properties > Advanced system settings
   - กด "Environment Variables"
   - เลือก "Path" > Edit > New
   - เพิ่ม `C:\tools\poppler-24.08.0\Library\bin`
   - กด OK ทั้งหมด

**สำหรับ Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

**สำหรับ Mac:**
```bash
brew install poppler
```

### ตั้งค่าระบบ

#### ขั้นตอนที่ 1: สร้างไฟล์ตั้งค่า

**สำหรับ Windows:**
```bash
copy .env.example .env
```

**สำหรับ Linux/Mac:**
```bash
cp .env.example .env
```

#### ขั้นตอนที่ 2: แก้ไขไฟล์ `.env`

เปิดไฟล์ `.env` ด้วย text editor แล้วแก้ไขค่าต่างๆ:

```env
# ================ การตั้งค่า OCR ================
# เลือกวิธี OCR: 'ollama' (รันในเครื่อง) หรือ 'api' (ใช้ Typhoon API)
OCR_METHOD=api

# ================ การตั้งค่า Path ================
# โฟลเดอร์ที่มีไฟล์ input (CSV และ PDF)
INPUT_BASE_DIR="./training/train input"

# ชื่อไฟล์ CSV input
INPUT_CSV_DOC_INFO="Train_doc_info.csv"
INPUT_CSV_NACC_DETAIL="Train_nacc_detail.csv"
INPUT_CSV_SUBMITTER="Train_submitter_info.csv"
OUTPUT_PREFIX="Train"

# โฟลเดอร์ที่เก็บไฟล์ PDF
PDF_FOLDER="Train_pdf/pdf"

# โฟลเดอร์สำหรับเก็บผลลัพธ์
OUTPUT_DIR="./training/test_output"

# ================ การตั้งค่า Ollama (OCR ในเครื่อง) ================
OLLAMA_BASE_URL=http://localhost:7869/v1
OLLAMA_MODEL=scb10x/typhoon-ocr1.5-3b:latest

# ================ การตั้งค่า Typhoon API ================
# ใส่ API Key ที่ได้รับจาก Typhoon
TYPHOON_API_KEY=ใส่_api_key_ของคุณ_ที่นี่
TYPHOON_MODEL=typhoon-ocr-preview

# ================ การตั้งค่า OpenAI API (LLM Parser) ================
# ใส่ API Key ที่ได้รับจาก OpenAI
OPENAI_API_KEY=ใส่_openai_api_key_ของคุณ_ที่นี่
LLM_MODEL=gpt-4.1-mini

# ================ การข้ามขั้นตอน (สำหรับทดสอบ) ================
# ตั้งเป็น "true" เพื่อข้ามขั้นตอนนั้นๆ
SKIP_PHASE_1=false
SKIP_PHASE_2=false
SKIP_PHASE_3=false
SKIP_PHASE_4=false
SKIP_PHASE_5=false
```

---

## โครงสร้างโฟลเดอร์

```
Hackathon2/
│
├── .env                          # ไฟล์ตั้งค่า (สร้างจาก .env.example)
├── .env.example                  # ตัวอย่างไฟล์ตั้งค่า
├── requirements.txt              # รายการ Python packages ที่ต้องติดตั้ง
├── README.md                     # คู่มือการใช้งาน (ไฟล์นี้)
│
├── src/                          # โค้ดโปรแกรม
│   ├── pdf_to_image.py           # แปลง PDF เป็นรูปภาพ
│   ├── extract_text_from_image.py        # OCR ด้วย Typhoon API
│   ├── extract_text_from_image_ollama.py # OCR ด้วย Ollama (รันในเครื่อง)
│   ├── llm_parser.py             # แยกข้อมูลด้วย LLM (GPT-4.1-mini)
│   ├── json_to_csv.py            # แปลง JSON เป็น CSV
│   ├── load_test_doc.py          # โปรแกรมหลักสำหรับรันทั้งระบบ
│   ├── schema.py                 # โครงสร้างข้อมูล
│   └── enum_type.py              # ค่า Enum ต่างๆ
│
├── enum_type/                    # ไฟล์ Enum อ้างอิง
│   ├── asset_type.csv            # ประเภททรัพย์สิน
│   ├── relationship.csv          # ความสัมพันธ์
│   ├── statement_type.csv        # ประเภทบัญชี
│   └── ...
│
├── training/                     # ข้อมูลสำหรับประมวลผล
│   ├── train input/              # ไฟล์ input
│   │   ├── Train_doc_info.csv    # รายชื่อเอกสาร PDF
│   │   ├── Train_nacc_detail.csv # รายละเอียด NACC
│   │   ├── Train_submitter_info.csv # ข้อมูลผู้ยื่น
│   │   └── Train_pdf/
│   │       └── pdf/              # โฟลเดอร์เก็บไฟล์ PDF
│   │           ├── ชื่อ_นามสกุล_ตำแหน่ง.pdf
│   │           └── ...
│   │
│   └── test_output/              # ผลลัพธ์
│       ├── images/               # รูปภาพจาก PDF
│       ├── ocr_text/             # ข้อความที่ได้จาก OCR
│       ├── json/                 # ข้อมูล JSON
│       └── csv/                  # ไฟล์ CSV ผลลัพธ์
│
└── pdf others/                   # PDF เพิ่มเติม (ถ้ามี)
```

---

## การวางไฟล์

### ขั้นตอนที่ 1: สร้างโฟลเดอร์

**สำหรับ Windows:**
```bash
mkdir "training\train input\Train_pdf\pdf"
```

**สำหรับ Linux/Mac:**
```bash
mkdir -p "training/train input/Train_pdf/pdf"
```

### ขั้นตอนที่ 2: วางไฟล์ PDF

คัดลอกไฟล์ PDF ทั้งหมดไปยังโฟลเดอร์:
```
training/train input/Train_pdf/pdf/
├── ชวน_หลีกภัย_ส.ส._กรณีเข้ารับตำแหน่ง_15_ก.ย._2566.pdf
├── พิธา_ลิ้มเจริญรัตน์_ส.ส._กรณีเข้ารับตำแหน่ง_15_ต.ค._2562.pdf
├── ทวี_สอดส่อง_ส.ส._กรณีเข้ารับตำแหน่ง_15_ต.ค._2562.pdf
└── ...
```

### ขั้นตอนที่ 3: สร้างไฟล์ Train_doc_info.csv

สร้างไฟล์ `Train_doc_info.csv` ในโฟลเดอร์ `training/train input/`:

```csv
doc_id,doc_location_url,type_id,nacc_id
1,ชวน_หลีกภัย_ส.ส._กรณีเข้ารับตำแหน่ง_15_ก.ย._2566.pdf,1,1001
2,พิธา_ลิ้มเจริญรัตน์_ส.ส._กรณีเข้ารับตำแหน่ง_15_ต.ค._2562.pdf,1,1002
3,ทวี_สอดส่อง_ส.ส._กรณีเข้ารับตำแหน่ง_15_ต.ค._2562.pdf,1,1003
```

**คำอธิบายคอลัมน์:**
- `doc_id` - รหัสเอกสาร (ตัวเลขไม่ซ้ำ)
- `doc_location_url` - ชื่อไฟล์ PDF (ต้องตรงกับชื่อไฟล์จริง)
- `type_id` - ประเภทเอกสาร (1 = เข้ารับตำแหน่ง, 2 = พ้นตำแหน่ง, ฯลฯ)
- `nacc_id` - รหัส NACC (ตัวเลขไม่ซ้ำ)

---

## การใช้งาน

### รันทั้งระบบ (แนะนำ)

```bash
# เปิดใช้งาน virtual environment ก่อน (ถ้ายังไม่ได้เปิด)
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# รันโปรแกรมหลัก
python src/load_test_doc.py
```

### รันแยกขั้นตอน

#### ขั้นตอนที่ 1: แปลง PDF เป็นรูปภาพ
```bash
python src/pdf_to_image.py
```

#### ขั้นตอนที่ 2: OCR (แปลงรูปภาพเป็นข้อความ)
```bash
# ใช้ Typhoon API
python src/extract_text_from_image.py

# หรือใช้ Ollama (รันในเครื่อง)
python src/extract_text_from_image_ollama.py
```

#### ขั้นตอนที่ 3: แยกข้อมูลด้วย LLM
```bash
python src/llm_parser.py
```

#### ขั้นตอนที่ 4: แปลง JSON เป็น CSV
```bash
python src/json_to_csv.py
```

---

## ขั้นตอนการทำงาน

```
┌──────────────────────────┐
│  1. อ่านรายชื่อเอกสาร     │ ← เริ่มจาก Train_doc_info.csv
│     (Train_doc_info)     │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  2. แปลง PDF เป็นรูปภาพ   │ ← ใช้ pdf2image / PyMuPDF
│     (PDF to Image)       │    ความละเอียด 200 DPI
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  3. OCR                  │ ← Typhoon OCR / Ollama
│     (รูปภาพ → ข้อความ)    │    อ่านภาษาไทย-อังกฤษ
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  4. LLM Parsing          │ ← GPT-4.1-mini
│     (ข้อความ → JSON)      │    แยกข้อมูลเป็นโครงสร้าง
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  5. สร้างไฟล์ CSV         │ ← สร้าง 13 ไฟล์
│     (JSON to CSV)        │
└──────────────────────────┘
```

---

## ไฟล์ผลลัพธ์

ระบบจะสร้างไฟล์ CSV ทั้งหมด 13 ไฟล์:

| ลำดับ | ชื่อไฟล์ | คำอธิบาย |
|-------|----------|----------|
| 1 | `submitter_info.csv` | ข้อมูลผู้ยื่นบัญชี |
| 2 | `submitter_old_name.csv` | ชื่อ-นามสกุลเดิมของผู้ยื่น |
| 3 | `submitter_position.csv` | ตำแหน่งของผู้ยื่น |
| 4 | `spouse_info.csv` | ข้อมูลคู่สมรส |
| 5 | `spouse_old_name.csv` | ชื่อ-นามสกุลเดิมของคู่สมรส |
| 6 | `spouse_position.csv` | ตำแหน่งของคู่สมรส |
| 7 | `relative_info.csv` | ข้อมูลบิดา มารดา บุตร |
| 8 | `statement.csv` | สรุปยอดทรัพย์สินและหนี้สิน |
| 9 | `statement_detail.csv` | รายละเอียดทรัพย์สินและหนี้สิน |
| 10 | `asset.csv` | รายการทรัพย์สินทั้งหมด |
| 11 | `asset_land_info.csv` | รายละเอียดที่ดิน |
| 12 | `asset_building_info.csv` | รายละเอียดสิ่งปลูกสร้าง |
| 13 | `asset_vehicle_info.csv` | รายละเอียดยานพาหนะ |

---

## ข้อกำหนดระบบ

- **Python**: เวอร์ชัน 3.10 ขึ้นไป
- **Encoding**: UTF-8-sig (รองรับภาษาไทย)
- **API Keys ที่ต้องมี**:
  - OpenAI API Key (สำหรับ LLM Parser)
  - Typhoon API Key (ถ้าใช้โหมด API สำหรับ OCR)

---

## การแก้ไขปัญหา

### ปัญหา: PDF ไม่สามารถแปลงได้

**สาเหตุ:** ไม่ได้ติดตั้ง Poppler หรือ path ไม่ถูกต้อง

**วิธีแก้:**
1. ตรวจสอบว่าติดตั้ง Poppler แล้ว
2. ตรวจสอบว่าเพิ่ม path ใน Environment Variables แล้ว
3. ลองรีสตาร์ท Command Prompt

### ปัญหา: OCR อ่านข้อความผิดพลาด

**สาเหตุ:** คุณภาพ PDF ต่ำ หรือความละเอียดไม่เพียงพอ

**วิธีแก้:**
1. ตรวจสอบคุณภาพไฟล์ PDF ต้นฉบับ
2. ลองเพิ่มค่า DPI จาก 200 เป็น 300 ในไฟล์ `pdf_to_image.py`

### ปัญหา: LLM Parser เกิด error

**สาเหตุ:** API Key ไม่ถูกต้อง หรือเกิน rate limit

**วิธีแก้:**
1. ตรวจสอบว่า `OPENAI_API_KEY` ในไฟล์ `.env` ถูกต้อง
2. รอสักครู่แล้วลองใหม่ (กรณี rate limit)
3. ตรวจสอบยอดเงินคงเหลือใน OpenAI account

### ปัญหา: ไฟล์ CSV แสดงภาษาไทยไม่ถูกต้อง

**สาเหตุ:** เปิดไฟล์ด้วย encoding ที่ไม่ถูกต้อง

**วิธีแก้:**
1. เปิดไฟล์ด้วย Excel: Data > From Text/CSV > เลือก encoding เป็น UTF-8
2. หรือใช้ Notepad++ แล้วเลือก Encoding > UTF-8

---