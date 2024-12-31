
from typing import Dict, Tuple, List, TYPE_CHECKING
from ..models.dataTypes import Instruction, Symbol, Location, ModificationRecord, OpcodeTable
from config import REGISTER_TABLE
import ast

if TYPE_CHECKING:
    from .section import Section

class ObjectCodeGenerator:
    def __init__(self, section: 'Section'):
        self.sectionTmp = section
        self.base_value = 0
        
    @property
    def symbol_table(self) -> Dict[str, Symbol]:
        return self.sectionTmp.symbol_table
    
    @property
    def extref_table(self) -> Dict[str, Symbol]:
        return self.sectionTmp.extref_table
    
    @property
    def opcode_table(self) -> OpcodeTable:
        return self.sectionTmp.opcode_table
    
    @property
    def modification_records(self) -> List[ModificationRecord]:
        return self.sectionTmp.modification_records
    
    @property
    def x_directive_mode(self) -> Dict[str, bool]:
        return self.sectionTmp.x_directive_mode
    
    def set_base_value(self, value: int) -> None:
        """設定 BASE 暫存器的值"""
        self.base_value = value
        
    def _generate_byte_code(self, operand: str) -> str:
        """
        生成 BYTE 指令的目標碼
        C'EOF' -> 454F46 (ASCII)
        X'F1' -> F1 (直接使用十六進位)
        """
        if operand.startswith('C') or operand.startswith('c'):
            # 字元常數轉換為十六進位
            return ''.join(f"{ord(c):02X}" for c in operand[2:-1])
        elif operand.startswith('X') or operand.startswith('x'):
            # 直接返回十六進位值
            return operand[2:-1]
        return ""
    
    def _generate_word_code(self, operand: str) -> str:
        """
        生成 WORD 指令的目標碼
        轉換為 6 位十六進位數
        """
        try:
            value = ast.literal_eval(operand) #! 比較安全的 eval
            if not isinstance(value, int):
                raise ValueError("Operand must evaluate to an integer")
            return f"{value & 0xFFFFFF:06X}"  # 確保是 6 位十六進位，0xFFFFFF = 16777215 = 24 個 1
        except:
            return "000000"
    
    #! Calculate Target Address
    def _get_target_address(self, operand: str) -> int:
        """取得目標位址"""
        if operand.startswith(("#", "@")):
            operand = operand[1:] #? Pass the '#' or '@'
            
        #! If is number, return it
        if operand.isdigit():
            return int(operand)

        #! Search for symbol table
        if operand in self.symbol_table:
            return self.symbol_table[operand].addr or 0
        
        #! Search for external references
        if operand in self.extref_table:
            return self.extref_table[operand].addr or 0
        
        return 0
    
    #! Format 1
    def _format1(self, instruction: Instruction) -> str:
        """Format 1: 8位元操作碼"""
        return f"{self.opcode_table[instruction.mnemonic]['obj']}"
    
    #! Format 2
    def _format2(self, instruction: Instruction) -> str:
        """Format 2: 8位元操作碼 + 4位元暫存器1 + 4位元暫存器2"""
        operand = instruction.operand.split(',')
        #! Range 0-9
        #? Ex: ADDR, A,X or CLEAR, A
        r1 = REGISTER_TABLE[operand[0]]
        r2 = REGISTER_TABLE[operand[1] if len(operand) > 1 else 'A'] #! 如果沒有第二個暫存器，則使用 A(default)
        return f"{self.opcode_table[instruction.mnemonic]['obj']}{r1}{r2}" #! 四位 16 進位
        
    #! Format 3
    def _cal_flags(self, instruction: Instruction, current_location: Location) -> Tuple[int, int, int, int, int, int]:
        """計算 nixbpe 旗標"""
        class Flags:
            def __init__(self):
                self.n = self.i = self.x = self.b = self.p = self.e = 0
        
        flags = Flags()
        operand = instruction.operand
        
        #! 處理索引定址(index addressing)
        # print('Instruction:', instruction.mnemonic, instruction.operand)
        if "," in operand: #! 如果有逗號
            flags.x = 1
            operand = operand.split(",")[0]
        if instruction.mnemonic + instruction.operand in self.x_directive_mode:
            if self.x_directive_mode[instruction.mnemonic + instruction.operand]:
                flags.x = 1
        
        
        #! 處理定址模式
        if operand.startswith("#"): # Direct Addressing
            flags.n = 0
            flags.i = 1
        elif operand.startswith("@"): # Indirect Addressing
            flags.n = 1
            flags.i = 0
        else: # Immediate Addressing
            flags.n = 1
            flags.i = 1
        
        #! 計算是否使用基底相對(base relative)或程式計數器相對定址(PC relative)
        target_address = self._get_target_address(operand)
        if operand.startswith("#") and operand[1:].isdigit(): #? Ex: #4096
            if target_address == int(operand[1:]):
                flags.b = 0
                flags.p = 0
                instruction.location.is_relative = False
                return flags.n, flags.i, flags.x, flags.b, flags.p, flags.e
        
        pc_realtive = target_address - (current_location.address + instruction.formatType)
        
        if -2048 <= pc_realtive <= 2047:
            if not (operand.startswith("@") or operand.startswith("#")):
                instruction.location.is_relative = True
            else:
                instruction.location.is_relative = False
            flags.b = 0
            flags.p = 1
        elif 0 <= target_address - self.base_value <= 4095:
            if not (operand.startswith("@") or operand.startswith("#")):
                instruction.location.is_relative = True
            else:
                instruction.location.is_relative = False
            flags.b = 1
            flags.p = 0
        else:
            print(f"Error determining flags on: {instruction.mnemonic} {instruction.operand} {current_location.address}")
            raise ValueError(f"Error determining flags on: {instruction.mnemonic} {instruction.operand} {current_location.address}")
        
        return flags.n, flags.i, flags.x, flags.b, flags.p, flags.e
        
    def _cal_displacement(self, instruction: Instruction, current_location: Location, flags: Tuple[int, int, int, int, int, int]) -> int:
        """計算位移值"""
        # flags -> n, i, x, b, p, e
        if "," in instruction.operand:
            operand = instruction.operand.split(",")[0] #! remove index part
        else:
            operand = instruction.operand
        
        if operand.startswith(("#", "@")):
            operand = operand[1:]
        
        target_address = self._get_target_address(operand)
        
        if flags[4]:
            displacement = target_address - (current_location.address + instruction.formatType)
            if not -2048 <= displacement <= 2047:
                raise ValueError(f"Displacement out of range for PC-relative addressing: {displacement}")
            displacement = displacement & 0xFFF  # 截取 12 位元
        elif flags[3]:
            displacement = target_address - self.base_value
            if not 0 <= displacement <= 4095:
                raise ValueError(f"Displacement out of range for Base-relative addressing: {displacement}")
            displacement = displacement & 0xFFF  # 截取 12 位元
        else:
            #! format 3, 12 位元的 displacement
            displacement = target_address & 0x7FF #! (2^11 - 1) = 2047, 於確保位移值不超過 11 位元
        return displacement
    
    def _format3(self, instruction: Instruction, current_location: Location) -> str:
        """Format 3: 6位元操作碼 + nixbpe + 12位元位移"""
        opcode = int(self.opcode_table[instruction.mnemonic]["obj"], 16) >> 2 #! 取前 6 位
        flags = self._cal_flags(instruction, current_location)
        disp = self._cal_displacement(instruction, current_location, flags)
        
        #! 組合目標碼
        #? 先把所有這些二進制位串接在一起，形成一個 24 位元的二進制字串
        #? 然後用 int(code, 2) 將二進制字串轉換為整數
        #? 最後用 {:06X} 將整數轉換為 6 位的十六進制字串
        code = f"{opcode:06b}{flags[0]}{flags[1]}{flags[2]}{flags[3]}{flags[4]}{flags[5]}{disp:012b}"
        return f"{int(code, 2):06X}"

    def _parse_addressing_mode_for_format4(self, instruction: Instruction, operand: str) -> Tuple[int, int, int]:
        """解析定址模式，返回 n, i, x 值"""
        n, i, x = 0, 0, 0
        
        # 處理索引定址
        if "," in operand:
            x = 1
            operand = operand.split(",")[0]
        if instruction.mnemonic + instruction.operand in self.x_directive_mode:
            if self.x_directive_mode[instruction.mnemonic + instruction.operand]:
                x = 1
        
        # 處理定址模式
        if operand.startswith("#"):  # Direct addressing
            n, i = 0, 1
        elif operand.startswith("@"):  # Indirect addressing
            n, i = 1, 0
        else:  # Simple addressing
            n, i = 1, 1
            
        return n, i, x
    
    def _cal_address(self, operand: str) -> int:
        """計算 Format 4 的位址值"""
        if "," in operand:
            operand = operand.split(",")[0]
        
        if operand.startswith(("#", "@")):
            operand = operand[1:]
        
        # 如果是數字，直接返回
        if operand.isdigit():
            return int(operand)
        
        # 查找符號表
        if operand in self.symbol_table:
            return self.symbol_table[operand].addr or 0
        
        # 查找外部參照
        if operand in self.extref_table:
            return self.extref_table[operand].addr or 0
        
        return 0
    
    def _format4(self, instruction: Instruction) -> str:
        """Format 4: 6位元操作碼 + nixbpe + 20位元位址"""
        opcode = int(self.opcode_table[instruction.mnemonic]["obj"], 16) >> 2 #! 取前 6 位
        n, i, x = self._parse_addressing_mode_for_format4(instruction, instruction.operand)
        b, p, e = 0, 0, 1 #! default (e = 1)
        
        #! Deal with address
        address = self._cal_address(instruction.operand)
        
        #! 組合 object code
        code = f"{opcode:06b}{n}{i}{x}{b}{p}{e}{address:020b}"
        
        #! 只在 simple addressing (n=1, i=1) 的情況下處理 modification record
        if n == 1 and i == 1: #! Simple addressing
            #? Need to check modification record
            if instruction.location != None:
                record_exists = any(record.location == instruction.location.address + 1 and record.reference == instruction.operand for record in self.modification_records)
                if not record_exists:
                    self.sectionTmp._add_modification_record(ModificationRecord(instruction.location.address + 1, 5, "", ""))
    
        return f"{int(code, 2):08X}"
    
    def generate_for_instruction(self, instruction: Instruction, current_location: Location) -> str:
        """生成指令格式 1-4 的目標碼"""
        if instruction.formatType == 1:
            return self._format1(instruction)
        elif instruction.formatType == 2:
            return self._format2(instruction)
        elif instruction.formatType == 3:
            return self._format3(instruction, current_location)
        elif instruction.formatType == 4:
            return self._format4(instruction)
        return ""
        
    #! 生成指令的 object code
    def generateOpCode(self, instruction: Instruction, location: Location) -> str:
        # print(f"instruction: {instruction.mnemonic} {instruction.operand}")
        if instruction.mnemonic == "BYTE":
            return self._generate_byte_code(instruction.operand)
        elif instruction.mnemonic == "WORD":
            return self._generate_word_code(instruction.operand)
        elif instruction.mnemonic == "RSUB":
            return "4F0000"
        elif instruction.formatType > 0:
            return self.generate_for_instruction(instruction, location) #! 對不同的 format 生成不同的 object code
        else:
            return ""
    
