"""
Enum Types Loader - โหลดและจัดการ enum types จาก CSV files
"""

import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path


class EnumTypes:
    """
    โหลดและจัดการ enum types ทั้งหมด
    """
    
    def __init__(self, enum_dir: str = "/mnt/user-data/uploads"):
        self.enum_dir = Path(enum_dir)
        
        # โหลด enum types ทั้งหมด
        self.asset_acquisition_types = self._load_asset_acquisition_types()
        self.asset_types = self._load_asset_types()
        self.date_acquiring_types = self._load_date_acquiring_types()
        self.date_ending_types = self._load_date_ending_types()
        self.position_category_types = self._load_position_category_types()
        self.position_period_types = self._load_position_period_types()
        self.relationships = self._load_relationships()
        self.statement_detail_types = self._load_statement_detail_types()
        self.statement_types = self._load_statement_types()
    
    def _load_asset_acquisition_types(self) -> Dict[int, str]:
        """วิธีการได้มาของทรัพย์สิน"""
        df = pd.read_csv(self.enum_dir / "asset_acquisition_type.csv")
        return dict(zip(
            df['asset_acquisition_type_id'], 
            df['asset_acquisition_type_name']
        ))
    
    def _load_asset_types(self) -> pd.DataFrame:
        """ประเภททรัพย์สิน (มีทั้ง main และ sub type)"""
        df = pd.read_csv(self.enum_dir / "asset_type.csv")
        return df
    
    def _load_date_acquiring_types(self) -> Dict[int, str]:
        """ประเภทวันที่ได้มา"""
        df = pd.read_csv(self.enum_dir / "date_acquiring_type.csv")
        return dict(zip(
            df['date_acquiring_type_id'],
            df['date_acquiring_type_name']
        ))
    
    def _load_date_ending_types(self) -> Dict[int, str]:
        """ประเภทวันที่สิ้นสุด"""
        df = pd.read_csv(self.enum_dir / "date_ending_type.csv")
        return dict(zip(
            df['date_ending_type_id'],
            df['date_ending_type_name']
        ))
    
    def _load_position_category_types(self) -> pd.DataFrame:
        """ประเภทตำแหน่ง (มีหลายระดับ)"""
        df = pd.read_csv(self.enum_dir / "position_category_type.csv")
        return df
    
    def _load_position_period_types(self) -> Dict[int, str]:
        """ช่วงเวลาตำแหน่ง"""
        df = pd.read_csv(self.enum_dir / "position_period_type.csv")
        return dict(zip(
            df['position_period_type_id'],
            df['position_period_type_name']
        ))
    
    def _load_relationships(self) -> Dict[int, str]:
        """ความสัมพันธ์กับผู้ยื่น"""
        df = pd.read_csv(self.enum_dir / "relationship.csv")
        return dict(zip(
            df['relationship_id'],
            df['relationship_name']
        ))
    
    def _load_statement_detail_types(self) -> pd.DataFrame:
        """ประเภทรายละเอียดรายการ"""
        df = pd.read_csv(self.enum_dir / "statement_detail_type.csv")
        return df
    
    def _load_statement_types(self) -> Dict[int, str]:
        """ประเภทรายการหลัก"""
        df = pd.read_csv(self.enum_dir / "statement_type.csv")
        return dict(zip(
            df['statement_type_id'],
            df['statement_type_name']
        ))
    
    # ============================================
    # Helper Methods - ช่วยหา ID จากชื่อ
    # ============================================
    
    def get_asset_acquisition_id(self, name: str) -> Optional[int]:
        """หา asset_acquisition_type_id จากชื่อ"""
        for id, type_name in self.asset_acquisition_types.items():
            if name and type_name in name or name in type_name:
                return id
        return 6  # default: ไม่ได้ระบุในเอกสาร
    
    def get_asset_type_id(self, main_type: str, sub_type: str = None) -> Optional[int]:
        """
        หา asset_type_id จากชื่อประเภท
        เช่น: main_type="ที่ดิน", sub_type="โฉนด" -> 1
        """
        df = self.asset_types
        
        # Filter by main type
        if main_type:
            df = df[df['asset_type_main_type_name'].str.contains(main_type, na=False)]
        
        # Filter by sub type
        if sub_type:
            df = df[df['asset_type_sub_type_name'].str.contains(sub_type, na=False)]
        
        if len(df) > 0:
            return int(df.iloc[0]['asset_type_id'])
        
        return None
    
    def get_position_category_id(self, position_name: str) -> Optional[int]:
        """หา position_category_id จากชื่อตำแหน่ง"""
        df = self.position_category_types
        
        # ลองหาจาก nacc_sub_category ก่อน
        match = df[df['nacc_sub_category'].str.contains(position_name, na=False, case=False)]
        if len(match) > 0:
            return int(match.iloc[0]['position_category_id'])
        
        # ลองหาจาก nacc_category
        match = df[df['nacc_category'].str.contains(position_name, na=False, case=False)]
        if len(match) > 0:
            return int(match.iloc[0]['position_category_id'])
        
        # ตรวจสอบจาก keywords
        if 'ส.ส.' in position_name or 'สมาชิกสภาผู้แทนราษฎร' in position_name:
            return 4
        elif 'ส.ว.' in position_name or 'สมาชิกวุฒิสภา' in position_name:
            return 5
        elif 'รัฐมนตรี' in position_name:
            return 3
        elif 'นายกรัฐมนตรี' in position_name:
            return 2
        
        return None
    
    def get_relationship_id(self, relationship_name: str) -> Optional[int]:
        """หา relationship_id จากชื่อ"""
        for id, name in self.relationships.items():
            if relationship_name and name in relationship_name:
                return id
        return None
    
    def get_statement_type_id(self, statement_name: str) -> Optional[int]:
        """หา statement_type_id จากชื่อ"""
        for id, name in self.statement_types.items():
            if statement_name and name in statement_name:
                return id
        return None
    
    # ============================================
    # Generate Prompt Context
    # ============================================
    
    def get_asset_acquisition_prompt_context(self) -> str:
        """สร้าง context สำหรับ LLM prompt"""
        lines = ["วิธีการได้มาของทรัพย์สิน (asset_acquisition_type):"]
        for id, name in self.asset_acquisition_types.items():
            lines.append(f"  {id} = {name}")
        return '\n'.join(lines)
    
    def get_asset_type_prompt_context(self) -> str:
        """สร้าง context สำหรับ LLM prompt"""
        lines = ["ประเภททรัพย์สิน (asset_type):"]
        
        # จัดกลุ่มตาม main type
        grouped = self.asset_types.groupby('asset_type_main_type_name')
        
        for main_type, group in grouped:
            lines.append(f"\n{main_type}:")
            for _, row in group.iterrows():
                lines.append(f"  {row['asset_type_id']} = {row['asset_type_sub_type_name']}")
        
        return '\n'.join(lines)
    
    def get_position_category_prompt_context(self) -> str:
        """สร้าง context สำหรับ LLM prompt"""
        lines = ["ประเภทตำแหน่ง (position_category):"]
        
        df = self.position_category_types
        for _, row in df.iterrows():
            lines.append(
                f"  {row['position_category_id']} = {row['nacc_sub_category']} "
                f"({row['nacc_category']})"
            )
        
        return '\n'.join(lines)
    
    def get_relationship_prompt_context(self) -> str:
        """สร้าง context สำหรับ LLM prompt"""
        lines = ["ความสัมพันธ์ (relationship):"]
        for id, name in self.relationships.items():
            lines.append(f"  {id} = {name}")
        return '\n'.join(lines)
    
    def get_position_period_prompt_context(self) -> str:
        """สร้าง context สำหรับ LLM prompt"""
        lines = ["ช่วงเวลาตำแหน่ง (position_period):"]
        for id, name in self.position_period_types.items():
            lines.append(f"  {id} = {name}")
        return '\n'.join(lines)
    
    def get_date_acquiring_prompt_context(self) -> str:
        """สร้าง context สำหรับ LLM prompt"""
        lines = ["ประเภทวันที่ได้มา (date_acquiring_type):"]
        for id, name in self.date_acquiring_types.items():
            lines.append(f"  {id} = {name}")
        return '\n'.join(lines)
    
    def get_all_enum_context_for_llm(self) -> str:
        """รวม context ทั้งหมดสำหรับ LLM"""
        contexts = [
            "=" * 60,
            "ENUM TYPES REFERENCE",
            "=" * 60,
            "",
            self.get_asset_acquisition_prompt_context(),
            "",
            self.get_asset_type_prompt_context(),
            "",
            self.get_position_category_prompt_context(),
            "",
            self.get_position_period_prompt_context(),
            "",
            self.get_relationship_prompt_context(),
            "",
            self.get_date_acquiring_prompt_context(),
            "",
            "=" * 60,
        ]
        return '\n'.join(contexts)


