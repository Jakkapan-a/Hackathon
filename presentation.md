# 🎯 NACC Asset Declaration Parser
## ระบบประมวลผลบัญชีทรัพย์สินอัตโนมัติ

---

# Slide 1: ปัญหาที่ต้องแก้ไข (Problem Statement)

## 📋 ความท้าทายในปัจจุบัน

| ปัญหา | ผลกระทบ |
|-------|---------|
| เอกสารบัญชีทรัพย์สินเป็น PDF | ไม่สามารถค้นหาหรือวิเคราะห์ข้อมูลได้ |
| การกรอกข้อมูลด้วยมือ | เกิดข้อผิดพลาด ใช้เวลานาน |
| ข้อมูลไม่เป็นมาตรฐาน | ยากต่อการเปรียบเทียบและตรวจสอบ |
| ปริมาณเอกสารมหาศาล | ขาดแคลนบุคลากรในการประมวลผล |

**เป้าหมาย**: แปลงเอกสาร PDF → ข้อมูลที่มีโครงสร้าง (CSV/Database) อัตโนมัติ

---

# Slide 2: Solution Overview

## 🚀 NACC Asset Declaration Parser

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    PDF      │ →  │   Images    │ →  │    Text     │ →  │    JSON     │ →  │  CSV / DB   │
│  Documents  │    │  (PNG/JPG)  │    │   (OCR)     │    │ (Structured)│    │  (Output)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     Phase 1            Phase 2           Phase 3            Phase 4           Phase 5
   PDF to Image     Image to Text     LLM Parsing       JSON to CSV        Summary
```

**5-Phase Pipeline Architecture**

---

# Slide 3: เทคโนโลยีที่ใช้ (Technology Stack)

## 🔧 Core Technologies

### OCR Layer
- **Typhoon OCR API** - Cloud-based Thai OCR
- **Ollama (Local)** - typhoon-ocr1.5-3b model

### AI/LLM Layer
- **GPT-4.1-mini** - Intelligent data extraction
- Custom prompts optimized for Thai documents

### Data Processing
- **Python 3.10+** - Main programming language
- **pdf2image / PyMuPDF** - PDF processing
- **pandas** - Data manipulation
- **SQLite** - Database storage

---

# Slide 4: Phase 1 - PDF to Image

## 📄 → 🖼️ PDF Conversion

```python
# แปลง PDF เป็นภาพ PNG ความละเอียด 200 DPI
pdf_to_images(pdf_path, output_folder)
```

### Features:
- ✅ รองรับ PDF หลายหน้า
- ✅ ใช้ **pdf2image** เป็นหลัก
- ✅ Fallback to **PyMuPDF** ถ้าล้มเหลว
- ✅ Output: PNG 200 DPI per page

### Output Structure:
```
document_output/
  └── images/
      ├── page_0001.png
      ├── page_0002.png
      └── page_0003.png
