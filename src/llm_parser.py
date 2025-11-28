# -*- coding: utf-8 -*-
"""
LLM Parser for NACC Document - Phase 3
Uses GPT-4.1-mini to extract structured data from OCR text
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMParser:
    """LLM-based parser for NACC documents"""

    def __init__(self, model: str = "gpt-4.1-mini", temperature: float = 0.1):
        """
        Initialize LLM Parser

        Args:
            model: OpenAI model name (default: gpt-4.1-mini)
            temperature: Temperature for generation (lower = more deterministic)
        """
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """คุณเป็น AI ผู้เชี่ยวชาญในการวิเคราะห์และแยกข้อมูลจากเอกสารบัญชีแสดงรายการทรัพย์สินและหนี้สิน
ของสำนักงานคณะกรรมการป้องกันและปราบปรามการทุจริตแห่งชาติ (ป.ป.ช.)

หน้าที่ของคุณคือ:
1. อ่านและทำความเข้าใจข้อความจากเอกสาร OCR
2. แยกข้อมูลออกมาเป็น JSON ตามโครงสร้างที่กำหนด
3. จัดหมวดหมู่ทรัพย์สินตาม asset_type_id ที่ถูกต้อง
4. แปลงค่าตัวเลขเป็น float (ลบเครื่องหมาย , ออก)
5. แปลงวันที่เป็นตัวเลข (วัน, เดือน, ปี พ.ศ.)

กฎสำคัญ:
- ถ้าไม่พบข้อมูล ให้ใส่ null
- ตัวเลขเงินให้เก็บเป็น float (ไม่ใช่ string) เช่น 1234567.89
- ปี พ.ศ. ให้เก็บเป็น พ.ศ. (เช่น 2566)
- owner_by_* ให้เป็น boolean (true/false)
- ตอบเป็น JSON เท่านั้น ไม่ต้องมีคำอธิบายอื่น

Enum References:
- relationship_id: 1=บิดา, 2=มารดา, 3=พี่น้อง, 4=บุตร, 5=บิดาคู่สมรส, 6=มารดาคู่สมรส
- statement_type_id: 1=เงินสด/หลักทรัพย์/สิทธิ, 2=เงินฝาก, 3=เงินให้กู้ยืม, 4=ที่ดิน/โรงเรือน, 5=หนี้สิน
- asset_type_id: 1=โฉนด/ที่ดิน, 10=บ้านเดี่ยว, 11=อาคารพาณิชย์, 13=ห้องชุด/คอนโด, 18=รถยนต์, 19=มอเตอร์ไซค์, 22=กรมธรรม์ประกันภัย, 24=สิทธิในสมาชิก, 25=กองทุน, 28=กระเป๋า, 29=ปืน, 30=นาฬิกา, 31=เครื่องประดับ/อัญมณี/แหวน/สร้อย, 32=พระเครื่อง, 33=ทองคำ, 37=ทาวน์เฮ้าส์, 39=อื่นๆ
- date_acquiring_type_id: 1=ระบุวันที่แน่นอน, 2=ไม่ระบุ(ได้มาก่อน), 3=ไม่ทราบ, 4=ไม่มีวันสิ้นสุด
- asset_acquisition_type_id: 1=ซื้อ, 2=มรดก, 3=รับให้, 4=ประเมินราคา, 5=ราคาตลาด, 6=ราคาที่ได้มา
- statement_detail_type_id: 1=รายได้ประจำ, 2=รายได้จากทรัพย์สิน, 3=รายได้จากขาย/มรดก, 5=รายได้อื่น, 6=รายจ่ายประจำ, 7=รายจ่ายอื่น, 8=เงินสด, 9=เงินฝาก, 10=เงินลงทุน, 11=เงินให้กู้ยืม, 12=ที่ดิน, 13=โรงเรือน, 14=ยานพาหนะ, 15=สิทธิ/สัมปทาน, 16=ทรัพย์สินอื่น, 17=เงินเบิกเกินบัญชี, 18=เงินกู้ธนาคาร, 19=หนี้สินที่มีหลักฐาน, 20=หนี้สินอื่น"""

    def _get_user_prompt(self, ocr_text: str, doc_id: str, nacc_id: int) -> str:
        """Get user prompt with OCR text"""
        return f"""จากข้อความ OCR ต่อไปนี้ของเอกสาร ป.ป.ช. กรุณาแยกข้อมูลออกมาเป็น JSON:

