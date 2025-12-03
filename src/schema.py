# -*- coding: utf-8 -*-
"""
Schema definitions and Enum types for NACC document parsing
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# ==================== ENUM TYPES ====================

class StatementType(IntEnum):
    """ประเภทงบการเงิน"""
    CASH_SECURITIES = 1      # เงินสด หลักทรัพย์ และสิทธิ
    DEPOSIT = 2              # เงินฝาก
    LOAN = 3                 # เงินให้กู้ยืม
    LAND_BUILDING = 4        # ที่ดิน โรงเรือน และสิ่งปลูกสร้าง
    LIABILITY = 5            # หนี้สิน


class AssetType(IntEnum):
    """ประเภททรัพย์สิน"""
    LAND_CHANOTE = 1         # ที่ดิน (โฉนด)
    LAND_NS3K = 2            # น.ส.3 ก.
    LAND_NS3 = 3             # น.ส.3
    LAND_SPK = 4             # ส.ป.ก.
    HOUSE_SINGLE = 10        # บ้านเดี่ยว
    COMMERCIAL_BUILDING = 11 # อาคารพาณิชย์
    CONDO = 13               # ห้องชุด
    CAR = 18                 # รถยนต์
    MOTORCYCLE = 19          # รถจักรยานยนต์
    BOAT = 20                # เรือ
    INSURANCE_POLICY = 22    # กรมธรรม์ประกันภัย
    MEMBERSHIP = 24          # สิทธิในสมาชิก
    FUND = 25                # กองทุน
    BAG = 28                 # กระเป๋า
    GUN = 29                 # ปืน
    WATCH = 30               # นาฬิกา
    JEWELRY = 31             # เครื่องประดับ/อัญมณี
    AMULET = 32              # พระเครื่อง
    GOLD = 33                # ทองคำ
    TOWNHOUSE = 37           # ทาวน์เฮ้าส์
    OTHER = 39               # อื่นๆ


class RelationshipType(IntEnum):
    """ความสัมพันธ์"""
    FATHER = 1               # บิดา
    MOTHER = 2               # มารดา
    SIBLING = 3              # พี่น้อง
    CHILD = 4                # บุตร
    SPOUSE_FATHER = 5        # บิดาของคู่สมรส
    SPOUSE_MOTHER = 6        # มารดาของคู่สมรส


class DateAcquiringType(IntEnum):
    """ประเภทวันที่ได้มา"""
    EXACT_DATE = 1           # ระบุวันที่แน่นอน
    BEFORE = 2               # ไม่ระบุวันที่ (ได้มาก่อน)
    UNKNOWN = 3              # ไม่ทราบ
    NO_END = 4               # ไม่มีวันสิ้นสุด


class AssetAcquisitionType(IntEnum):
    """วิธีการได้มาของทรัพย์สิน"""
    PURCHASE = 1             # ซื้อ
    INHERITANCE = 2          # มรดก
    GIFT = 3                 # รับให้
    ASSESSED = 4             # ประเมินราคา
    MARKET_VALUE = 5         # ราคาตลาด
    ACQUISITION_COST = 6     # ราคาที่ได้มา


class StatementDetailType(IntEnum):
    """ประเภทรายละเอียดงบการเงิน"""
    REGULAR_INCOME = 1       # รายได้ประจำ
    ASSET_INCOME = 2         # รายได้จากทรัพย์สิน
    SALE_INHERITANCE = 3     # รายได้จากการขายทรัพย์สิน/มรดก
    OTHER_INCOME = 5         # รายได้อื่น
    REGULAR_EXPENSE = 6      # รายจ่ายประจำ
    OTHER_EXPENSE = 7        # รายจ่ายอื่น
    CASH = 8                 # เงินสด
    DEPOSIT = 9              # เงินฝาก
    INVESTMENT = 10          # เงินลงทุน
    LOAN_GIVEN = 11          # เงินให้กู้ยืม
    LAND = 12                # ที่ดิน
    BUILDING = 13            # โรงเรือนและสิ่งปลูกสร้าง
    VEHICLE = 14             # ยานพาหนะ
    RIGHTS = 15              # สิทธิและสัมปทาน
    OTHER_ASSET = 16         # ทรัพย์สินอื่น
    OVERDRAFT = 17           # เงินเบิกเกินบัญชี
    BANK_LOAN = 18           # เงินกู้ธนาคาร
    DOCUMENTED_DEBT = 19     # หนี้สินที่มีหลักฐาน
    OTHER_DEBT = 20          # หนี้สินอื่น


class MaritalStatus:
    """สถานะการสมรส"""
    MARRIED = "สมรส"
    SINGLE = "โสด"
    DIVORCED = "หย่า"
    WIDOWED = "คู่สมรสเสียชีวิต"
    COHABITING = "อยู่กินกันฉันสามีภริยาตามที่คณะกรรมการ ป.ป.ช. กำหนด"


# ==================== ENUM MAPPINGS FOR LLM ====================

ASSET_TYPE_MAPPING = {
    "โฉนด": 1,
    "ที่ดิน": 1,
    "น.ส.3 ก.": 2,
    "น.ส.3": 3,
    "ส.ป.ก.": 4,
    "บ้านเดี่ยว": 10,
    "บ้านพัก": 10,
    "บ้านพักอาศัย": 10,
    "อาคารพาณิชย์": 11,
    "ห้องชุด": 13,
    "คอนโด": 13,
    "เพนท์เฮ้าส์": 13,
    "รถยนต์": 18,
    "รถจักรยานยนต์": 19,
    "มอเตอร์ไซค์": 19,
    "เรือ": 20,
    "กรมธรรม์": 22,
    "ประกันภัย": 22,
    "ประกันชีวิต": 22,
    "สิทธิในสมาชิก": 24,
    "สมาชิก": 24,
    "กองทุน": 25,
    "กระเป๋า": 28,
    "ปืน": 29,
    "อาวุธปืน": 29,
    "นาฬิกา": 30,
    "แหวน": 31,
    "สร้อย": 31,
    "กำไล": 31,
    "ต่างหู": 31,
    "เพชร": 31,
    "เครื่องประดับ": 31,
    "อัญมณี": 31,
    "พระเครื่อง": 32,
    "พระ": 32,
    "เหรียญพระ": 32,
    "ทองคำ": 33,
    "ทอง": 33,
    "ทาวน์เฮ้าส์": 37,
    "ทาวน์โฮม": 37,
}


# ==================== JSON SCHEMA ====================

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "doc_id": {"type": "string"},
        "nacc_id": {"type": "integer"},
        "extraction_status": {"type": "string", "enum": ["success", "partial", "failed"]},
        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},

        "submitter_info": {
            "type": "object",
            "properties": {
                "title": {"type": ["string", "null"]},
                "first_name": {"type": ["string", "null"]},
                "last_name": {"type": ["string", "null"]},
                "age": {"type": ["integer", "null"]},
                "marital_status": {"type": ["string", "null"]},
                "status_date": {"type": ["integer", "null"]},
                "status_month": {"type": ["integer", "null"]},
                "status_year": {"type": ["integer", "null"]},
                "sub_district": {"type": ["string", "null"]},
                "district": {"type": ["string", "null"]},
                "province": {"type": ["string", "null"]},
                "post_code": {"type": ["string", "null"]},
                "positions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "position_period_type_id": {"type": ["integer", "null"]},
                            "index": {"type": ["integer", "null"]},
                            "position": {"type": ["string", "null"]},
                            "position_category_type_id": {"type": ["integer", "null"]},
                            "workplace": {"type": ["string", "null"]},
                            "workplace_location": {"type": ["string", "null"]},
                            "date_acquiring_type_id": {"type": ["integer", "null"]},
                            "start_date": {"type": ["integer", "null"]},
                            "start_month": {"type": ["integer", "null"]},
                            "start_year": {"type": ["integer", "null"]},
                            "date_ending_type_id": {"type": ["integer", "null"]},
                            "end_date": {"type": ["integer", "null"]},
                            "end_month": {"type": ["integer", "null"]},
                            "end_year": {"type": ["integer", "null"]},
                            "note": {"type": ["string", "null"]}
                        }
                    }
                },
                "old_names": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "index": {"type": ["integer", "null"]},
                            "title": {"type": ["string", "null"]},
                            "first_name": {"type": ["string", "null"]},
                            "last_name": {"type": ["string", "null"]},
                            "title_en": {"type": ["string", "null"]},
                            "first_name_en": {"type": ["string", "null"]},
                            "last_name_en": {"type": ["string", "null"]}
                        }
                    }
                }
            }
        },

        "spouse_info": {
            "type": ["object", "null"],
            "properties": {
                "title": {"type": ["string", "null"]},
                "first_name": {"type": ["string", "null"]},
                "last_name": {"type": ["string", "null"]},
                "age": {"type": ["integer", "null"]},
                "status": {"type": ["string", "null"]},
                "status_date": {"type": ["integer", "null"]},
                "status_month": {"type": ["integer", "null"]},
                "status_year": {"type": ["integer", "null"]},
                "sub_district": {"type": ["string", "null"]},
                "district": {"type": ["string", "null"]},
                "province": {"type": ["string", "null"]},
                "post_code": {"type": ["string", "null"]},
                "positions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "position_period_type_id": {"type": ["integer", "null"]},
                            "index": {"type": ["integer", "null"]},
                            "position": {"type": ["string", "null"]},
                            "workplace": {"type": ["string", "null"]},
                            "workplace_location": {"type": ["string", "null"]},
                            "note": {"type": ["string", "null"]}
                        }
                    }
                },
                "old_names": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "index": {"type": ["integer", "null"]},
                            "title": {"type": ["string", "null"]},
                            "first_name": {"type": ["string", "null"]},
                            "last_name": {"type": ["string", "null"]},
                            "title_en": {"type": ["string", "null"]},
                            "first_name_en": {"type": ["string", "null"]},
                            "last_name_en": {"type": ["string", "null"]}
                        }
                    }
                }
            }
        },

        "relatives": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "relationship_id": {"type": "integer", "minimum": 1, "maximum": 6},
                    "title": {"type": ["string", "null"]},
                    "first_name": {"type": ["string", "null"]},
                    "last_name": {"type": ["string", "null"]},
                    "age": {"type": ["integer", "null"]},
                    "address": {"type": ["string", "null"]},
                    "occupation": {"type": ["string", "null"]},
                    "school": {"type": ["string", "null"]},
                    "workplace": {"type": ["string", "null"]},
                    "workplace_location": {"type": ["string", "null"]},
                    "is_death": {"type": "boolean"}
                }
            }
        },

        "statements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "statement_type_id": {"type": "integer", "minimum": 1, "maximum": 5},
                    "valuation_submitter": {"type": ["number", "null"]},
                    "valuation_spouse": {"type": ["number", "null"]},
                    "valuation_child": {"type": ["number", "null"]}
                }
            }
        },

        "statement_details": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "statement_detail_type_id": {"type": "integer"},
                    "index": {"type": "integer"},
                    "detail": {"type": ["string", "null"]},
                    "valuation_submitter": {"type": ["number", "null"]},
                    "valuation_spouse": {"type": ["number", "null"]},
                    "valuation_child": {"type": ["number", "null"]},
                    "note": {"type": ["string", "null"]}
                }
            }
        },

        "assets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "asset_type_id": {"type": "integer"},
                    "asset_type_other": {"type": ["string", "null"]},
                    "asset_name": {"type": ["string", "null"]},
                    "date_acquiring_type_id": {"type": ["integer", "null"]},
                    "acquiring_date": {"type": ["integer", "null"]},
                    "acquiring_month": {"type": ["integer", "null"]},
                    "acquiring_year": {"type": ["integer", "null"]},
                    "date_ending_type_id": {"type": ["integer", "null"]},
                    "ending_date": {"type": ["integer", "null"]},
                    "ending_month": {"type": ["integer", "null"]},
                    "ending_year": {"type": ["integer", "null"]},
                    "asset_acquisition_type_id": {"type": ["integer", "null"]},
                    "valuation": {"type": ["number", "null"]},
                    "owner_by_submitter": {"type": "boolean"},
                    "owner_by_spouse": {"type": "boolean"},
                    "owner_by_child": {"type": "boolean"}
                }
            }
        }
    },
    "required": ["doc_id", "nacc_id", "extraction_status"]
}