```

---

# Slide 5: Phase 2 - OCR Processing

## 🖼️ → 📝 Image to Text

### Dual OCR Options:

| Mode | Provider | Use Case |
|------|----------|----------|
| **API** | OpenTyphoon | Production, High accuracy |
| **Local** | Ollama | Development, No internet |

### Key Features:
- ✅ Thai language optimized
- ✅ Automatic retry on rate limit
- ✅ Exponential backoff (1s → 2s → 4s → 8s)
- ✅ Skip already processed files

```python
# Output: text file per image
page_0001.png → page_0001.txt
```

---

# Slide 6: Phase 3 - LLM Parsing (Core Innovation)

## 📝 → 📊 Text to Structured JSON

### Intelligence Features:

**1. Thai Character Error Correction**
```
ภ → ก, พ → ภ, ม → น (OCR confusion fixes)
```

**2. Name/Title Parsing**
```
"นายสมชาย ใจดี" → title: "นาย", first: "สมชาย", last: "ใจดี"
```

**3. Financial Value Parsing**
```
"1,234,567.89" → 1234567.89 (float)
```

**4. Date Parsing**
```
"พ.ศ. 2567" → Buddhist calendar handling
```

### Processing Modes:
- **Combined**: Parse all pages at once (fast)
- **Page-by-Page**: Parse individually then merge (accurate)

---

# Slide 7: Data Schema - ข้อมูลที่ Extract ได้

## 📋 Comprehensive Data Extraction

### ผู้ยื่นแสดง (Submitter)
- ข้อมูลส่วนตัว (ชื่อ, อายุ, สถานะสมรส)
- ตำแหน่งปัจจุบันและอดีต
- ที่อยู่

### คู่สมรส (Spouse)
- ข้อมูลเดียวกับผู้ยื่น

### ญาติ (Relatives)
- บิดา, มารดา, พี่น้อง, บุตร
- ความสัมพันธ์, อาชีพ

### ทรัพย์สิน (Assets) - 40+ ประเภท
| หมวด | ตัวอย่าง |
|------|---------|
| ที่ดิน | โฉนด, น.ส.3, ส.ป.ก. |
| สิ่งปลูกสร้าง | บ้าน, คอนโด, อาคาร |
| ยานพาหนะ | รถยนต์, รถจักรยานยนต์, เรือ |
| สิทธิ/หลักทรัพย์ | ประกันชีวิต, กองทุน |
| อื่นๆ | ทอง, เครื่องประดับ, ของสะสม |

---

# Slide 8: Phase 4 & 5 - Output Generation

## 📊 JSON → CSV / Database

### Output Files (13+ CSV):

```
Output/
├── submitter_info.csv        # ข้อมูลผู้ยื่น
├── submitter_position.csv    # ตำแหน่งผู้ยื่น
├── spouse_info.csv           # ข้อมูลคู่สมรส
├── relative_info.csv         # ข้อมูลญาติ
├── asset.csv                 # รายการทรัพย์สิน
├── asset_land_info.csv       # รายละเอียดที่ดิน
├── asset_building_info.csv   # รายละเอียดสิ่งปลูกสร้าง
├── asset_vehicle_info.csv    # รายละเอียดยานพาหนะ
├── statement.csv             # สรุปรายได้/รายจ่าย
├── statement_detail.csv      # รายละเอียดการเงิน
├── nacc_data.db             # SQLite Database
└── validation_summary.csv    # สรุปการตรวจสอบ
```

---

# Slide 9: System Architecture

## 🏗️ High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Input Layer                                │
│  ┌──────────┐  ┌────────────────┐  ┌────────────────────────┐   │
│  │ PDF Files │  │ doc_info.csv   │  │ nacc_detail.csv       │   │
│  └──────────┘  └────────────────┘  └────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    Processing Pipeline                            │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐          │
│  │ Phase 1 │ → │ Phase 2 │ → │ Phase 3 │ → │ Phase 4 │ → Phase 5│
│  │ PDF→IMG │   │  OCR    │   │   LLM   │   │ CSV/DB  │   Summary│
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘          │
│       ↓             ↓             ↓             ↓                │
│   pdf2image    Typhoon/      GPT-4.1      pandas/              │
│   PyMuPDF      Ollama        -mini        SQLite               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                       Output Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ 13+ CSV Files│  │ SQLite DB    │  │ Validation Report   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

# Slide 10: Key Features & Advantages

## ⭐ จุดเด่นของระบบ

### 1. 🇹🇭 Thai Language Optimized
- รองรับภาษาไทยเต็มรูปแบบ
- แก้ไข OCR errors อัตโนมัติ

### 2. 🔄 Flexible Processing
- Skip phases ได้ตามต้องการ
- รองรับทั้ง API และ Local OCR

### 3. ⚡ Scalable
- Parallel document processing
- Multi-threaded page processing

### 4. 🛡️ Error Handling
- Retry mechanism
- Graceful fallbacks
- Confidence scoring

### 5. 📊 Comprehensive Output
- 13+ CSV files
- SQLite database
- Validation reports

---

# Slide 11: Performance & Results

## 📈 ผลการทดสอบ

### Test Dataset:
- **Test Phase 1**: 9 documents
- **Test Final**: 32+ documents

### Processing Metrics:

| Metric | Value |
|--------|-------|
| Average OCR Time | 2-5 sec/page |
| LLM Parsing Time | 5-15 sec/doc |
| Accuracy Rate | High confidence |
| Throughput | Parallel processing |

### Confidence Scoring:
```
extraction_status: success | partial | failed
confidence_score: 0.0 - 1.0
```

---

# Slide 12: Configuration & Flexibility

## ⚙️ Easy Configuration

### Environment Variables (.env):

```bash
# OCR Configuration
OCR_METHOD=ollama           # 'api' or 'ollama'
TYPHOON_API_KEY=xxx         # For API mode

# LLM Configuration
OPENAI_API_KEY=xxx
LLM_MODEL=gpt-4.1-mini
LLM_PARSE_MODE=page_by_page # or 'combined'
LLM_MAX_WORKERS=5           # Parallel workers

# Phase Control
SKIP_PHASE_1=false          # PDF to Image
SKIP_PHASE_2=false          # OCR
SKIP_PHASE_3=false          # LLM Parsing
SKIP_PHASE_4=false          # JSON to CSV
SKIP_PHASE_5=false          # Summary
```

---

# Slide 13: Use Cases

## 🎯 การนำไปใช้งาน

### 1. ตรวจสอบทรัพย์สิน
- เปรียบเทียบทรัพย์สินก่อน-หลังดำรงตำแหน่ง
- ตรวจหาความผิดปกติ

### 2. วิเคราะห์ข้อมูล
- สร้าง Dashboard visualization
- Statistical analysis

### 3. Database สำหรับค้นหา
- ค้นหาตามชื่อ, ตำแหน่ง, ทรัพย์สิน
- Cross-reference ระหว่างบุคคล

### 4. Compliance Reporting
- ตรวจสอบความครบถ้วน
- สร้างรายงานอัตโนมัติ

---

# Slide 14: Future Improvements

## 🔮 แผนพัฒนาในอนาคต

### Short-term:
- [ ] Web UI Dashboard
- [ ] Real-time processing status
- [ ] Batch upload interface

### Mid-term:
- [ ] Custom LLM fine-tuning
- [ ] Improved OCR accuracy
- [ ] Anomaly detection

### Long-term:
- [ ] Cross-document analysis
- [ ] Historical trend tracking
- [ ] Automated red-flag alerts

---

# Slide 15: Demo & Contact

## 🎬 Live Demo

### Quick Start:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run pipeline
python app.py
```

### Output Location:
```
./test phase 1/test phase 1 output/
├── *.json          # Parsed data
├── Train_*.csv     # Output CSVs
├── nacc_data.db    # SQLite database
└── validation_summary.csv
```

---

# Slide 16: Summary

## 📌 สรุป

### NACC Asset Declaration Parser

✅ **ปัญหาที่แก้**: แปลง PDF บัญชีทรัพย์สินเป็นข้อมูลมีโครงสร้าง

✅ **เทคโนโลยี**: OCR + LLM (GPT-4.1-mini) + Python

✅ **Output**: 13+ CSV files + SQLite Database

✅ **จุดเด่น**:
- รองรับภาษาไทย
- ประมวลผลอัตโนมัติ
- Scalable & Flexible

---

# 🙏 ขอบคุณครับ

## Q&A

**Repository**: GitHub
**Technologies**: Python, OCR, LLM, SQLite

---