---OCR TEXT START---
{ocr_text}
---OCR TEXT END---

Document ID: {doc_id}
NACC ID: {nacc_id}

โปรดส่งผลลัพธ์เป็น JSON ตามโครงสร้างนี้เท่านั้น:

{{
  "doc_id": "{doc_id}",
  "nacc_id": {nacc_id},
  "extraction_status": "success หรือ partial หรือ failed",
  "confidence_score": 0.0-1.0,

  "submitter_info": {{
    "title": "คำนำหน้า เช่น นาย, นาง, นางสาว, พลเอก",
    "first_name": "ชื่อ",
    "last_name": "นามสกุล",
    "age": ตัวเลขหรือnull,
    "marital_status": "สมรส/โสด/หย่า/คู่สมรสเสียชีวิต/อยู่กินกันฯ",
    "status_date": วันที่สมรสหรือnull,
    "status_month": เดือนสมรสหรือnull,
    "status_year": ปีสมรส(พ.ศ.)หรือnull,
    "sub_district": "ตำบล/แขวง",
    "district": "อำเภอ/เขต",
    "province": "จังหวัด",
    "post_code": "รหัสไปรษณีย์",
    "position": "ตำแหน่ง เช่น สมาชิกสภาผู้แทนราษฎร",
    "agency": "หน่วยงาน"
  }},

  "spouse_info": {{
    "title": "คำนำหน้า",
    "first_name": "ชื่อ",
    "last_name": "นามสกุล",
    "age": ตัวเลขหรือnull,
    "status": "จดทะเบียนสมรส/อยู่กินฯ",
    "status_date": วันที่หรือnull,
    "status_month": เดือนหรือnull,
    "status_year": ปี(พ.ศ.)หรือnull,
    "sub_district": "ตำบล/แขวง",
    "district": "อำเภอ/เขต",
    "province": "จังหวัด",
    "post_code": "รหัสไปรษณีย์"
  }} หรือ null ถ้าไม่มีคู่สมรส,

  "relatives": [
    {{
      "index": ลำดับเริ่มจาก1,
      "relationship_id": 1=บิดา/2=มารดา/3=พี่น้อง/4=บุตร/5=บิดาคู่สมรส/6=มารดาคู่สมรส,
      "title": "คำนำหน้า",
      "first_name": "ชื่อ",
      "last_name": "นามสกุล",
      "age": ตัวเลขหรือnull,
      "address": "ที่อยู่",
      "occupation": "อาชีพ",
      "school": "สถานศึกษา",
      "workplace": "ที่ทำงาน",
      "workplace_location": "ที่ตั้งที่ทำงาน",
      "is_death": true/false
    }}
  ],

  "statements": [
    {{
      "statement_type_id": 1-5,
      "valuation_submitter": ตัวเลขหรือnull,
      "valuation_spouse": ตัวเลขหรือnull,
      "valuation_child": ตัวเลขหรือnull
    }}
  ],

  "statement_details": [
    {{
      "statement_detail_type_id": 1-20,
      "index": ลำดับ,
      "detail": "รายละเอียด เช่น เงินเดือน, ค่าเช่า",
      "valuation_submitter": ตัวเลขหรือnull,
      "valuation_spouse": ตัวเลขหรือnull,
      "valuation_child": ตัวเลขหรือnull,
      "note": "หมายเหตุ"
    }}
  ],

  "assets": [
    {{
      "index": ลำดับเริ่มจาก1,
      "asset_type_id": 1/10/11/13/18/19/22/24/25/28/29/30/31/32/33/37/39,
      "asset_type_other": "ถ้าเป็นอื่นๆให้ระบุ",
      "asset_name": "ชื่อทรัพย์สิน เช่น โฉนด, รถยนต์ Toyota",
      "date_acquiring_type_id": 1=ระบุวันที่/2=ไม่ระบุ,
      "acquiring_date": วันที่ได้มาหรือnull,
      "acquiring_month": เดือนได้มาหรือnull,
      "acquiring_year": ปีได้มา(พ.ศ.)หรือnull,
      "date_ending_type_id": 1/2/3/4หรือnull,
      "ending_date": วันสิ้นสุดหรือnull,
      "ending_month": เดือนสิ้นสุดหรือnull,
      "ending_year": ปีสิ้นสุดหรือnull,
      "asset_acquisition_type_id": 1-6หรือnull,
      "valuation": มูลค่าเป็นตัวเลข,
      "owner_by_submitter": true/false,
      "owner_by_spouse": true/false,
      "owner_by_child": true/false
    }}
  ]
}}

