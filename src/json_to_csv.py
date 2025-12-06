# -*- coding: utf-8 -*-
"""
JSON to CSV Converter for NACC Document Data
Converts parsed JSON data to CSV format matching training output structure
Supports both CSV and SQLite output
"""

import os
import csv
import json
import re
import sqlite3
import unicodedata
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class JSONToCSVConverter:
    """Convert parsed JSON data to CSV files matching training output format"""

    def __init__(self, output_dir: str):
        """
        Initialize converter

        Args:
            output_dir: Directory to save CSV files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Initialize data containers
        self.statements = []
        self.statement_details = []
        self.assets = []
        self.asset_land_infos = []
        self.asset_building_infos = []
        self.asset_vehicle_infos = []
        self.asset_other_infos = []
        self.submitter_infos = []
        self.submitter_old_names = []
        self.submitter_positions = []
        self.spouse_infos = []
        self.spouse_old_names = []
        self.spouse_positions = []
        self.relative_infos = []
        self.summaries = []

        # Counters for IDs
        self.asset_id_counter = 1
        self.relative_id_counter = 1
        self.submitter_id_counter = 1
        self.spouse_id_counter = 1

        # Input data lookup tables (loaded from input CSV files)
        self.input_doc_info = {}      # doc_id -> {nacc_id, doc_location_url, type_id}
        self.input_doc_order = []     # List of doc_ids in order from doc_info.csv
        self.input_nacc_detail = {}   # nacc_id -> {title, first_name, last_name, position, dates, agency, submitter_id}
        self.input_submitter_info = {} # submitter_id -> {title, first_name, last_name, age, status, address, etc.}

    def _safe_get(self, data: dict, key: str, default=None):
        """Safely get value from dict"""
        return data.get(key, default) if data else default

    def _format_date(self, date_str: str) -> str:
        """Format date string to YYYY-MM-DD format"""
        if not date_str:
            return "NONE"
        # Convert D/M/YYYY or DD/MM/YYYY to YYYY-MM-DD
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return date_str

    def _parse_land_info(self, asset_name: str, asset_type_id: int) -> Dict[str, Any]:
        """
        Parse land information from asset_name

        Examples:
        - "โฉนดที่ดิน เลขที่ 114172 ตำบลคลองต้น อำเภอพระโขนง กรุงเทพมหานคร"
        - "น.ส.3 ก. เลขที่ 123 จังหวัดเชียงใหม่"

        Returns dict with: land_type, land_number, area_rai, area_ngan, area_sqwa, province
        """
        land_info = {
            "land_type": "",
            "land_number": "",
            "area_rai": "",
            "area_ngan": "",
            "area_sqwa": "",
            "province": ""
        }

        if not asset_name:
            return land_info

        # Map asset_type_id to land_type
        land_type_map = {
            1: "โฉนด",
            2: "น.ส.3 ก.",
            3: "น.ส.3",
            4: "ส.ป.ก."
        }
        land_info["land_type"] = land_type_map.get(asset_type_id, "")

        # Extract land number - patterns like "เลขที่ 114172", "เลขที่โฉนด 123"
        land_number_patterns = [
            r'เลขที่(?:โฉนด)?\s*(\d+)',
            r'เลขที่\s*(\d+)',
            r'ที่ดิน\s*เลขที่\s*(\d+)',
            r'โฉนด(?:ที่ดิน)?\s*(?:เลขที่)?\s*(\d+)'
        ]
        for pattern in land_number_patterns:
            match = re.search(pattern, asset_name)
            if match:
                land_info["land_number"] = match.group(1)
                break

        # Extract area - patterns like "0 ไร่ 1 งาน 50 ตารางวา"
        rai_match = re.search(r'(\d+(?:\.\d+)?)\s*ไร่', asset_name)
        if rai_match:
            land_info["area_rai"] = float(rai_match.group(1))

        ngan_match = re.search(r'(\d+(?:\.\d+)?)\s*งาน', asset_name)
        if ngan_match:
            land_info["area_ngan"] = float(ngan_match.group(1))

        sqwa_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ตารางวา|ตร\.ว\.?|วา)', asset_name)
        if sqwa_match:
            land_info["area_sqwa"] = float(sqwa_match.group(1))

        # Extract province - common patterns
        province_patterns = [
            r'จังหวัด(\S+)',
            r'กรุงเทพ(?:มหานคร)?',
            r'(\S+มหานคร)',
            # Province at end of address
            r'(?:อำเภอ|เขต)\S+\s+(\S+)$'
        ]

        # Try to find province
        for pattern in province_patterns:
            match = re.search(pattern, asset_name)
            if match:
                if 'กรุงเทพ' in pattern or 'กรุงเทพ' in match.group(0):
                    land_info["province"] = "กรุงเทพมหานคร"
                else:
                    land_info["province"] = match.group(1) if match.lastindex else match.group(0)
                break

        # Additional check for Bangkok
        if 'กรุงเทพ' in asset_name and not land_info["province"]:
            land_info["province"] = "กรุงเทพมหานคร"

        return land_info

    def _parse_building_info(self, asset_name: str, asset_type_id: int) -> Dict[str, Any]:
        """
        Parse building information from asset_name

        Examples:
        - "บ้านเดี่ยว 3 ชั้น"
        - "ห้องชุด เพนท์เฮ้าส์"
        - "ทาวน์เฮ้าส์"
        - "อาคารพาณิชย์ ตึกแถว"

        Returns dict with: building_type, building_name, room_number, province
        """
        building_info = {
            "building_type": "",
            "building_name": "",
            "room_number": "",
            "province": ""
        }

        if not asset_name:
            return building_info

        # Map asset_type_id to building_type
        building_type_map = {
            10: "บ้านเดี่ยว",
            11: "อาคารพาณิชย์",
            13: "ห้องชุด",
            37: "ทาวน์เฮ้าส์"
        }
        building_info["building_type"] = building_type_map.get(asset_type_id, "")

        # Extract building name (typically the full description)
        building_info["building_name"] = asset_name

        # Extract room number - patterns like "ห้องเลขที่ 123", "เลขที่ห้อง 456"
        room_patterns = [
            r'ห้อง(?:เลขที่)?\s*(\S+)',
            r'เลขที่(?:ห้อง)?\s*(\S+)',
            r'ชั้น\s*(\d+)',
            r'ยูนิต\s*(\S+)',
            r'unit\s*(\S+)'
        ]
        for pattern in room_patterns:
            match = re.search(pattern, asset_name, re.IGNORECASE)
            if match:
                building_info["room_number"] = match.group(1)
                break

        # Extract province
        if 'กรุงเทพ' in asset_name:
            building_info["province"] = "กรุงเทพมหานคร"
        else:
            province_match = re.search(r'จังหวัด(\S+)', asset_name)
            if province_match:
                building_info["province"] = province_match.group(1)

        return building_info

    def _parse_vehicle_info(self, asset_name: str, asset_type_id: int) -> Dict[str, Any]:
        """
        Parse vehicle information from asset_name

        Examples:
        - "รถยนต์ Mercedes Benz S400 Hybrid"
        - "รถจักรยานยนต์ HONDA WAVE"
        - "รถยนต์ Volkswagen Caravelle Minorchange 2 ปี 2019"

        Returns dict with: vehicle_type, brand, model, registration, province
        """
        vehicle_info = {
            "vehicle_type": "",
            "brand": "",
            "model": "",
            "registration": "",
            "province": ""
        }

        if not asset_name:
            return vehicle_info

        # Map asset_type_id to vehicle_type
        vehicle_type_map = {
            18: "รถยนต์",
            19: "รถจักรยานยนต์",
            20: "เรือ"
        }
        vehicle_info["vehicle_type"] = vehicle_type_map.get(asset_type_id, "")

        # Common car brands for detection
        car_brands = [
            'Mercedes Benz', 'Mercedes-Benz', 'Mercedes', 'Benz',
            'BMW', 'Audi', 'Lexus', 'Toyota', 'Honda', 'Nissan',
            'Mazda', 'Ford', 'Chevrolet', 'Volkswagen', 'Porsche',
            'Volvo', 'Hyundai', 'Kia', 'Mitsubishi', 'Suzuki',
            'Subaru', 'Isuzu', 'MG', 'Mini', 'Jaguar', 'Land Rover',
            'Range Rover', 'Ferrari', 'Lamborghini', 'Bentley', 'Rolls Royce',
            'Tesla', 'BYD', 'GWM', 'ORA', 'NETA',
            'HONDA', 'TOYOTA', 'YAMAHA', 'KAWASAKI', 'VESPA', 'Piaggio',
            'Ducati', 'Harley Davidson', 'Triumph', 'KTM'
        ]

        # Find brand in asset_name
        name_lower = asset_name.lower()
        for brand in car_brands:
            if brand.lower() in name_lower:
                vehicle_info["brand"] = brand
                # Try to extract model - text after brand
                brand_idx = name_lower.find(brand.lower())
                if brand_idx >= 0:
                    after_brand = asset_name[brand_idx + len(brand):].strip()
                    # Model is typically the first word/phrase after brand
                    model_match = re.match(r'^[\s,]*([A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+)?)', after_brand)
                    if model_match:
                        vehicle_info["model"] = model_match.group(1).strip()
                break

        # If no brand found, try to extract from text patterns
        if not vehicle_info["brand"]:
            # Pattern for "รถยนต์ XXX" or "รถจักรยานยนต์ XXX"
            vehicle_patterns = [
                r'รถยนต์\s+(\S+)',
                r'รถจักรยานยนต์\s+(\S+)',
                r'เรือ\s+(\S+)'
            ]
            for pattern in vehicle_patterns:
                match = re.search(pattern, asset_name)
                if match:
                    # First word after vehicle type could be brand
                    potential_brand = match.group(1)
                    if potential_brand and not potential_brand[0].isdigit():
                        vehicle_info["brand"] = potential_brand
                    break

        # Extract registration number - Thai license plate patterns
        # Patterns like "1กค5025", "กข 1234", "1-กก-1234"
        registration_patterns = [
            r'ทะเบียน\s*(\S+)',
            r'หมายเลขทะเบียน\s*(\S+)',
            r'เลขทะเบียน\s*(\S+)',
            r'([0-9]*[ก-ฮ]{1,3}[\s\-]?[0-9]{1,4})',  # Thai license plate
        ]
        for pattern in registration_patterns:
            match = re.search(pattern, asset_name)
            if match:
                vehicle_info["registration"] = match.group(1)
                break

        # Extract province for registration
        province_match = re.search(r'จังหวัด(\S+)', asset_name)
        if province_match:
            vehicle_info["province"] = province_match.group(1)
        elif 'กรุงเทพ' in asset_name:
            vehicle_info["province"] = "กรุงเทพมหานคร"

        return vehicle_info

    def load_input_data(self, input_dir: str, csv_doc_info: str = None, csv_nacc_detail: str = None, csv_submitter: str = None):
        """
        Load input CSV files into lookup tables for summary generation

        Args:
            input_dir: Directory containing input CSV files (Test_doc_info.csv, etc.)
            csv_doc_info: Optional filename for doc_info CSV (from ENV)
            csv_nacc_detail: Optional filename for nacc_detail CSV (from ENV)
            csv_submitter: Optional filename for submitter_info CSV (from ENV)
        """
        # Load doc_info - use provided filename or fallback to defaults
        if csv_doc_info:
            doc_info_path = os.path.join(input_dir, csv_doc_info)
        else:
            doc_info_path = os.path.join(input_dir, "Test_doc_info.csv")
            if not os.path.exists(doc_info_path):
                doc_info_path = os.path.join(input_dir, "Train_doc_info.csv")

        if os.path.exists(doc_info_path):
            with open(doc_info_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    doc_id = row.get('doc_id', '')
                    self.input_doc_info[doc_id] = {
                        'nacc_id': row.get('nacc_id', ''),
                        'doc_location_url': row.get('doc_location_url', ''),
                        'type_id': row.get('type_id', '')
                    }
                    self.input_doc_order.append(doc_id)  # Keep order from CSV
            print(f"✓ Loaded {len(self.input_doc_info)} records from doc_info")
        else:
            print(f"✗ doc_info file not found: {doc_info_path}")

        # Load nacc_detail - use provided filename or fallback to defaults
        if csv_nacc_detail:
            nacc_detail_path = os.path.join(input_dir, csv_nacc_detail)
        else:
            nacc_detail_path = os.path.join(input_dir, "Test_nacc_detail.csv")
            if not os.path.exists(nacc_detail_path):
                nacc_detail_path = os.path.join(input_dir, "Train_nacc_detail.csv")

        if os.path.exists(nacc_detail_path):
            with open(nacc_detail_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    nacc_id = row.get('nacc_id', '')
                    self.input_nacc_detail[nacc_id] = {
                        'title': row.get('title', ''),
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'position': row.get('position', ''),
                        'submitted_case': row.get('submitted_case', ''),
                        'submitted_date': row.get('submitted_date', ''),
                        'disclosure_announcement_date': row.get('disclosure_announcement_date', ''),
                        'disclosure_start_date': row.get('disclosure_start_date', ''),
                        'disclosure_end_date': row.get('disclosure_end_date', ''),
                        'agency': row.get('agency', ''),
                        'date_by_submitted_case': row.get('date_by_submitted_case', ''),
                        'royal_start_date': row.get('royal_start_date', ''),
                        'submitter_id': row.get('submitter_id', '')
                    }
            print(f"✓ Loaded {len(self.input_nacc_detail)} records from nacc_detail")
        else:
            print(f"✗ nacc_detail file not found: {nacc_detail_path}")

        # Load submitter_info - use provided filename or fallback to defaults
        if csv_submitter:
            submitter_info_path = os.path.join(input_dir, csv_submitter)
        else:
            submitter_info_path = os.path.join(input_dir, "Test_submitter_info.csv")
            if not os.path.exists(submitter_info_path):
                submitter_info_path = os.path.join(input_dir, "Train_submitter_info.csv")

        if os.path.exists(submitter_info_path):
            with open(submitter_info_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    submitter_id = row.get('submitter_id', '')
                    self.input_submitter_info[submitter_id] = {
                        'title': row.get('title', ''),
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'age': row.get('age', ''),
                        'status': row.get('status', ''),
                        'status_date': row.get('status_date', ''),
                        'status_month': row.get('status_month', ''),
                        'status_year': row.get('status_year', ''),
                        'sub_district': row.get('sub_district', ''),
                        'district': row.get('district', ''),
                        'province': row.get('province', ''),
                        'post_code': row.get('post_code', ''),
                        'phone_number': row.get('phone_number', ''),
                        'mobile_number': row.get('mobile_number', ''),
                        'email': row.get('email', '')
                    }
            print(f"✓ Loaded {len(self.input_submitter_info)} records from submitter_info")
        else:
            print(f"✗ submitter_info file not found: {submitter_info_path}")

    def _normalize_thai_text(self, text: str) -> str:
        """Normalize Thai text for comparison by removing extra spaces and normalizing Unicode"""
        import unicodedata
        if not text:
            return ''
        # Normalize Unicode (NFC form)
        normalized = unicodedata.normalize('NFC', text)
        # Remove extra spaces
        return normalized.strip()

    def _find_nacc_id_by_name(self, first_name: str, last_name: str) -> Optional[int]:
        """
        Find nacc_id from nacc_detail by matching first_name and last_name.
        Uses normalized comparison to handle Unicode variations.

        Args:
            first_name: First name to search
            last_name: Last name to search

        Returns:
            nacc_id if found, None otherwise
        """
        norm_first = self._normalize_thai_text(first_name)
        norm_last = self._normalize_thai_text(last_name)

        for nacc_id, detail in self.input_nacc_detail.items():
            detail_first = self._normalize_thai_text(detail.get('first_name', ''))
            detail_last = self._normalize_thai_text(detail.get('last_name', ''))

            # Exact match after normalization
            if detail_first == norm_first and detail_last == norm_last:
                return int(nacc_id)

        # If no exact match, try partial match (first name only)
        for nacc_id, detail in self.input_nacc_detail.items():
            detail_first = self._normalize_thai_text(detail.get('first_name', ''))
            if detail_first == norm_first and norm_first:
                return int(nacc_id)

        return None

    def _extract_name_from_filename(self, filename: str) -> Tuple[str, str]:
        """
        Extract first_name and last_name from PDF/JSON filename.
        Filename format: firstname_lastname_position_case_date.pdf

        Args:
            filename: PDF or JSON filename

        Returns:
            Tuple of (first_name, last_name)
        """
        # Remove extension
        base_name = os.path.splitext(filename)[0]
        # Split by underscore
        parts = base_name.split('_')
        if len(parts) >= 2:
            first_name = parts[0]
            last_name = parts[1]
            return first_name, last_name
        return '', ''

    def process_from_doc_info(self, json_dir: str) -> int:
        """
        Process all documents using doc_info.csv as the driver.

        For each row in doc_info.csv:
        1. Use doc_id from doc_info.csv
        2. Use nacc_id from doc_info.csv to lookup data from nacc_detail.csv and submitter_info.csv
        3. Find JSON file by doc_location_url (filename)
        4. Process and generate output row

        Args:
            json_dir: Directory containing JSON files

        Returns:
            Number of documents processed
        """
        if not self.input_doc_info:
            print("✗ No doc_info data loaded. Call load_input_data first.")
            return 0

        processed_count = 0
        missing_json = []

        print(f"\n--- Processing {len(self.input_doc_order)} documents from doc_info ---")

        for doc_id in self.input_doc_order:
            doc_info = self.input_doc_info.get(doc_id, {})
            nacc_id = int(doc_info.get('nacc_id', 0))
            doc_location_url = doc_info.get('doc_location_url', '')

            # Get JSON filename from doc_location_url (replace .pdf with .json)
            if doc_location_url:
                json_filename = os.path.splitext(doc_location_url)[0] + '.json'
                # Normalize Unicode for Thai filename matching
                json_filename = unicodedata.normalize('NFC', json_filename)
            else:
                json_filename = None

            json_path = os.path.join(json_dir, json_filename) if json_filename else None

            print(f"  doc_id={doc_id}, nacc_id={nacc_id}, file={json_filename}")

            # Try to find matching JSON file with Unicode normalization
            json_found = False
            if json_path:
                # First try exact path
                if os.path.exists(json_path):
                    json_found = True
                else:
                    # Try to find file by scanning directory with normalized comparison
                    try:
                        for f in os.listdir(json_dir):
                            if f.endswith('.json'):
                                normalized_f = unicodedata.normalize('NFC', f)
                                if normalized_f == json_filename:
                                    json_path = os.path.join(json_dir, f)
                                    json_found = True
                                    break
                    except Exception:
                        pass

            if json_found:
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        parsed_data = json.load(f)

                    # Process with doc_id and nacc_id from doc_info.csv (NOT from JSON file)
                    self.process_document(
                        parsed_data,
                        override_doc_id=str(doc_id),
                        override_nacc_id=nacc_id
                    )
                    processed_count += 1
                    print(f"    ✓ Processed")
                except Exception as e:
                    print(f"    ✗ Error: {e}")
            else:
                missing_json.append(doc_id)
                print(f"    ✗ JSON file not found: {json_path}")

        print(f"\n--- Processing Complete ---")
        print(f"  Processed: {processed_count} documents")
        if missing_json:
            print(f"  Missing JSON: {len(missing_json)} documents: {missing_json}")

        return processed_count

    def process_document(self, parsed_data: Dict[str, Any], submitter_id: int = None,
                         override_doc_id: str = None, override_nacc_id: int = None) -> int:
        """
        Process a single parsed document and add to data containers

        Args:
            parsed_data: Parsed JSON data from LLM
            submitter_id: Optional submitter ID, auto-generated if not provided
            override_doc_id: Override doc_id from doc_info.csv (use this instead of JSON value)
            override_nacc_id: Override nacc_id from doc_info.csv (use this instead of JSON value)

        Returns:
            submitter_id used
        """
        if submitter_id is None:
            submitter_id = self.submitter_id_counter
            self.submitter_id_counter += 1

        # Use override values from doc_info.csv if provided, otherwise use JSON values
        doc_id = override_doc_id if override_doc_id is not None else parsed_data.get("doc_id", "")
        nacc_id = override_nacc_id if override_nacc_id is not None else parsed_data.get("nacc_id", 0)

        # Process submitter info
        self._process_submitter(parsed_data, submitter_id, nacc_id)

        # Process spouse info
        self._process_spouse(parsed_data, submitter_id, nacc_id)

        # Process relatives
        self._process_relatives(parsed_data, submitter_id, nacc_id)

        # Process statements
        self._process_statements(parsed_data, submitter_id, nacc_id)

        # Process statement details
        self._process_statement_details(parsed_data, submitter_id, nacc_id)

        # Process assets
        self._process_assets(parsed_data, submitter_id, nacc_id)

        # Generate summary
        self._generate_summary(parsed_data, submitter_id, nacc_id, doc_id)

        return submitter_id

    def _process_submitter(self, data: Dict, submitter_id: int, nacc_id: int):
        """Process submitter information"""
        submitter = data.get("submitter_info", {})
        if not submitter:
            return

        today = datetime.now().strftime("%Y-%m-%d")

        self.submitter_infos.append({
            "submitter_id": submitter_id,
            "nacc_id": nacc_id,
            "title": self._safe_get(submitter, "title", ""),
            "first_name": self._safe_get(submitter, "first_name", ""),
            "last_name": self._safe_get(submitter, "last_name", ""),
            "age": self._safe_get(submitter, "age", ""),
            "marital_status": self._safe_get(submitter, "marital_status", ""),
            "status_date": self._safe_get(submitter, "status_date", ""),
            "status_month": self._safe_get(submitter, "status_month", ""),
            "status_year": self._safe_get(submitter, "status_year", ""),
            "sub_district": self._safe_get(submitter, "sub_district", ""),
            "district": self._safe_get(submitter, "district", ""),
            "province": self._safe_get(submitter, "province", ""),
            "post_code": self._safe_get(submitter, "post_code", ""),
            "phone_number": self._safe_get(submitter, "phone_number", ""),
            "mobile_number": self._safe_get(submitter, "mobile_number", ""),
            "email": self._safe_get(submitter, "email", ""),
            "latest_submitted_date": today
        })

        # Process submitter positions
        positions = submitter.get("positions", [])
        for pos in positions:
            self.submitter_positions.append({
                "submitter_id": submitter_id,
                "nacc_id": nacc_id,
                "position_period_type_id": self._safe_get(pos, "position_period_type_id", ""),
                "index": self._safe_get(pos, "index", 0),
                "position": self._safe_get(pos, "position", ""),
                "position_category_type_id": self._safe_get(pos, "position_category_type_id", ""),
                "workplace": self._safe_get(pos, "workplace", ""),
                "workplace_location": self._safe_get(pos, "workplace_location", ""),
                "date_acquiring_type_id": self._safe_get(pos, "date_acquiring_type_id", ""),
                "start_date": self._safe_get(pos, "start_date", ""),
                "start_month": self._safe_get(pos, "start_month", ""),
                "start_year": self._safe_get(pos, "start_year", ""),
                "date_ending_type_id": self._safe_get(pos, "date_ending_type_id", ""),
                "end_date": self._safe_get(pos, "end_date", ""),
                "end_month": self._safe_get(pos, "end_month", ""),
                "end_year": self._safe_get(pos, "end_year", ""),
                "note": self._safe_get(pos, "note", ""),
                "latest_submitted_date": today
            })

        # Process submitter old names
        old_names = submitter.get("old_names", [])
        for idx, old_name in enumerate(old_names, 1):
            # Handle both string and dict formats
            if isinstance(old_name, str):
                # If old_name is a plain string, treat as first_name
                self.submitter_old_names.append({
                    "submitter_id": submitter_id,
                    "nacc_id": nacc_id,
                    "index": idx,
                    "title": "",
                    "first_name": old_name,
                    "last_name": "",
                    "title_en": "",
                    "first_name_en": "",
                    "last_name_en": "",
                    "latest_submitted_date": today
                })
            else:
                self.submitter_old_names.append({
                    "submitter_id": submitter_id,
                    "nacc_id": nacc_id,
                    "index": self._safe_get(old_name, "index", idx),
                    "title": self._safe_get(old_name, "title", ""),
                    "first_name": self._safe_get(old_name, "first_name", ""),
                    "last_name": self._safe_get(old_name, "last_name", ""),
                    "title_en": self._safe_get(old_name, "title_en", ""),
                    "first_name_en": self._safe_get(old_name, "first_name_en", ""),
                    "last_name_en": self._safe_get(old_name, "last_name_en", ""),
                    "latest_submitted_date": today
                })

    def _process_spouse(self, data: Dict, submitter_id: int, nacc_id: int):
        """Process spouse information"""
        spouse = data.get("spouse_info")
        if not spouse:
            return

        spouse_id = self.spouse_id_counter
        self.spouse_id_counter += 1
        today = datetime.now().strftime("%Y-%m-%d")

        self.spouse_infos.append({
            "spouse_id": spouse_id,
            "submitter_id": submitter_id,
            "nacc_id": nacc_id,
            "title": self._safe_get(spouse, "title", ""),
            "first_name": self._safe_get(spouse, "first_name", ""),
            "last_name": self._safe_get(spouse, "last_name", ""),
            "title_en": self._safe_get(spouse, "title_en", ""),
            "first_name_en": self._safe_get(spouse, "first_name_en", ""),
            "last_name_en": self._safe_get(spouse, "last_name_en", ""),
            "age": self._safe_get(spouse, "age", ""),
            "status": self._safe_get(spouse, "status", ""),
            "status_date": self._safe_get(spouse, "status_date", ""),
            "status_month": self._safe_get(spouse, "status_month", ""),
            "status_year": self._safe_get(spouse, "status_year", ""),
            "sub_district": self._safe_get(spouse, "sub_district", ""),
            "district": self._safe_get(spouse, "district", ""),
            "province": self._safe_get(spouse, "province", ""),
            "post_code": self._safe_get(spouse, "post_code", ""),
            "phone_number": self._safe_get(spouse, "phone_number", ""),
            "mobile_number": self._safe_get(spouse, "mobile_number", ""),
            "email": self._safe_get(spouse, "email", ""),
            "latest_submitted_date": today
        })

        # Process spouse old names
        old_names = spouse.get("old_names", [])
        for idx, old_name in enumerate(old_names, 1):
            # Handle both string and dict formats
            if isinstance(old_name, str):
                # If old_name is a plain string, treat as first_name
                self.spouse_old_names.append({
                    "spouse_id": spouse_id,
                    "index": idx,
                    "title": "",
                    "first_name": old_name,
                    "last_name": "",
                    "title_en": "",
                    "first_name_en": "",
                    "last_name_en": "",
                    "submitter_id": submitter_id,
                    "nacc_id": nacc_id,
                    "latest_submitted_date": today
                })
            else:
                self.spouse_old_names.append({
                    "spouse_id": spouse_id,
                    "index": self._safe_get(old_name, "index", idx),
                    "title": self._safe_get(old_name, "title", ""),
                    "first_name": self._safe_get(old_name, "first_name", ""),
                    "last_name": self._safe_get(old_name, "last_name", ""),
                    "title_en": self._safe_get(old_name, "title_en", ""),
                    "first_name_en": self._safe_get(old_name, "first_name_en", ""),
                    "last_name_en": self._safe_get(old_name, "last_name_en", ""),
                    "submitter_id": submitter_id,
                    "nacc_id": nacc_id,
                    "latest_submitted_date": today
                })

        # Process spouse positions
        positions = spouse.get("positions", [])
        for pos in positions:
            self.spouse_positions.append({
                "spouse_id": spouse_id,
                "submitter_id": submitter_id,
                "nacc_id": nacc_id,
                "position_period_type_id": self._safe_get(pos, "position_period_type_id", ""),
                "index": self._safe_get(pos, "index", 0),
                "position": self._safe_get(pos, "position", ""),
                "workplace": self._safe_get(pos, "workplace", ""),
                "workplace_location": self._safe_get(pos, "workplace_location", ""),
                "note": self._safe_get(pos, "note", ""),
                "latest_submitted_date": today
            })

    def _process_relatives(self, data: Dict, submitter_id: int, nacc_id: int):
        """Process relatives information"""
        relatives = data.get("relatives", [])
        today = datetime.now().strftime("%Y-%m-%d")

        for relative in relatives:
            relative_id = self.relative_id_counter
            self.relative_id_counter += 1

            self.relative_infos.append({
                "relative_id": relative_id,
                "submitter_id": submitter_id,
                "nacc_id": nacc_id,
                "index": self._safe_get(relative, "index", 1),
                "relationship_id": self._safe_get(relative, "relationship_id", ""),
                "title": self._safe_get(relative, "title", ""),
                "first_name": self._safe_get(relative, "first_name", ""),
                "last_name": self._safe_get(relative, "last_name", ""),
                "age": self._safe_get(relative, "age", ""),
                "address": self._safe_get(relative, "address", ""),
                "occupation": self._safe_get(relative, "occupation", ""),
                "school": self._safe_get(relative, "school", ""),
                "workplace": self._safe_get(relative, "workplace", ""),
                "workplace_location": self._safe_get(relative, "workplace_location", ""),
                "latest_submitted_date": today,
                "is_death": "TRUE" if self._safe_get(relative, "is_death", False) else "FALSE"
            })

    def _process_statements(self, data: Dict, submitter_id: int, nacc_id: int):
        """Process statement data"""
        statements = data.get("statements", [])
        today = datetime.now().strftime("%Y-%m-%d")

        for stmt in statements:
            self.statements.append({
                "nacc_id": nacc_id,
                "statement_type_id": self._safe_get(stmt, "statement_type_id", ""),
                "valuation_submitter": self._safe_get(stmt, "valuation_submitter", ""),
                "submitter_id": submitter_id,
                "valuation_spouse": self._safe_get(stmt, "valuation_spouse", ""),
                "valuation_child": self._safe_get(stmt, "valuation_child", ""),
                "latest_submitted_date": today
            })

    def _process_statement_details(self, data: Dict, submitter_id: int, nacc_id: int):
        """Process statement details"""
        details = data.get("statement_details", [])
        today = datetime.now().strftime("%Y-%m-%d")

        for detail in details:
            self.statement_details.append({
                "nacc_id": nacc_id,
                "submitter_id": submitter_id,
                "statement_detail_type_id": self._safe_get(detail, "statement_detail_type_id", ""),
                "index": self._safe_get(detail, "index", 1),
                "detail": self._safe_get(detail, "detail", ""),
                "valuation_submitter": self._safe_get(detail, "valuation_submitter", ""),
                "valuation_spouse": self._safe_get(detail, "valuation_spouse", ""),
                "valuation_child": self._safe_get(detail, "valuation_child", ""),
                "note": self._safe_get(detail, "note", ""),
                "latest_submitted_date": today
            })

    def _process_assets(self, data: Dict, submitter_id: int, nacc_id: int):
        """Process assets"""
        assets = data.get("assets", [])
        today = datetime.now().strftime("%Y-%m-%d")

        for asset in assets:
            asset_id = self.asset_id_counter
            self.asset_id_counter += 1

            asset_type_id = self._safe_get(asset, "asset_type_id", 39)

            self.assets.append({
                "asset_id": asset_id,
                "submitter_id": submitter_id,
                "nacc_id": nacc_id,
                "index": self._safe_get(asset, "index", 1),
                "asset_type_id": asset_type_id,
                "asset_type_other": self._safe_get(asset, "asset_type_other", ""),
                "asset_name": self._safe_get(asset, "asset_name", ""),
                "date_acquiring_type_id": self._safe_get(asset, "date_acquiring_type_id", ""),
                "acquiring_date": self._safe_get(asset, "acquiring_date", ""),
                "acquiring_month": self._safe_get(asset, "acquiring_month", ""),
                "acquiring_year": self._safe_get(asset, "acquiring_year", ""),
                "date_ending_type_id": self._safe_get(asset, "date_ending_type_id", ""),
                "ending_date": self._safe_get(asset, "ending_date", ""),
                "ending_month": self._safe_get(asset, "ending_month", ""),
                "ending_year": self._safe_get(asset, "ending_year", ""),
                "asset_acquisition_type_id": self._safe_get(asset, "asset_acquisition_type_id", ""),
                "valuation": self._safe_get(asset, "valuation", ""),
                "owner_by_submitter": "TRUE" if self._safe_get(asset, "owner_by_submitter", False) else "FALSE",
                "owner_by_spouse": "TRUE" if self._safe_get(asset, "owner_by_spouse", False) else "FALSE",
                "owner_by_child": "TRUE" if self._safe_get(asset, "owner_by_child", False) else "FALSE",
                "latest_submitted_date": today
            })

            # Get asset_name for parsing
            asset_name = self._safe_get(asset, "asset_name", "")

            # Process land info - parse from asset_name if no nested object
            if asset_type_id in [1, 2, 3, 4]:
                land_info = self._safe_get(asset, "land_info", {})
                # If land_info is empty or has no land_number, parse from asset_name
                if not land_info or not land_info.get("land_number"):
                    land_info = self._parse_land_info(asset_name, asset_type_id)
                self.asset_land_infos.append({
                    "asset_id": asset_id,
                    "nacc_id": nacc_id,
                    "land_type": self._safe_get(land_info, "land_type", ""),
                    "land_number": self._safe_get(land_info, "land_number", ""),
                    "area_rai": self._safe_get(land_info, "area_rai", ""),
                    "area_ngan": self._safe_get(land_info, "area_ngan", ""),
                    "area_sqwa": self._safe_get(land_info, "area_sqwa", ""),
                    "province": self._safe_get(land_info, "province", ""),
                    "latest_submitted_date": today
                })

            # Process building info - parse from asset_name if no nested object
            if asset_type_id in [10, 11, 13, 37]:
                building_info = self._safe_get(asset, "building_info", {})
                # If building_info is empty, parse from asset_name
                if not building_info or not building_info.get("building_type"):
                    building_info = self._parse_building_info(asset_name, asset_type_id)
                self.asset_building_infos.append({
                    "asset_id": asset_id,
                    "nacc_id": nacc_id,
                    "building_type": self._safe_get(building_info, "building_type", ""),
                    "building_name": self._safe_get(building_info, "building_name", ""),
                    "room_number": self._safe_get(building_info, "room_number", ""),
                    "province": self._safe_get(building_info, "province", ""),
                    "latest_submitted_date": today
                })

            # Process vehicle info - parse from asset_name if no nested object
            if asset_type_id in [18, 19, 20]:
                vehicle_info = self._safe_get(asset, "vehicle_info", {})
                # If vehicle_info is empty, parse from asset_name
                if not vehicle_info or not vehicle_info.get("brand"):
                    vehicle_info = self._parse_vehicle_info(asset_name, asset_type_id)
                self.asset_vehicle_infos.append({
                    "asset_id": asset_id,
                    "nacc_id": nacc_id,
                    "vehicle_type": self._safe_get(vehicle_info, "vehicle_type", ""),
                    "brand": self._safe_get(vehicle_info, "brand", ""),
                    "model": self._safe_get(vehicle_info, "model", ""),
                    "registration": self._safe_get(vehicle_info, "registration", ""),
                    "province": self._safe_get(vehicle_info, "province", ""),
                    "latest_submitted_date": today
                })

            # Process other asset info
            if asset_type_id not in [1, 2, 3, 4, 10, 11, 13, 18, 19, 20, 37]:
                self.asset_other_infos.append({
                    "asset_id": asset_id,
                    "nacc_id": nacc_id,
                    "description": self._safe_get(asset, "asset_name", ""),
                    "latest_submitted_date": today
                })

    def _generate_summary(self, data: Dict, submitter_id: int, nacc_id: int, doc_id: str):
        """Generate summary record matching training data format

        Uses data from input files (nacc_detail, submitter_info) for base columns,
        and LLM parsed data for calculated columns (statements, assets, relatives).
        """
        # Get LLM parsed data for spouse and calculated fields
        spouse = data.get("spouse_info", {})

        # Get statements and calculate totals from LLM parsed data
        statements = data.get("statements", [])
        statement_details = data.get("statement_details", [])
        assets = data.get("assets", [])
        relatives = data.get("relatives", [])

        total_valuation_submitter = sum(
            s.get("valuation_submitter", 0) or 0 for s in statements
        )
        total_valuation_spouse = sum(
            s.get("valuation_spouse", 0) or 0 for s in statements
        )
        total_valuation_child = sum(
            s.get("valuation_child", 0) or 0 for s in statements
        )

        # Count assets by type (land: 1-9, building: 10-17, vehicle: 18-21)
        asset_land_count = sum(1 for a in assets if a.get("asset_type_id") in range(1, 10))
        asset_building_count = sum(1 for a in assets if a.get("asset_type_id") in range(10, 18))
        asset_vehicle_count = sum(1 for a in assets if a.get("asset_type_id") in range(18, 22))
        asset_other_count = sum(1 for a in assets if a.get("asset_type_id") and a.get("asset_type_id") >= 22)

        # Calculate asset valuations by type
        asset_total = sum(a.get("valuation", 0) or 0 for a in assets)
        asset_land_val = sum(a.get("valuation", 0) or 0 for a in assets if a.get("asset_type_id") in range(1, 10))
        asset_building_val = sum(a.get("valuation", 0) or 0 for a in assets if a.get("asset_type_id") in range(10, 18))
        asset_vehicle_val = sum(a.get("valuation", 0) or 0 for a in assets if a.get("asset_type_id") in range(18, 22))
        asset_other_val = sum(a.get("valuation", 0) or 0 for a in assets if a.get("asset_type_id") and a.get("asset_type_id") >= 22)

        # Calculate asset valuations by owner
        asset_submitter_val = sum(a.get("valuation", 0) or 0 for a in assets if a.get("owner_by_submitter"))
        asset_spouse_val = sum(a.get("valuation", 0) or 0 for a in assets if a.get("owner_by_spouse"))
        asset_child_val = sum(a.get("valuation", 0) or 0 for a in assets if a.get("owner_by_child"))

        # Check for death flag in relatives
        has_death_flag = 1 if any(r.get("is_death") for r in relatives) else 0

        # Check for statement detail notes
        has_detail_note = 1 if any(d.get("note") for d in statement_details) else 0

        # Get spouse_id (use the counter value - 1 since it was already incremented)
        spouse_id = self.spouse_id_counter - 1 if spouse else None

        # ==================== Use Input Data for Base Columns ====================
        # Get nacc_detail from input file (for nd_* columns and dates)
        nacc_detail = self.input_nacc_detail.get(str(nacc_id), {})

        # Get submitter_id from nacc_detail if available
        input_submitter_id = nacc_detail.get('submitter_id', '') or str(submitter_id)

        # Get submitter_info from input file
        submitter_input = self.input_submitter_info.get(input_submitter_id, {})

        # Helper function to get value with fallback
        def get_value(val, fallback="NONE"):
            return val if val and val.strip() else fallback

        # Helper function to format date
        def format_date(val):
            return self._format_date(val) if val and val.strip() else "NONE"

        self.summaries.append({
            # ID columns - from nacc_detail
            "id": nacc_id,
            "doc_id": doc_id,

            # nd_* columns - from nacc_detail input file, fallback to submitter_info
            "nd_title": get_value(nacc_detail.get('title', '')) or get_value(submitter_input.get('title', '')),
            "nd_first_name": get_value(nacc_detail.get('first_name', '')) or get_value(submitter_input.get('first_name', '')),
            "nd_last_name": get_value(nacc_detail.get('last_name', '')) or get_value(submitter_input.get('last_name', '')),
            "nd_position": get_value(nacc_detail.get('position', '')),

            # Date columns - from nacc_detail input file (format to YYYY-MM-DD)
            "submitted_date": format_date(nacc_detail.get('submitted_date', '')),
            "disclosure_announcement_date": format_date(nacc_detail.get('disclosure_announcement_date', '')),
            "disclosure_start_date": format_date(nacc_detail.get('disclosure_start_date', '')),
            "disclosure_end_date": format_date(nacc_detail.get('disclosure_end_date', '')),
            "date_by_submitted_case": format_date(nacc_detail.get('date_by_submitted_case', '')),
            "royal_start_date": format_date(nacc_detail.get('royal_start_date', '')),
            "agency": get_value(nacc_detail.get('agency', '')),

            # submitter_* columns - from submitter_info input file
            "submitter_id": input_submitter_id,
            "submitter_title": get_value(submitter_input.get('title', '')),
            "submitter_first_name": get_value(submitter_input.get('first_name', '')),
            "submitter_last_name": get_value(submitter_input.get('last_name', '')),
            "submitter_age": get_value(submitter_input.get('age', '')),
            "submitter_marital_status": get_value(submitter_input.get('status', '')),
            "submitter_status_date": get_value(submitter_input.get('status_date', '')),
            "submitter_status_month": get_value(submitter_input.get('status_month', '')),
            "submitter_status_year": get_value(submitter_input.get('status_year', '')),
            "submitter_sub_district": get_value(submitter_input.get('sub_district', '')),
            "submitter_district": get_value(submitter_input.get('district', '')),
            "submitter_province": get_value(submitter_input.get('province', '')),
            "submitter_post_code": get_value(submitter_input.get('post_code', '')),
            "submitter_phone_number": get_value(submitter_input.get('phone_number', '')),
            "submitter_mobile_number": get_value(submitter_input.get('mobile_number', '')),
            "submitter_email": get_value(submitter_input.get('email', '')),

            # spouse_* columns - from LLM parsed data
            "spouse_id": spouse_id if spouse else "NONE",
            "spouse_title": self._safe_get(spouse, "title", "NONE") if spouse else "NONE",
            "spouse_first_name": self._safe_get(spouse, "first_name", "NONE") if spouse else "NONE",
            "spouse_last_name": self._safe_get(spouse, "last_name", "NONE") if spouse else "NONE",
            "spouse_age": self._safe_get(spouse, "age", "NONE") if spouse else "NONE",
            "spouse_status": self._safe_get(spouse, "status", "NONE") if spouse else "NONE",
            "spouse_status_date": self._safe_get(spouse, "status_date", "NONE") if spouse else "NONE",
            "spouse_status_month": self._safe_get(spouse, "status_month", "NONE") if spouse else "NONE",
            "spouse_status_year": self._safe_get(spouse, "status_year", "NONE") if spouse else "NONE",

            # Calculated columns - from LLM parsed data
            "statement_valuation_submitter_total": total_valuation_submitter or "NONE",
            "statement_valuation_spouse_total": total_valuation_spouse or "NONE",
            "statement_valuation_child_total": total_valuation_child or "NONE",
            "statement_detail_count": len(statement_details) or "NONE",
            "has_statement_detail_note": has_detail_note,
            "asset_count": len(assets) or "NONE",
            "asset_land_count": asset_land_count or "NONE",
            "asset_building_count": asset_building_count or "NONE",
            "asset_vehicle_count": asset_vehicle_count or "NONE",
            "asset_other_count": asset_other_count or "NONE",
            "asset_total_valuation_amount": asset_total or "NONE",
            "asset_land_valuation_amount": asset_land_val or "NONE",
            "asset_building_valuation_amount": asset_building_val or "NONE",
            "asset_vehicle_valuation_amount": asset_vehicle_val or "NONE",
            "asset_other_asset_valuation_amount": asset_other_val or "NONE",
            "asset_valuation_submitter_amount": asset_submitter_val or "NONE",
            "asset_valuation_spouse_amount": asset_spouse_val or "NONE",
            "asset_valuation_child_amount": asset_child_val or "NONE",
            "relative_count": len(relatives),
            "relative_has_death_flag": has_death_flag
        })

    def _write_csv(self, filename: str, data: List[Dict], fieldnames: List[str]):
        """Write data to CSV file"""
        if not data:
            return

        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                # Only include fields that exist in fieldnames
                filtered_row = {}
                for k, v in row.items():
                    if k not in fieldnames:
                        continue
                    # Convert float to int if it's a whole number (remove .0)
                    if isinstance(v, float) and v == int(v):
                        filtered_row[k] = int(v)
                    # Convert empty string to NONE for consistency
                    elif v == '' or v is None:
                        filtered_row[k] = 'NONE'
                    else:
                        filtered_row[k] = v
                writer.writerow(filtered_row)

        print(f"✓ Written {len(data)} records to {filename}")

    def save_all_csv(self, output_prefix: str = "Train"):
        """Save all data to CSV files

        Args:
            output_prefix: Prefix for output filenames (default: "Train")
        """
        # Statement
        self._write_csv(f"{output_prefix}_statement.csv", self.statements, [
            "nacc_id", "statement_type_id", "valuation_submitter", "submitter_id",
            "valuation_spouse", "valuation_child", "latest_submitted_date"
        ])

        # Statement details
        self._write_csv(f"{output_prefix}_statement_detail.csv", self.statement_details, [
            "nacc_id", "submitter_id", "statement_detail_type_id", "index",
            "detail", "valuation_submitter", "valuation_spouse", "valuation_child",
            "note", "latest_submitted_date"
        ])

        # Assets
        self._write_csv(f"{output_prefix}_asset.csv", self.assets, [
            "asset_id", "submitter_id", "nacc_id", "index", "asset_type_id",
            "asset_type_other", "asset_name", "date_acquiring_type_id",
            "acquiring_date", "acquiring_month", "acquiring_year",
            "date_ending_type_id", "ending_date", "ending_month", "ending_year",
            "asset_acquisition_type_id", "valuation",
            "owner_by_submitter", "owner_by_spouse", "owner_by_child",
            "latest_submitted_date"
        ])

        # Asset land info
        self._write_csv(f"{output_prefix}_asset_land_info.csv", self.asset_land_infos, [
            "asset_id", "nacc_id", "land_type", "land_number",
            "area_rai", "area_ngan", "area_sqwa", "province", "latest_submitted_date"
        ])

        # Asset building info
        self._write_csv(f"{output_prefix}_asset_building_info.csv", self.asset_building_infos, [
            "asset_id", "nacc_id", "building_type", "building_name",
            "room_number", "province", "latest_submitted_date"
        ])

        # Asset vehicle info
        self._write_csv(f"{output_prefix}_asset_vehicle_info.csv", self.asset_vehicle_infos, [
            "asset_id", "nacc_id", "vehicle_type", "brand", "model",
            "registration", "province", "latest_submitted_date"
        ])

        # Asset other info
        self._write_csv(f"{output_prefix}_asset_other_asset_info.csv", self.asset_other_infos, [
            "asset_id", "nacc_id", "description", "latest_submitted_date"
        ])

        # Relative info
        self._write_csv(f"{output_prefix}_relative_info.csv", self.relative_infos, [
            "relative_id", "submitter_id", "nacc_id", "index", "relationship_id",
            "title", "first_name", "last_name", "age", "address", "occupation",
            "school", "workplace", "workplace_location", "latest_submitted_date", "is_death"
        ])

        # Spouse info
        self._write_csv(f"{output_prefix}_spouse_info.csv", self.spouse_infos, [
            "spouse_id", "submitter_id", "nacc_id", "title", "first_name", "last_name",
            "title_en", "first_name_en", "last_name_en", "age", "status",
            "status_date", "status_month", "status_year", "sub_district", "district",
            "province", "post_code", "phone_number", "mobile_number", "email",
            "latest_submitted_date"
        ])

        # Submitter old name
        self._write_csv(f"{output_prefix}_submitter_old_name.csv", self.submitter_old_names, [
            "submitter_id", "nacc_id", "index", "title", "first_name", "last_name",
            "title_en", "first_name_en", "last_name_en", "latest_submitted_date"
        ])

        # Submitter position
        self._write_csv(f"{output_prefix}_submitter_position.csv", self.submitter_positions, [
            "submitter_id", "nacc_id", "position_period_type_id", "index", "position",
            "position_category_type_id", "workplace", "workplace_location",
            "date_acquiring_type_id", "start_date", "start_month", "start_year",
            "date_ending_type_id", "end_date", "end_month", "end_year",
            "note", "latest_submitted_date"
        ])

        # Spouse old name
        self._write_csv(f"{output_prefix}_spouse_old_name.csv", self.spouse_old_names, [
            "spouse_id", "index", "title", "first_name", "last_name",
            "title_en", "first_name_en", "last_name_en", "submitter_id", "nacc_id",
            "latest_submitted_date"
        ])

        # Spouse position
        self._write_csv(f"{output_prefix}_spouse_position.csv", self.spouse_positions, [
            "spouse_id", "submitter_id", "nacc_id", "position_period_type_id", "index",
            "position", "workplace", "workplace_location", "note", "latest_submitted_date"
        ])

        # Sort summaries by doc_id order from doc_info.csv
        if self.input_doc_order:
            doc_order_map = {doc_id: idx for idx, doc_id in enumerate(self.input_doc_order)}
            self.summaries.sort(key=lambda x: doc_order_map.get(str(x.get('doc_id', '')), 999999))

        # Summary - matching training data format
        self._write_csv(f"{output_prefix}_summary.csv", self.summaries, [
            "id", "doc_id", "nd_title", "nd_first_name", "nd_last_name", "nd_position",
            "submitted_date", "disclosure_announcement_date", "disclosure_start_date",
            "disclosure_end_date", "date_by_submitted_case", "royal_start_date", "agency",
            "submitter_id", "submitter_title", "submitter_first_name", "submitter_last_name",
            "submitter_age", "submitter_marital_status", "submitter_status_date",
            "submitter_status_month", "submitter_status_year", "submitter_sub_district",
            "submitter_district", "submitter_province", "submitter_post_code",
            "submitter_phone_number", "submitter_mobile_number", "submitter_email",
            "spouse_id", "spouse_title", "spouse_first_name", "spouse_last_name",
            "spouse_age", "spouse_status", "spouse_status_date", "spouse_status_month",
            "spouse_status_year", "statement_valuation_submitter_total",
            "statement_valuation_spouse_total", "statement_valuation_child_total",
            "statement_detail_count", "has_statement_detail_note", "asset_count",
            "asset_land_count", "asset_building_count", "asset_vehicle_count",
            "asset_other_count", "asset_total_valuation_amount", "asset_land_valuation_amount",
            "asset_building_valuation_amount", "asset_vehicle_valuation_amount",
            "asset_other_asset_valuation_amount", "asset_valuation_submitter_amount",
            "asset_valuation_spouse_amount", "asset_valuation_child_amount",
            "relative_count", "relative_has_death_flag"
        ])

    def save_json(self, parsed_data: Dict[str, Any], filename: str):
        """Save parsed data as JSON file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved JSON to {filename}")

    def save_to_sqlite(self, db_name: str = "nacc_data.db", input_dir: str = None,
                        enum_dir: str = None, training_dir: str = None,
                        import_external: bool = True):
        """
        Save all data to SQLite database for validation queries

        Args:
            db_name: Name of the SQLite database file
            input_dir: Directory containing input CSV files (Test_*.csv)
            enum_dir: Directory containing enum CSV files
            training_dir: Directory containing training output CSV files
            import_external: Whether to import external CSV files (input, enum, training)
        """
        db_path = os.path.join(self.output_dir, db_name)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        self._create_sqlite_tables(cursor)

        # Insert parsed data into tables
        self._insert_nacc_detail(cursor)
        self._insert_submitter_info(cursor)
        self._insert_spouse_info(cursor)
        self._insert_statement(cursor)
        self._insert_statement_detail(cursor)
        self._insert_asset(cursor)
        self._insert_asset_land_info(cursor)
        self._insert_asset_building_info(cursor)
        self._insert_asset_vehicle_info(cursor)
        self._insert_asset_other_asset_info(cursor)
        self._insert_relative_info(cursor)

        # Import external CSV files if requested
        if import_external:
            print("\n--- Importing External Data ---")
            # Import enum tables (replaces _insert_asset_type)
            self.import_enum_tables(cursor, enum_dir)

            # Import input tables
            self.import_input_tables(cursor, input_dir)

            # Import training data for comparison
            self.import_training_data(cursor, training_dir)
        else:
            # Use built-in asset_type data
            self._insert_asset_type(cursor)

        conn.commit()
        conn.close()
        print(f"\n✓ Saved all data to SQLite database: {db_path}")

    def _create_sqlite_tables(self, cursor):
        """Create all required tables for validation query"""

        # nacc_detail table (main document info)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nacc_detail (
                nacc_id INTEGER PRIMARY KEY,
                doc_id TEXT,
                title TEXT,
                first_name TEXT,
                last_name TEXT,
                position TEXT,
                submitted_case TEXT,
                submitted_date TEXT,
                disclosure_announcement_date TEXT,
                disclosure_start_date TEXT,
                disclosure_end_date TEXT,
                date_by_submitted_case TEXT,
                royal_start_date TEXT,
                submitter_id INTEGER,
                agency TEXT
            )
        ''')

        # submitter_info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submitter_info (
                submitter_id INTEGER PRIMARY KEY,
                nacc_id INTEGER,
                title TEXT,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                status TEXT,
                status_date INTEGER,
                status_month INTEGER,
                status_year INTEGER,
                sub_district TEXT,
                district TEXT,
                province TEXT,
                post_code TEXT,
                phone_number TEXT,
                mobile_number TEXT,
                email TEXT
            )
        ''')

        # spouse_info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spouse_info (
                spouse_id INTEGER PRIMARY KEY,
                nacc_id INTEGER,
                submitter_id INTEGER,
                title TEXT,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                status TEXT,
                status_date INTEGER,
                status_month INTEGER,
                status_year INTEGER
            )
        ''')

        # statement table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nacc_id INTEGER,
                statement_type_id INTEGER,
                valuation_submitter REAL,
                valuation_spouse REAL,
                valuation_child REAL
            )
        ''')

        # statement_detail table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statement_detail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nacc_id INTEGER,
                statement_detail_type_id INTEGER,
                detail TEXT,
                valuation_submitter REAL,
                valuation_spouse REAL,
                valuation_child REAL,
                note TEXT
            )
        ''')

        # asset table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset (
                asset_id INTEGER PRIMARY KEY,
                nacc_id INTEGER,
                submitter_id INTEGER,
                asset_type_id INTEGER,
                asset_name TEXT,
                valuation REAL,
                owner_by_submitter INTEGER,
                owner_by_spouse INTEGER,
                owner_by_child INTEGER
            )
        ''')

        # asset_land_info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_land_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER,
                nacc_id INTEGER,
                land_type TEXT,
                land_number TEXT,
                area_rai REAL,
                area_ngan REAL,
                area_sqwa REAL,
                province TEXT
            )
        ''')

        # asset_building_info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_building_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER,
                nacc_id INTEGER,
                building_type TEXT,
                building_name TEXT,
                room_number TEXT,
                province TEXT
            )
        ''')

        # asset_vehicle_info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_vehicle_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER,
                nacc_id INTEGER,
                vehicle_type TEXT,
                brand TEXT,
                model TEXT,
                registration TEXT,
                province TEXT
            )
        ''')

        # asset_other_asset_info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_other_asset_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER,
                nacc_id INTEGER,
                description TEXT,
                count INTEGER DEFAULT 1
            )
        ''')

        # relative_info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relative_info (
                relative_id INTEGER PRIMARY KEY,
                nacc_id INTEGER,
                submitter_id INTEGER,
                relationship_id INTEGER,
                title TEXT,
                first_name TEXT,
                last_name TEXT,
                age INTEGER,
                is_death INTEGER
            )
        ''')

        # asset_type reference table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_type (
                asset_type_id INTEGER PRIMARY KEY,
                asset_type_name TEXT,
                asset_type_main_type_name TEXT
            )
        ''')

    def _insert_nacc_detail(self, cursor):
        """Insert data into nacc_detail table from summaries"""
        cursor.execute('DELETE FROM nacc_detail')
        for summary in self.summaries:
            cursor.execute('''
                INSERT INTO nacc_detail (nacc_id, doc_id, title, first_name, last_name, position,
                    submitted_case, submitted_date, disclosure_announcement_date, disclosure_start_date,
                    disclosure_end_date, date_by_submitted_case, royal_start_date, submitter_id, agency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                summary.get('id'),
                summary.get('doc_id'),
                summary.get('nd_title'),
                summary.get('nd_first_name'),
                summary.get('nd_last_name'),
                summary.get('nd_position'),
                'ยื่นบัญชี',
                summary.get('submitted_date'),
                summary.get('disclosure_announcement_date'),
                summary.get('disclosure_start_date'),
                summary.get('disclosure_end_date'),
                summary.get('date_by_submitted_case'),
                summary.get('royal_start_date'),
                summary.get('submitter_id'),
                summary.get('agency')
            ))

    def _insert_submitter_info(self, cursor):
        """Insert data into submitter_info table"""
        cursor.execute('DELETE FROM submitter_info')
        for submitter in self.submitter_infos:
            cursor.execute('''
                INSERT INTO submitter_info (submitter_id, nacc_id, title, first_name, last_name,
                    age, status, status_date, status_month, status_year, sub_district, district,
                    province, post_code, phone_number, mobile_number, email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                submitter.get('submitter_id'),
                submitter.get('nacc_id'),
                submitter.get('title'),
                submitter.get('first_name'),
                submitter.get('last_name'),
                submitter.get('age') if submitter.get('age') else None,
                submitter.get('marital_status'),
                submitter.get('status_date') if submitter.get('status_date') else None,
                submitter.get('status_month') if submitter.get('status_month') else None,
                submitter.get('status_year') if submitter.get('status_year') else None,
                submitter.get('sub_district'),
                submitter.get('district'),
                submitter.get('province'),
                submitter.get('post_code'),
                submitter.get('phone_number'),
                submitter.get('mobile_number'),
                submitter.get('email')
            ))

    def _insert_spouse_info(self, cursor):
        """Insert data into spouse_info table"""
        cursor.execute('DELETE FROM spouse_info')
        for spouse in self.spouse_infos:
            cursor.execute('''
                INSERT INTO spouse_info (spouse_id, nacc_id, submitter_id, title, first_name,
                    last_name, age, status, status_date, status_month, status_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                spouse.get('spouse_id'),
                spouse.get('nacc_id'),
                spouse.get('submitter_id'),
                spouse.get('title'),
                spouse.get('first_name'),
                spouse.get('last_name'),
                spouse.get('age') if spouse.get('age') else None,
                spouse.get('status'),
                spouse.get('status_date') if spouse.get('status_date') else None,
                spouse.get('status_month') if spouse.get('status_month') else None,
                spouse.get('status_year') if spouse.get('status_year') else None
            ))

    def _insert_statement(self, cursor):
        """Insert data into statement table"""
        cursor.execute('DELETE FROM statement')
        for stmt in self.statements:
            cursor.execute('''
                INSERT INTO statement (nacc_id, statement_type_id, valuation_submitter,
                    valuation_spouse, valuation_child)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                stmt.get('nacc_id'),
                stmt.get('statement_type_id'),
                stmt.get('valuation_submitter') if stmt.get('valuation_submitter') else None,
                stmt.get('valuation_spouse') if stmt.get('valuation_spouse') else None,
                stmt.get('valuation_child') if stmt.get('valuation_child') else None
            ))

    def _insert_statement_detail(self, cursor):
        """Insert data into statement_detail table"""
        cursor.execute('DELETE FROM statement_detail')
        for detail in self.statement_details:
            cursor.execute('''
                INSERT INTO statement_detail (nacc_id, statement_detail_type_id, detail,
                    valuation_submitter, valuation_spouse, valuation_child, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                detail.get('nacc_id'),
                detail.get('statement_detail_type_id'),
                detail.get('detail'),
                detail.get('valuation_submitter') if detail.get('valuation_submitter') else None,
                detail.get('valuation_spouse') if detail.get('valuation_spouse') else None,
                detail.get('valuation_child') if detail.get('valuation_child') else None,
                detail.get('note')
            ))

    def _insert_asset(self, cursor):
        """Insert data into asset table"""
        cursor.execute('DELETE FROM asset')
        for asset in self.assets:
            owner_submitter = 1 if asset.get('owner_by_submitter') == 'TRUE' else 0
            owner_spouse = 1 if asset.get('owner_by_spouse') == 'TRUE' else 0
            owner_child = 1 if asset.get('owner_by_child') == 'TRUE' else 0
            cursor.execute('''
                INSERT INTO asset (asset_id, nacc_id, submitter_id, asset_type_id, asset_name,
                    valuation, owner_by_submitter, owner_by_spouse, owner_by_child)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asset.get('asset_id'),
                asset.get('nacc_id'),
                asset.get('submitter_id'),
                asset.get('asset_type_id'),
                asset.get('asset_name'),
                asset.get('valuation') if asset.get('valuation') else None,
                owner_submitter,
                owner_spouse,
                owner_child
            ))

    def _insert_asset_land_info(self, cursor):
        """Insert data into asset_land_info table"""
        cursor.execute('DELETE FROM asset_land_info')
        for land in self.asset_land_infos:
            cursor.execute('''
                INSERT INTO asset_land_info (asset_id, nacc_id, land_type, land_number,
                    area_rai, area_ngan, area_sqwa, province)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                land.get('asset_id'),
                land.get('nacc_id'),
                land.get('land_type'),
                land.get('land_number'),
                land.get('area_rai') if land.get('area_rai') else None,
                land.get('area_ngan') if land.get('area_ngan') else None,
                land.get('area_sqwa') if land.get('area_sqwa') else None,
                land.get('province')
            ))

    def _insert_asset_building_info(self, cursor):
        """Insert data into asset_building_info table"""
        cursor.execute('DELETE FROM asset_building_info')
        for building in self.asset_building_infos:
            cursor.execute('''
                INSERT INTO asset_building_info (asset_id, nacc_id, building_type, building_name,
                    room_number, province)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                building.get('asset_id'),
                building.get('nacc_id'),
                building.get('building_type'),
                building.get('building_name'),
                building.get('room_number'),
                building.get('province')
            ))

    def _insert_asset_vehicle_info(self, cursor):
        """Insert data into asset_vehicle_info table"""
        cursor.execute('DELETE FROM asset_vehicle_info')
        for vehicle in self.asset_vehicle_infos:
            cursor.execute('''
                INSERT INTO asset_vehicle_info (asset_id, nacc_id, vehicle_type, brand,
                    model, registration, province)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                vehicle.get('asset_id'),
                vehicle.get('nacc_id'),
                vehicle.get('vehicle_type'),
                vehicle.get('brand'),
                vehicle.get('model'),
                vehicle.get('registration'),
                vehicle.get('province')
            ))

    def _insert_asset_other_asset_info(self, cursor):
        """Insert data into asset_other_asset_info table"""
        cursor.execute('DELETE FROM asset_other_asset_info')
        for other in self.asset_other_infos:
            cursor.execute('''
                INSERT INTO asset_other_asset_info (asset_id, nacc_id, description, count)
                VALUES (?, ?, ?, ?)
            ''', (
                other.get('asset_id'),
                other.get('nacc_id'),
                other.get('description'),
                1
            ))

    def _insert_relative_info(self, cursor):
        """Insert data into relative_info table"""
        cursor.execute('DELETE FROM relative_info')
        for relative in self.relative_infos:
            is_death = 1 if relative.get('is_death') == 'TRUE' else 0
            cursor.execute('''
                INSERT INTO relative_info (relative_id, nacc_id, submitter_id, relationship_id,
                    title, first_name, last_name, age, is_death)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                relative.get('relative_id'),
                relative.get('nacc_id'),
                relative.get('submitter_id'),
                relative.get('relationship_id'),
                relative.get('title'),
                relative.get('first_name'),
                relative.get('last_name'),
                relative.get('age') if relative.get('age') else None,
                is_death
            ))

    def _insert_asset_type(self, cursor):
        """Insert asset_type reference data"""
        cursor.execute('DELETE FROM asset_type')
        asset_types = [
            (1, 'โฉนด', 'ที่ดิน'),
            (2, 'น.ส.3 ก.', 'ที่ดิน'),
            (3, 'น.ส.3', 'ที่ดิน'),
            (4, 'ส.ป.ก.', 'ที่ดิน'),
            (10, 'บ้านเดี่ยว', 'สิ่งปลูกสร้าง'),
            (11, 'อาคารพาณิชย์', 'สิ่งปลูกสร้าง'),
            (13, 'ห้องชุด', 'สิ่งปลูกสร้าง'),
            (37, 'ทาวน์เฮ้าส์', 'สิ่งปลูกสร้าง'),
            (18, 'รถยนต์', 'ยานพาหนะ'),
            (19, 'รถจักรยานยนต์', 'ยานพาหนะ'),
            (20, 'เรือ', 'ยานพาหนะ'),
            (22, 'กรมธรรม์ประกันภัย', 'ทรัพย์สินอื่น'),
            (24, 'สิทธิในสมาชิก', 'ทรัพย์สินอื่น'),
            (25, 'กองทุน', 'ทรัพย์สินอื่น'),
            (28, 'กระเป๋า', 'ทรัพย์สินอื่น'),
            (29, 'ปืน', 'ทรัพย์สินอื่น'),
            (30, 'นาฬิกา', 'ทรัพย์สินอื่น'),
            (31, 'เครื่องประดับ', 'ทรัพย์สินอื่น'),
            (32, 'พระเครื่อง', 'ทรัพย์สินอื่น'),
            (33, 'ทองคำ', 'ทรัพย์สินอื่น'),
            (39, 'อื่นๆ', 'ทรัพย์สินอื่น'),
        ]
        cursor.executemany('''
            INSERT INTO asset_type (asset_type_id, asset_type_name, asset_type_main_type_name)
            VALUES (?, ?, ?)
        ''', asset_types)

    def import_input_tables(self, cursor, input_dir: str = None):
        """
        Import input CSV tables (doc_info, nacc_detail, submitter_info) into SQLite

        Args:
            cursor: SQLite cursor
            input_dir: Directory containing input CSV files
        """
        if input_dir is None:
            input_dir = os.path.join(os.path.dirname(self.output_dir), "test phase 1", "test phase 1 input")

        # Import Test_doc_info.csv
        doc_info_path = os.path.join(input_dir, "Test_doc_info.csv")
        if os.path.exists(doc_info_path):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doc_info (
                    doc_id TEXT PRIMARY KEY,
                    doc_location_url TEXT,
                    type_id INTEGER,
                    nacc_id INTEGER
                )
            ''')
            cursor.execute('DELETE FROM doc_info')
            with open(doc_info_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT INTO doc_info (doc_id, doc_location_url, type_id, nacc_id)
                        VALUES (?, ?, ?, ?)
                    ''', (row.get('doc_id'), row.get('doc_location_url'),
                          row.get('type_id'), row.get('nacc_id')))
            print(f"✓ Imported doc_info from {doc_info_path}")

        # Import Test_nacc_detail.csv (update existing nacc_detail table)
        nacc_detail_path = os.path.join(input_dir, "Test_nacc_detail.csv")
        if os.path.exists(nacc_detail_path):
            with open(nacc_detail_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Update or insert into nacc_detail
                    cursor.execute('''
                        INSERT OR REPLACE INTO nacc_detail
                        (nacc_id, doc_id, title, first_name, last_name, position,
                         submitted_case, submitted_date, disclosure_announcement_date,
                         disclosure_start_date, disclosure_end_date, date_by_submitted_case,
                         royal_start_date, submitter_id, agency)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('nacc_id'),
                        None,  # doc_id from doc_info
                        row.get('title'),
                        row.get('first_name'),
                        row.get('last_name'),
                        row.get('position'),
                        row.get('submitted_case'),
                        row.get('submitted_date'),
                        row.get('disclosure_announcement_date'),
                        row.get('disclosure_start_date'),
                        row.get('disclosure_end_date'),
                        row.get('date_by_submitted_case'),
                        row.get('royal_start_date'),
                        row.get('submitter_id'),
                        row.get('agency')
                    ))
            print(f"✓ Imported nacc_detail from {nacc_detail_path}")

        # Import Test_submitter_info.csv (update existing submitter_info table)
        submitter_info_path = os.path.join(input_dir, "Test_submitter_info.csv")
        if os.path.exists(submitter_info_path):
            with open(submitter_info_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT OR REPLACE INTO submitter_info
                        (submitter_id, nacc_id, title, first_name, last_name,
                         age, status, status_date, status_month, status_year,
                         sub_district, district, province, post_code,
                         phone_number, mobile_number, email)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('submitter_id'),
                        None,  # nacc_id will be linked separately
                        row.get('title'),
                        row.get('first_name'),
                        row.get('last_name'),
                        row.get('age') if row.get('age') else None,
                        row.get('status'),
                        row.get('status_date') if row.get('status_date') else None,
                        row.get('status_month') if row.get('status_month') else None,
                        row.get('status_year') if row.get('status_year') else None,
                        row.get('sub_district'),
                        row.get('district'),
                        row.get('province'),
                        row.get('post_code'),
                        row.get('phone_number'),
                        row.get('mobile_number'),
                        row.get('email')
                    ))
            print(f"✓ Imported submitter_info from {submitter_info_path}")

    def import_enum_tables(self, cursor, enum_dir: str = None):
        """
        Import all enum type CSV files into SQLite

        Args:
            cursor: SQLite cursor
            enum_dir: Directory containing enum CSV files
        """
        if enum_dir is None:
            # Try to find enum_type directory
            base_dir = os.path.dirname(self.output_dir)
            enum_dir = os.path.join(base_dir, "enum_type")
            if not os.path.exists(enum_dir):
                enum_dir = os.path.join(os.path.dirname(base_dir), "enum_type")

        if not os.path.exists(enum_dir):
            print(f"✗ Enum directory not found: {enum_dir}")
            return

        # asset_type.csv
        asset_type_path = os.path.join(enum_dir, "asset_type.csv")
        if os.path.exists(asset_type_path):
            cursor.execute('DROP TABLE IF EXISTS asset_type')
            cursor.execute('''
                CREATE TABLE asset_type (
                    asset_type_id INTEGER PRIMARY KEY,
                    asset_type_main_type_name TEXT,
                    asset_type_sub_type_name TEXT
                )
            ''')
            with open(asset_type_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT INTO asset_type (asset_type_id, asset_type_main_type_name, asset_type_sub_type_name)
                        VALUES (?, ?, ?)
                    ''', (row.get('asset_type_id'), row.get('asset_type_main_type_name'),
                          row.get('asset_type_sub_type_name')))
            print(f"✓ Imported asset_type")

        # relationship.csv
        relationship_path = os.path.join(enum_dir, "relationship.csv")
        if os.path.exists(relationship_path):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS relationship (
                    relationship_id INTEGER PRIMARY KEY,
                    relationship_name TEXT
                )
            ''')
            cursor.execute('DELETE FROM relationship')
            with open(relationship_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT INTO relationship (relationship_id, relationship_name)
                        VALUES (?, ?)
                    ''', (row.get('relationship_id'), row.get('relationship_name')))
            print(f"✓ Imported relationship")

        # statement_type.csv
        statement_type_path = os.path.join(enum_dir, "statement_type.csv")
        if os.path.exists(statement_type_path):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statement_type (
                    statement_type_id INTEGER PRIMARY KEY,
                    statement_type_name TEXT
                )
            ''')
            cursor.execute('DELETE FROM statement_type')
            with open(statement_type_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT INTO statement_type (statement_type_id, statement_type_name)
                        VALUES (?, ?)
                    ''', (row.get('statement_type_id'), row.get('statement_type_name')))
            print(f"✓ Imported statement_type")

        # statement_detail_type.csv
        statement_detail_type_path = os.path.join(enum_dir, "statement_detail_type.csv")
        if os.path.exists(statement_detail_type_path):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statement_detail_type (
                    statement_detail_type_id INTEGER PRIMARY KEY,
                    statement_type_id INTEGER,
                    statement_detail_sub_type_name TEXT
                )
            ''')
            cursor.execute('DELETE FROM statement_detail_type')
            with open(statement_detail_type_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT INTO statement_detail_type (statement_detail_type_id, statement_type_id, statement_detail_sub_type_name)
                        VALUES (?, ?, ?)
                    ''', (row.get('statement_detail_type_id'), row.get('statement_type_id'),
                          row.get('statement_detail_sub_type_name')))
            print(f"✓ Imported statement_detail_type")

        # asset_acquisition_type.csv
        asset_acquisition_type_path = os.path.join(enum_dir, "asset_acquisition_type.csv")
        if os.path.exists(asset_acquisition_type_path):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS asset_acquisition_type (
                    asset_acquisition_type_id INTEGER PRIMARY KEY,
                    asset_acquisition_type_name TEXT
                )
            ''')
            cursor.execute('DELETE FROM asset_acquisition_type')
            with open(asset_acquisition_type_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT INTO asset_acquisition_type (asset_acquisition_type_id, asset_acquisition_type_name)
                        VALUES (?, ?)
                    ''', (row.get('asset_acquisition_type_id'), row.get('asset_acquisition_type_name')))
            print(f"✓ Imported asset_acquisition_type")

        # date_acquiring_type.csv
        date_acquiring_type_path = os.path.join(enum_dir, "date_acquiring_type.csv")
        if os.path.exists(date_acquiring_type_path):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS date_acquiring_type (
                    date_acquiring_type_id INTEGER PRIMARY KEY,
                    date_acquiring_type_name TEXT
                )
            ''')
            cursor.execute('DELETE FROM date_acquiring_type')
            with open(date_acquiring_type_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT INTO date_acquiring_type (date_acquiring_type_id, date_acquiring_type_name)
                        VALUES (?, ?)
                    ''', (row.get('date_acquiring_type_id'), row.get('date_acquiring_type_name')))
            print(f"✓ Imported date_acquiring_type")

        # date_ending_type.csv
        date_ending_type_path = os.path.join(enum_dir, "date_ending_type.csv")
        if os.path.exists(date_ending_type_path):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS date_ending_type (
                    date_ending_type_id INTEGER PRIMARY KEY,
                    date_ending_type_name TEXT
                )
            ''')
            cursor.execute('DELETE FROM date_ending_type')
            with open(date_ending_type_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT INTO date_ending_type (date_ending_type_id, date_ending_type_name)
                        VALUES (?, ?)
                    ''', (row.get('date_ending_type_id'), row.get('date_ending_type_name')))
            print(f"✓ Imported date_ending_type")

        # position_period_type.csv
        position_period_type_path = os.path.join(enum_dir, "position_period_type.csv")
        if os.path.exists(position_period_type_path):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS position_period_type (
                    position_period_type_id INTEGER PRIMARY KEY,
                    position_period_type_name TEXT
                )
            ''')
            cursor.execute('DELETE FROM position_period_type')
            with open(position_period_type_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT INTO position_period_type (position_period_type_id, position_period_type_name)
                        VALUES (?, ?)
                    ''', (row.get('position_period_type_id'), row.get('position_period_type_name')))
            print(f"✓ Imported position_period_type")

        # position_category_type.csv
        position_category_type_path = os.path.join(enum_dir, "position_category_type.csv")
        if os.path.exists(position_category_type_path):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS position_category_type (
                    position_category_id INTEGER PRIMARY KEY,
                    corrupt0_category TEXT,
                    nacc_category_number TEXT,
                    nacc_category TEXT,
                    nacc_sub_category_number TEXT,
                    nacc_sub_category TEXT
                )
            ''')
            cursor.execute('DELETE FROM position_category_type')
            with open(position_category_type_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cursor.execute('''
                        INSERT INTO position_category_type
                        (position_category_id, corrupt0_category, nacc_category_number,
                         nacc_category, nacc_sub_category_number, nacc_sub_category)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (row.get('position_category_id'), row.get('corrupt0_category'),
                          row.get('nacc_category_number'), row.get('nacc_category'),
                          row.get('nacc_sub_category_number'), row.get('nacc_sub_category')))
            print(f"✓ Imported position_category_type")

    def import_training_data(self, cursor, training_dir: str = None):
        """
        Import training output CSV files into SQLite for comparison

        Args:
            cursor: SQLite cursor
            training_dir: Directory containing training output CSV files
        """
        if training_dir is None:
            base_dir = os.path.dirname(self.output_dir)
            training_dir = os.path.join(base_dir, "training", "train output")

        if not os.path.exists(training_dir):
            print(f"✗ Training directory not found: {training_dir}")
            return

        # Create training tables with "train_" prefix
        csv_files = [f for f in os.listdir(training_dir) if f.endswith('.csv')]

        for csv_file in csv_files:
            csv_path = os.path.join(training_dir, csv_file)
            table_name = "train_" + os.path.splitext(csv_file)[0].lower().replace("train_", "")

            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if reader.fieldnames:
                    # Create table dynamically
                    columns = ', '.join([f'"{col}" TEXT' for col in reader.fieldnames])
                    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                    cursor.execute(f'CREATE TABLE "{table_name}" ({columns})')

                    # Insert data
                    placeholders = ', '.join(['?' for _ in reader.fieldnames])
                    for row in reader:
                        values = [row.get(col, '') for col in reader.fieldnames]
                        cursor.execute(f'INSERT INTO "{table_name}" VALUES ({placeholders})', values)

                    print(f"✓ Imported training data: {table_name}")

    def run_validation_query(self, db_name: str = "nacc_data.db", output_csv: str = "validation_summary.csv"):
        """
        Run validation query and export results to CSV

        Args:
            db_name: Name of the SQLite database file
            output_csv: Name of the output CSV file
        """
        db_path = os.path.join(self.output_dir, db_name)
        if not os.path.exists(db_path):
            print(f"✗ Database not found: {db_path}")
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Read and execute validation query
        validation_query = '''
WITH

-- 1) Core NACC Detail (base record)
detail AS (
    SELECT
        nacc_id,
        doc_id,
        title AS nd_title,
        first_name AS nd_first_name,
        last_name AS nd_last_name,
        position AS nd_position,
        submitted_case,
        submitted_date,
        disclosure_announcement_date,
        disclosure_start_date,
        disclosure_end_date,
        date_by_submitted_case,
        royal_start_date,
        submitter_id as ref_id,
        agency
    FROM nacc_detail
),

-- 2) Submitter info (1 row per nacc_id)
submitter AS (
    SELECT
        submitter_id,
        title AS submitter_title,
        first_name AS submitter_first_name,
        last_name AS submitter_last_name,
        age AS submitter_age,
        status AS submitter_marital_status,
        status_date AS submitter_status_date,
        status_month AS submitter_status_month,
        status_year AS submitter_status_year,
        sub_district AS submitter_sub_district,
        district AS submitter_district,
        province AS submitter_province,
        post_code AS submitter_post_code,
        phone_number AS submitter_phone_number,
        mobile_number AS submitter_mobile_number,
        email AS submitter_email
    FROM submitter_info
),

-- 3) Spouse info (0–1 rows per nacc_id)
spouse AS (
    SELECT
        nacc_id,
        spouse_id,
        title AS spouse_title,
        first_name AS spouse_first_name,
        last_name AS spouse_last_name,
        age AS spouse_age,
        status AS spouse_status,
        status_date AS spouse_status_date,
        status_month AS spouse_status_month,
        status_year AS spouse_status_year
    FROM spouse_info
),

-- 4) Statement totals (valuation)
statement_totals AS (
    SELECT
        nacc_id,
        SUM(valuation_submitter) AS statement_valuation_submitter_total,
        SUM(valuation_spouse) AS statement_valuation_spouse_total,
        SUM(valuation_child) AS statement_valuation_child_total
    FROM statement
    GROUP BY nacc_id
),

-- 5) Statement detail aggregates
detail_totals AS (
    SELECT
        nacc_id,
        COUNT(*) AS statement_detail_count,
        MAX(CASE WHEN note IS NULL OR TRIM(note) = '' THEN 0 ELSE 1 END) AS has_statement_detail_note
    FROM statement_detail
    GROUP BY nacc_id
),

-- 6) Asset counts by subtype
asset_counts AS (
    SELECT
        nacc_id,
        COUNT(*) AS asset_count
    FROM asset
    GROUP BY nacc_id
),

asset_land AS (
    SELECT nacc_id, COUNT(*) AS asset_land_count
    FROM asset_land_info
    GROUP BY nacc_id
),

asset_building AS (
    SELECT nacc_id, COUNT(*) AS asset_building_count
    FROM asset_building_info
    GROUP BY nacc_id
),

asset_vehicle AS (
    SELECT nacc_id, COUNT(*) AS asset_vehicle_count
    FROM asset_vehicle_info
    GROUP BY nacc_id
),

asset_other AS (
    SELECT nacc_id, SUM(count) AS asset_other_count
    FROM asset_other_asset_info
    GROUP BY nacc_id
),

-- 7) Asset valuation per type (using asset_type)
asset_val AS (
    SELECT
        a.nacc_id,
        SUM(a.valuation) AS asset_total_valuation_amount,
        SUM(CASE WHEN t.asset_type_main_type_name = 'ที่ดิน'
                 THEN a.valuation ELSE 0 END) AS asset_land_valuation_amount,
        SUM(CASE WHEN t.asset_type_main_type_name = 'สิ่งปลูกสร้าง'
                 THEN a.valuation ELSE 0 END) AS asset_building_valuation_amount,
        SUM(CASE WHEN t.asset_type_main_type_name = 'ยานพาหนะ'
                 THEN a.valuation ELSE 0 END) AS asset_vehicle_valuation_amount,
        SUM(CASE WHEN t.asset_type_main_type_name NOT IN ('ที่ดิน','สิ่งปลูกสร้าง','ยานพาหนะ')
                 THEN a.valuation ELSE 0 END) AS asset_other_asset_valuation_amount,
        SUM(CASE WHEN a.owner_by_submitter THEN a.valuation ELSE 0 END) AS asset_valuation_submitter_amount,
        SUM(CASE WHEN a.owner_by_spouse THEN a.valuation ELSE 0 END) AS asset_valuation_spouse_amount,
        SUM(CASE WHEN a.owner_by_child THEN a.valuation ELSE 0 END) AS asset_valuation_child_amount
    FROM asset a
    LEFT JOIN asset_type t ON a.asset_type_id = t.asset_type_id
    GROUP BY a.nacc_id
),

-- 8) Relatives
rel AS (
    SELECT
        nacc_id,
        COUNT(*) AS relative_count,
        MAX(CASE WHEN is_death THEN 1 ELSE 0 END) AS relative_has_death_flag
    FROM relative_info
    GROUP BY nacc_id
)

-- 9) FINAL SELECT (flattened)
SELECT
    d.nacc_id,
    d.doc_id, d.nd_title, d.nd_first_name, d.nd_last_name, d.nd_position, d.submitted_date,
    d.disclosure_announcement_date, d.disclosure_start_date, d.disclosure_end_date,
    d.date_by_submitted_case, d.royal_start_date, d.agency,
    s.submitter_id, s.submitter_title, s.submitter_first_name, s.submitter_last_name,
    s.submitter_age, s.submitter_marital_status,
    s.submitter_status_date, s.submitter_status_month, s.submitter_status_year,
    s.submitter_sub_district, s.submitter_district, s.submitter_province, s.submitter_post_code,
    s.submitter_phone_number, s.submitter_mobile_number, s.submitter_email,
    sp.spouse_id, sp.spouse_title, sp.spouse_first_name, sp.spouse_last_name,
    sp.spouse_age, sp.spouse_status, sp.spouse_status_date, sp.spouse_status_month, sp.spouse_status_year,
    st.statement_valuation_submitter_total,
    st.statement_valuation_spouse_total,
    st.statement_valuation_child_total,
    dt.statement_detail_count,
    dt.has_statement_detail_note,
    ac.asset_count,
    al.asset_land_count,
    ab.asset_building_count,
    av.asset_vehicle_count,
    ao.asset_other_count,
    avl.asset_total_valuation_amount,
    avl.asset_land_valuation_amount,
    avl.asset_building_valuation_amount,
    avl.asset_vehicle_valuation_amount,
    avl.asset_other_asset_valuation_amount,
    avl.asset_valuation_submitter_amount,
    avl.asset_valuation_spouse_amount,
    avl.asset_valuation_child_amount,
    r.relative_count,
    r.relative_has_death_flag

FROM detail d
LEFT JOIN submitter s ON d.ref_id = s.submitter_id
LEFT JOIN spouse sp ON d.nacc_id = sp.nacc_id
LEFT JOIN statement_totals st ON d.nacc_id = st.nacc_id
LEFT JOIN detail_totals dt ON d.nacc_id = dt.nacc_id
LEFT JOIN asset_counts ac ON d.nacc_id = ac.nacc_id
LEFT JOIN asset_land al ON d.nacc_id = al.nacc_id
LEFT JOIN asset_building ab ON d.nacc_id = ab.nacc_id
LEFT JOIN asset_vehicle av ON d.nacc_id = av.nacc_id
LEFT JOIN asset_other ao ON d.nacc_id = ao.nacc_id
LEFT JOIN asset_val avl ON d.nacc_id = avl.nacc_id
LEFT JOIN rel r ON d.nacc_id = r.nacc_id

ORDER BY d.nacc_id
        '''

        cursor.execute(validation_query)
        rows = cursor.fetchall()

        if rows:
            # Get column names
            columns = [description[0] for description in cursor.description]

            # Write to CSV
            output_path = os.path.join(self.output_dir, output_csv)
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in rows:
                    writer.writerow(list(row))

            print(f"✓ Validation query exported to: {output_path}")
            print(f"  Total records: {len(rows)}")
        else:
            print("✗ No data returned from validation query")

        conn.close()