# ============================================
# Singleton Instance
# ============================================

_enum_types_instance = None

def get_enum_types() -> EnumTypes:
    """Get singleton instance of EnumTypes"""
    global _enum_types_instance
    if _enum_types_instance is None:
        _enum_types_instance = EnumTypes("./enum_type")
    return _enum_types_instance


# ============================================
# Usage Examples
# ============================================

if __name__ == "__main__":
    enums = get_enum_types()
    
    # แสดง enum types ทั้งหมด
    print("=" * 60)
    print("ENUM TYPES LOADED")
    print("=" * 60)
    
    print("\n1. Asset Acquisition Types:")
    print(enums.asset_acquisition_types)
    
    print("\n2. Asset Types (first 5):")
    print(enums.asset_types.head())
    
    print("\n3. Position Categories (first 5):")
    print(enums.position_category_types.head())
    
    print("\n4. Relationships:")
    print(enums.relationships)
    
    # ทดสอบการหา ID จากชื่อ
    print("\n" + "=" * 60)
    print("FINDING IDS")
    print("=" * 60)
    
    print(f"\n'ซื้อ' -> ID: {enums.get_asset_acquisition_id('ซื้อ')}")
    print(f"'โฉนด' (ที่ดิน) -> ID: {enums.get_asset_type_id('ที่ดิน', 'โฉนด')}")
    print(f"'ส.ส.' -> ID: {enums.get_position_category_id('ส.ส.')}")
    print(f"'บุตร' -> ID: {enums.get_relationship_id('บุตร')}")
    
    # แสดง context สำหรับ LLM
    print("\n" + "=" * 60)
    print("LLM PROMPT CONTEXT")
    print("=" * 60)
    print(enums.get_all_enum_context_for_llm())