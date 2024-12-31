from typing import List, Tuple, Set
from ..models.dataTypes import Instruction, OpcodeTable
from ..corefunc.section import Section


from config import directive_table, opcode_table


class Preprocessor:
    def __init__(self):
        self.opcode_table: OpcodeTable = opcode_table
        self.directive_table: Set[str] = directive_table

    def _parse_line(self, line: str) -> Tuple[str, str, str]:
        """
        解析單行組合語言程式碼
        
        Args:
            line: 輸入的程式碼行
            
        Returns:
            (symbol, mnemonic, operand) 的元組
        """
        # 移除註解和空白
        if line.strip().startswith('.'):
            return "", "", ""
        if '.' in line:
            line = line.split('.')[0]  # 只取 `.` 前的部分
        line = line.strip().replace('\t', ' ')
        
        # 分割行內容
        parts = line.split()
        parts.extend([""] * (3 - len(parts)))  # 確保有三個部分
        
        symbol, mnemonic, operand = parts[:3]
        
        #! 特殊處理 BYTE 指令的操作數
        if mnemonic == "BYTE":
            operand = " ".join([operand] + parts[3:])
        
        return symbol, mnemonic, operand

    def _create_instruction(self, line_parts: Tuple[str, str, str], index: int) -> Instruction:
        """
        從解析後的行內容建立指令物件
        
        Args:
            line_parts: (symbol, mnemonic, operand) 的元組
            index: 指令的索引
            
        Returns:
            建立的 Instruction 物件
        """
        symbol, mnemonic, operand = line_parts
        formatType = 0
        
        # 處理 Format 4 指令
        if '+' in symbol:
            formatType = 4
            symbol = symbol.replace('+', '')
        elif '+' in mnemonic:
            formatType = 4
            mnemonic = mnemonic.replace('+', '')
            
        # 處理沒有標籤的指令
        if symbol in self.opcode_table or symbol in self.directive_table or symbol == '*': #! mnemonic 是中間的指令
            operand = mnemonic
            mnemonic = symbol
            symbol = ""
        
        #TODO 還需要處理 ADD ADD VALUE 這種指令，symbol 的名稱不能是 opcode 或 directive
        #! 處理指令中可能出現的情況，symbol 的名稱不能是 opcode 或 directive
        if symbol in self.opcode_table or symbol in self.directive_table:
            # 如果 symbol 是 opcode 或 directive，則將其視為 operand
            print(f"Warning: In index: {index}, insturction: {line_parts}, '{symbol}' is an opcode/directive and cannot be used as a symbol. Treating it as an operand.")
            symbol = "WRONG_SYMBOL_NAME_" + symbol
        
        # 檢查指令格式是否有效
        if mnemonic not in self.opcode_table and mnemonic not in self.directive_table:
            raise ValueError(f"Invalid mnemonic '{mnemonic}' at index {index}: not found in opcode or directive tables.")
        
        # 設定指令格式
        if formatType != 4 and mnemonic in self.opcode_table:
            formatType = self.opcode_table[mnemonic]['format']
            
        return Instruction(
            index=index,
            formatType=formatType,
            symbol=symbol,
            mnemonic=mnemonic,
            operand=operand,
            objectCode="",
            location=None
        )
    
    def process(self, input_file: str) -> List[Section]:
        """
        處理輸入檔案並返回程式區段列表
        Args:
            input_file: 輸入檔案的路徑
        Returns:
            Section 物件的列表
        Raises:
            FileNotFoundError: 當輸入檔案不存在時
            ValueError: 當輸入檔案格式不正確時
        """
        sections: List[Section] = [Section("DEFAULT", self.opcode_table)] #! 傳送 opcode_table 供 Section 傳遞
        instruction_index = 0
        instruction_temp = []
        
        try:
            with open(input_file, 'r') as f:
                for line in f:
                    if line.strip() == "": #! 跳過空行
                        continue
                        
                    # 解析行內容
                    linesContent = self._parse_line(line)
                    if not any(linesContent):  # 跳過空行或純註解行
                        continue
                        
                    # 建立指令物件
                    instruction = self._create_instruction(linesContent, instruction_index)
                    instruction_index += 1
                    
                    instruction_temp.append(instruction)
            
            # 確保每個區段都有 END 指令
            for instruction in instruction_temp:
                if instruction.mnemonic == "END":
                    sections[0].add_instruction(instruction)
                    break
                elif instruction.mnemonic == "CSECT":
                    sections.append(Section(instruction.symbol, self.opcode_table))
                sections[-1].add_instruction(instruction)
            
            for section in sections:
                if not section.has_END():
                    print('Warning: No END directive found in section', section.name)
                    section.add_instruction(Instruction(
                        index=-1,
                        formatType=0,
                        symbol="",
                        mnemonic="END",
                        operand="",
                        objectCode="",
                        location=None
                    ))
                    
            return sections
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file {input_file} not found")
        except Exception as e:
            raise ValueError(f"Error processing input file: {str(e)}")