def test_converter():
    """Test the JSON to CSV converter"""
    converter = JSONToCSVConverter("./test_output")

    # Test data
    test_data = {
        "doc_id": "TEST001",
        "nacc_id": 999,
        "extraction_status": "success",
        "confidence_score": 0.95,
        "submitter_info": {
            "title": "นาย",
            "first_name": "ทดสอบ",
            "last_name": "ตัวอย่าง",
            "age": 45,
            "marital_status": "สมรส",
            "position": "สมาชิกสภาผู้แทนราษฎร",
            "province": "กรุงเทพมหานคร"
        },
        "spouse_info": {
            "title": "นาง",
            "first_name": "ทดสอบ",
            "last_name": "ตัวอย่าง",
            "age": 42
        },
        "relatives": [
            {
                "index": 1,
                "relationship_id": 4,
                "title": "นาย",
                "first_name": "บุตร",
                "last_name": "ตัวอย่าง",
                "age": 20,
                "is_death": False
            }
        ],
        "statements": [
            {"statement_type_id": 1, "valuation_submitter": 1000000, "valuation_spouse": 500000}
        ],
        "assets": [
            {
                "index": 1,
                "asset_type_id": 1,
                "asset_name": "โฉนด",
                "valuation": 5000000,
                "owner_by_submitter": True,
                "owner_by_spouse": False,
                "owner_by_child": False
            }
        ]
    }

    converter.process_document(test_data)
    converter.save_all_csv()
    converter.save_json(test_data, "test_output.json")


if __name__ == "__main__":
    test_converter()
