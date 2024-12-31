from typing import Dict, List
from ..models.dataTypes import Literal

class LiteralManager:
    def __init__(self):
        self.literal_table: List[Literal] = []  #! literal table，紀錄 name, data, used_count
        self.literal_set: Dict[str, str] = {}   #! 快速查找用的 set
        self.literal_count: int = 1             #! 紀錄 literal 的數量
        self.literal_temp_table: List[Literal] = [] #! 紀錄輸出用的 literal
    
    def add_literal(self, literal_value: str) -> str:
        """添加新的 literal 到 literal table"""
        # 檢查是否已存在
        if literal_value in self.literal_set:
            # 更新使用次數
            for entry in self.literal_table:
                if entry.name == self.literal_set[literal_value]:
                    entry.used_count += 1
            return self.literal_set[literal_value] #! instruction.operand = literal_set[literal_value]

        # 創建新的 literal entry
        new_name = f"literal{self.literal_count}"
        print(f"New literal: {new_name} = {literal_value}")
        new_entry = Literal(
            name=new_name,
            data=literal_value[1:],  # 移除 '=' 前綴
            used_count=1
        )
        
        # 更新表格和集合
        self.literal_table.append(new_entry)
        self.literal_set[literal_value] = new_name
        self.literal_count += 1
        
        return new_name

    def get_current_literals(self) -> List[Literal]:
        """獲取當前的 literal table"""
        return self.literal_table
    
    def get_literals_to_print(self) -> List[Literal]:
        """獲取當前的 literal table"""
        return self.literal_temp_table

    def clear_table(self) -> None:
        """清空 literal table"""
        self.literal_temp_table.extend(self.literal_table)  # 使用 extend 而不是 append
        self.literal_table = []
        self.literal_set = {}
        
