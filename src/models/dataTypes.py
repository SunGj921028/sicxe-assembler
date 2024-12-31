from dataclasses import dataclass
from typing import Optional, TypedDict, Dict

@dataclass
class Location:
    """位置類別，用於表示記憶體位置
    address: 記憶體地址
    is_relative: 是否為相對位置（預設為True）
    """
    address: int
    is_relative: bool = True

@dataclass
class Symbol:
    """符號類別，用於表示標籤
    name: 符號名稱
    addr: 符號對應的記憶體地址（可選）
    is_external: 是否為外部符號（預設為False）
    """
    name: str
    addr: Optional[int] = None
    is_external: bool = False

@dataclass
class ModificationRecord:   #! 修改記錄(M 000007 05+COPY)
    """修改記錄類別，用於處理目標程式的修改記錄
    location: 需要修改的位置
    length: 修改的長度（半位元組數）
    sign: 修改操作的符號（+ 或 -）
    reference: 參考的符號名稱
    """
    location: int           #! 000007
    length: int             #! 05
    sign: str = ""          #! +
    reference: str = ""     #! COPY

@dataclass
class Instruction:
    """指令類別，用於表示組合語言指令
    index: 指令索引
    formatType: 指令格式類型（1,2,3,4）
    symbol: 標籤符號
    mnemonic: 指令助記符
    operand: 運算元
    objectCode: 目標碼（預設為空字串）
    location: 指令位置（可選）
    """
    index: int
    formatType: int
    symbol: str
    mnemonic: str
    operand: str
    objectCode: str = ""
    location: Optional[Location] = None

@dataclass
class Literal:
    """字面值類別，用於處理常數或字串字面值
    name: 字面值名稱
    data: 字面值內容
    used_count: 使用次數（預設為0）
    """
    name: str
    data: str
    used_count: int = 0

@dataclass
class OpcodeEntry(TypedDict):
    """操作碼表項目類別，用於定義操作碼的相關資訊
    obj: 操作碼的機器碼
    format: 指令格式
    """
    obj: str
    format: int
    
# 操作碼表型別定義，用於儲存所有操作碼
OpcodeTable = Dict[str, OpcodeEntry]