สำคัญมาก: ตอบเป็น JSON เท่านั้น ไม่ต้องมี markdown code block หรือคำอธิบายอื่น"""

    def _extract_json_from_response(self, response_text: str) -> dict:
        """Extract JSON from LLM response"""
        # Try to parse directly
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object pattern
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract valid JSON from response: {response_text[:500]}...")

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=8000,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content

    def parse_document(self, ocr_texts: List[str], doc_id: str, nacc_id: int) -> Dict[str, Any]:
        """
        Parse OCR texts from all pages into structured data

        Args:
            ocr_texts: List of OCR text from each page
            doc_id: Document ID
            nacc_id: NACC ID

        Returns:
            Structured data as dictionary
        """
        # Combine all pages
        combined_text = "\n\n---PAGE BREAK---\n\n".join(ocr_texts)

        # Truncate if too long (GPT-4.1-mini context limit)
        max_chars = 100000
        if len(combined_text) > max_chars:
            combined_text = combined_text[:max_chars] + "\n\n[TEXT TRUNCATED]"

        # Get prompts
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(combined_text, doc_id, nacc_id)

        # Call LLM
        response_text = self._call_llm(system_prompt, user_prompt)

        # Parse response
        result = self._extract_json_from_response(response_text)

        # Ensure required fields
        result["doc_id"] = doc_id
        result["nacc_id"] = nacc_id

        return result

    def parse_document_from_files(self, txt_folder: str, doc_id: str, nacc_id: int) -> Dict[str, Any]:
        """
        Parse document from txt files in a folder

        Args:
            txt_folder: Path to folder containing OCR txt files
            doc_id: Document ID
            nacc_id: NACC ID

        Returns:
            Structured data as dictionary
        """
        ocr_texts = []

        # Get all txt files sorted by name
        txt_files = sorted([f for f in os.listdir(txt_folder) if f.endswith('.txt')])

        for txt_file in txt_files:
            txt_path = os.path.join(txt_folder, txt_file)
            with open(txt_path, 'r', encoding='utf-8') as f:
                ocr_texts.append(f.read())

        if not ocr_texts:
            return {
                "doc_id": doc_id,
                "nacc_id": nacc_id,
                "extraction_status": "failed",
                "confidence_score": 0,
                "error": "No OCR text files found"
            }

        return self.parse_document(ocr_texts, doc_id, nacc_id)


def test_parser():
    """Test the LLM parser"""
    parser = LLMParser(model="gpt-4.1-mini")

    # Example OCR text
    test_ocr = """
    บัญชีแสดงรายการทรัพย์สินและหนี้สิน

    ข้อมูลผู้ยื่น
    นาย ทดสอบ ตัวอย่าง
    ตำแหน่ง: สมาชิกสภาผู้แทนราษฎร
    อายุ: 45 ปี
    สถานภาพ: สมรส

    ข้อมูลคู่สมรส
    นาง ทดสอบ ตัวอย่าง
    อายุ: 42 ปี

    รายการทรัพย์สิน
    1. ที่ดิน โฉนด เลขที่ 12345
       ได้มา: 15/6/2560
       มูลค่า: 5,000,000 บาท
       เจ้าของ: ผู้ยื่น

    2. รถยนต์ Toyota Camry
       ได้มา: 1/3/2563
       มูลค่า: 1,200,000 บาท
       เจ้าของ: ผู้ยื่น
    """

    result = parser.parse_document([test_ocr], "TEST001", 999)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_parser()
