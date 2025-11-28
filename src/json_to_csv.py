# -*- coding: utf-8 -*-
"""
JSON to CSV Converter for NACC Document Data
Converts parsed JSON data to CSV format matching training output structure
"""

import os
import csv
import json
from typing import Dict, Any, List, Optional
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

    def _safe_get(self, data: dict, key: str, default=None):
        """Safely get value from dict"""
        return data.get(key, default) if data else default

    def _format_date(self, date_str: str) -> str:
        """Format date string"""
        if not date_str:
            return ""
        return date_str

    def process_document(self, parsed_data: Dict[str, Any], submitter_id: int = None) -> int:
        """
        Process a single parsed document and add to data containers

        Args:
            parsed_data: Parsed JSON data from LLM
            submitter_id: Optional submitter ID, auto-generated if not provided

        Returns:
            submitter_id used
        """
        if submitter_id is None:
            submitter_id = self.submitter_id_counter
            self.submitter_id_counter += 1

        doc_id = parsed_data.get("doc_id", "")
        nacc_id = parsed_data.get("nacc_id", 0)

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

        # Process position
        position = self._safe_get(submitter, "position", "")
        agency = self._safe_get(submitter, "agency", "")
        if position:
            self.submitter_positions.append({
                "submitter_id": submitter_id,
                "nacc_id": nacc_id,
                "position": position,
                "agency": agency,
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

            # Process land info
            if asset_type_id in [1, 2, 3, 4]:
                land_info = self._safe_get(asset, "land_info", {})
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

            # Process building info
            if asset_type_id in [10, 11, 13, 37]:
                building_info = self._safe_get(asset, "building_info", {})
                self.asset_building_infos.append({
                    "asset_id": asset_id,
                    "nacc_id": nacc_id,
                    "building_type": self._safe_get(building_info, "building_type", ""),
                    "building_name": self._safe_get(building_info, "building_name", ""),
                    "room_number": self._safe_get(building_info, "room_number", ""),
                    "province": self._safe_get(building_info, "province", ""),
                    "latest_submitted_date": today
                })

            # Process vehicle info
            if asset_type_id in [18, 19, 20]:
                vehicle_info = self._safe_get(asset, "vehicle_info", {})
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
        """Generate summary record"""
        submitter = data.get("submitter_info", {})
        spouse = data.get("spouse_info", {})
        today = datetime.now().strftime("%Y-%m-%d")

        # Calculate totals
        statements = data.get("statements", [])
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

        self.summaries.append({
            "id": nacc_id,
            "doc_id": doc_id,
            "nd_title": self._safe_get(submitter, "title", ""),
            "nd_first_name": self._safe_get(submitter, "first_name", ""),
            "nd_last_name": self._safe_get(submitter, "last_name", ""),
            "nd_position": self._safe_get(submitter, "position", ""),
            "submitter_id": submitter_id,
            "submitter_title": self._safe_get(submitter, "title", ""),
            "submitter_first_name": self._safe_get(submitter, "first_name", ""),
            "submitter_last_name": self._safe_get(submitter, "last_name", ""),
            "submitter_age": self._safe_get(submitter, "age", ""),
            "submitter_marital_status": self._safe_get(submitter, "marital_status", ""),
            "submitter_province": self._safe_get(submitter, "province", ""),
            "spouse_title": self._safe_get(spouse, "title", "") if spouse else "",
            "spouse_first_name": self._safe_get(spouse, "first_name", "") if spouse else "",
            "spouse_last_name": self._safe_get(spouse, "last_name", "") if spouse else "",
            "spouse_age": self._safe_get(spouse, "age", "") if spouse else "",
            "statement_valuation_submitter_total": total_valuation_submitter,
            "statement_valuation_spouse_total": total_valuation_spouse,
            "statement_valuation_child_total": total_valuation_child,
            "asset_count": len(assets),
            "relative_count": len(relatives),
            "extraction_status": data.get("extraction_status", ""),
            "confidence_score": data.get("confidence_score", 0),
            "latest_submitted_date": today
        })

    def _write_csv(self, filename: str, data: List[Dict], fieldnames: List[str]):
        """Write data to CSV file"""
        if not data:
            return

        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                # Only include fields that exist in fieldnames
                filtered_row = {k: v for k, v in row.items() if k in fieldnames}
                writer.writerow(filtered_row)

        print(f"✓ Written {len(data)} records to {filename}")

    def save_all_csv(self):
        """Save all data to CSV files"""
        # Statement
        self._write_csv("Output_statement.csv", self.statements, [
            "nacc_id", "statement_type_id", "valuation_submitter", "submitter_id",
            "valuation_spouse", "valuation_child", "latest_submitted_date"
        ])

        # Statement details
        self._write_csv("Output_statement_detail.csv", self.statement_details, [
            "nacc_id", "submitter_id", "statement_detail_type_id", "index",
            "detail", "valuation_submitter", "valuation_spouse", "valuation_child",
            "note", "latest_submitted_date"
        ])

        # Assets
        self._write_csv("Output_asset.csv", self.assets, [
            "asset_id", "submitter_id", "nacc_id", "index", "asset_type_id",
            "asset_type_other", "asset_name", "date_acquiring_type_id",
            "acquiring_date", "acquiring_month", "acquiring_year",
            "date_ending_type_id", "ending_date", "ending_month", "ending_year",
            "asset_acquisition_type_id", "valuation",
            "owner_by_submitter", "owner_by_spouse", "owner_by_child",
            "latest_submitted_date"
        ])

        # Asset land info
        self._write_csv("Output_asset_land_info.csv", self.asset_land_infos, [
            "asset_id", "nacc_id", "land_type", "land_number",
            "area_rai", "area_ngan", "area_sqwa", "province", "latest_submitted_date"
        ])

        # Asset building info
        self._write_csv("Output_asset_building_info.csv", self.asset_building_infos, [
            "asset_id", "nacc_id", "building_type", "building_name",
            "room_number", "province", "latest_submitted_date"
        ])

        # Asset vehicle info
        self._write_csv("Output_asset_vehicle_info.csv", self.asset_vehicle_infos, [
            "asset_id", "nacc_id", "vehicle_type", "brand", "model",
            "registration", "province", "latest_submitted_date"
        ])

        # Asset other info
        self._write_csv("Output_asset_other_asset_info.csv", self.asset_other_infos, [
            "asset_id", "nacc_id", "description", "latest_submitted_date"
        ])

        # Relative info
        self._write_csv("Output_relative_info.csv", self.relative_infos, [
            "relative_id", "submitter_id", "nacc_id", "index", "relationship_id",
            "title", "first_name", "last_name", "age", "address", "occupation",
            "school", "workplace", "workplace_location", "latest_submitted_date", "is_death"
        ])

        # Spouse info
        self._write_csv("Output_spouse_info.csv", self.spouse_infos, [
            "spouse_id", "submitter_id", "nacc_id", "title", "first_name", "last_name",
            "title_en", "first_name_en", "last_name_en", "age", "status",
            "status_date", "status_month", "status_year", "sub_district", "district",
            "province", "post_code", "phone_number", "mobile_number", "email",
            "latest_submitted_date"
        ])

        # Summary
        self._write_csv("Output_summary.csv", self.summaries, [
            "id", "doc_id", "nd_title", "nd_first_name", "nd_last_name", "nd_position",
            "submitter_id", "submitter_title", "submitter_first_name", "submitter_last_name",
            "submitter_age", "submitter_marital_status", "submitter_province",
            "spouse_title", "spouse_first_name", "spouse_last_name", "spouse_age",
            "statement_valuation_submitter_total", "statement_valuation_spouse_total",
            "statement_valuation_child_total", "asset_count", "relative_count",
            "extraction_status", "confidence_score", "latest_submitted_date"
        ])

    def save_json(self, parsed_data: Dict[str, Any], filename: str):
        """Save parsed data as JSON file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved JSON to {filename}")


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
