from typing import List, Dict, Optional
from ..models.dataTypes import Instruction, Symbol, ModificationRecord, Location, OpcodeTable
from ..corefunc.literal import LiteralManager
from ..corefunc.objectCode import ObjectCodeGenerator

from .analyzer import Analyzer

import config

DEFAULT_BLOCK = ""

class Section:
    """
    表示組合語言程式的一個區段
    負責:
    1. 管理指令序列
    2. 維護符號表
    3. 處理位置計數器
    4. 管理外部參考和定義
    5. 產生修改紀錄
    """
    def __init__(self, name: str, opcode_table: OpcodeTable): #! name = symbol(label, section 的名稱)
        self.name = name
        self.opcode_table: OpcodeTable = opcode_table #! To write object code, give to ObjectCodeGenerator
        
        self.instructions: List[Instruction] = []
        # 符號相關的 Table
        self.symbol_table: Dict[str, Symbol] = {}       #TODO 放 symbol 跟他的 location（address 實際記憶體位置）
        self.extdef_table: Dict[str, Symbol] = {}       #TODO 放 external definition 的 symbol
        self.extref_table: Dict[str, Symbol] = {}       #TODO 放 external reference 的 symbol
        # 修改紀錄
        self.modification_records: List[ModificationRecord] = []
        # Literal
        self.literal_pool = LiteralManager()
        
        # 當前位置計數器
        self.current_location: int = 0
        
        # 基底暫存器的值
        self.base_register_value: Optional[int] = None
        # 確認 x index 定址模式
        self.x_directive_mode: Dict[str, bool] = {"key": False}


    def add_instruction(self, instruction: Instruction) -> None:
        self.instructions.append(instruction)
        
    def has_END(self) -> bool:
        """檢查區段是否有 END 指令"""
        return any(inst.mnemonic == "END" for inst in self.instructions)
    
    def _add_modification_record(self, record: ModificationRecord) -> None:
        """添加修改紀錄"""
        self.modification_records.append(record)
    
    def _makeModificationRecord(self, operand: str, mnemonic: str, location: int) -> None:
        """
        1. 遍歷所有外部參考符號（EXTREF）
        2. 檢查該符號是否出現在運算式（operand）中
        3. 如果找到符號，則替換為其值
        4. 判斷符號前的運算子
        5. 檢查是否已存在相同的修改紀錄
        6. 如果不存在相同的修改紀錄，則創建新的
        """
        for symbol, symbol_info in self.extref_table.items():
            # print('symbol, operand, address:', symbol, operand, symbol_info.addr)
            if symbol in operand and symbol_info.addr is not None:
                m = operand.find(symbol)
                operand = operand.replace(symbol, str(symbol_info.addr))
                #! 判斷符號前的運算子
                sign = "+" if m == 0 or operand[m - 1] == "+" else "-"
                # 檢查是否已存在相同的修改紀錄
                record_exists = any(
                    ((mnemonic == "WORD" and MRecord.location == location) or (mnemonic != "WORD" and MRecord.location == location + 1)) and MRecord.reference == symbol
                    for MRecord in self.modification_records
                )
                # 如果不存在相同的修改紀錄，則創建新的
                if not record_exists:
                    self._add_modification_record(ModificationRecord(location + 1 if mnemonic != "WORD" else location, 6 if mnemonic == "WORD" else 5, sign, symbol))
    
    def _evaluate_operand(self, operand: str, mnemonic: str) -> int:
        """
        計算運算式的值
        """
        if operand == "*":
            operand = str(self.current_location)
            return self.current_location
        try:
            # 替換符號為其值
            for symbol, symbol_info in self.symbol_table.items():
                if symbol in operand and symbol_info.addr is not None: #! 如果 operand 本身是符號，則替換為其值
                    #? operand 會被透過 symbol table 的對應替換成 address，以讓 eval 可以正常運作
                    operand = operand.replace(symbol, str(symbol_info.addr)) #? Ex: operand = "BUFFER + LENGTH" -> operand = "1000 + 100"

            self._makeModificationRecord(operand, mnemonic, self.current_location)

            return eval(operand)
        except:
            return 0
    
    def _makeMrecordSure(self, operand: str, mnemonic: str, location: int) -> None:
        """
        計算運算式的值
        """
        # 替換符號為其值
        for symbol, symbol_info in self.symbol_table.items():
            if symbol in operand and symbol_info.addr is not None: #! 如果 operand 本身是符號，則替換為其值
                #? operand 會被透過 symbol table 的對應替換成 address，以讓 eval 可以正常運作
                operand = operand.replace(symbol, str(symbol_info.addr)) #? Ex: operand = "BUFFER + LENGTH" -> operand = "1000 + 100"

        self._makeModificationRecord(operand, mnemonic, location)
    
    def _update_location_counter(self, instruction: Instruction) -> None:
        """
        根據指令更新位置計數器
        """
        if instruction.mnemonic == "RESW": #! 保留字組空間，每個字組 3 bytes
            result = self._evaluate_operand(instruction.operand, instruction.mnemonic)
            if result != 0:
                # 檢查結果是否為正數
                if result < 0:
                    raise ValueError(f"RESW cannot reserve negative space: {result}")
                self.current_location += (3 * result)
        elif instruction.mnemonic == "RESB": #! 保留字節空間，每個字節 1 byte
            result = self._evaluate_operand(instruction.operand, instruction.mnemonic)
            if result != 0:
                # 檢查結果是否為正數
                if result < 0:
                    raise ValueError(f"RESB cannot reserve negative space: {result}")
                self.current_location += (result)
        elif instruction.mnemonic == "BYTE": #! 處理字元常數(C)或十六進位常數(X)
            operand = instruction.operand
            if operand.startswith('C') or operand.startswith('c'):
                # 檢查格式：C'...'
                if not ((operand.startswith("C'") or operand.startswith("c'")) and operand.endswith("'")):
                    raise ValueError(f"Invalid BYTE constant format: {operand}")
                # 計算實際內容長度（去掉C''）
                content = operand[2:-1]
                self.current_location += len(content)
            elif operand.startswith('X') or operand.startswith('x'):
                # 檢查格式：X'...'
                if not ((operand.startswith("X'") or operand.startswith("x'")) and operand.endswith("'")):
                    raise ValueError(f"Invalid BYTE constant format: {operand}")
                # 計算十六進位長度
                hex_content = operand[2:-1]
                if not all(c in '0123456789ABCDEF' for c in hex_content.upper()):
                    raise ValueError(f"Invalid hexadecimal value: {hex_content}")
                self.current_location += len(hex_content) // 2
            else:
                raise ValueError(f"Invalid BYTE constant type: {operand}")
        elif instruction.mnemonic == "WORD": #! 配置一個字組（3 bytes），更新符號表中的位址
            result = self._evaluate_operand(instruction.operand, instruction.mnemonic)
            if result != 0:
                self.symbol_table[instruction.symbol].addr = self.current_location
            self.current_location += 3
        elif instruction.mnemonic == "RSUB": #! 固定使用 3 bytes
            self.current_location += 3
        elif instruction.mnemonic == "ORG":
            result = self._evaluate_operand(instruction.operand, instruction.mnemonic)
            if result != 0:
                self.current_location = result
        elif instruction.formatType > 0:  #! 一般指令
            self.current_location += instruction.formatType
    
    def _process_literal_pool(self) -> None:
        """處理 literal pool"""
        """
        功能：
        1. 收集程式中的字面值（以 = 開頭的運算元）
        2. 在遇到 LTORG 或 END 指令時，生成對應的 BYTE 指令
        3. 維護字面值表並確保不重複處理相同的字面值
        
        注意事項：
        - 字面值必須以 = 開頭
        - 支援的格式包括 =C'...' 和 =X'...'
        - 字面值會被轉換為 BYTE 指令
        """
        #! 處理帶有 = 前綴的字面值運算元（例如：=C'EOF'）
        for index, instruction in enumerate(self.instructions):
            if instruction.operand != "" and instruction.mnemonic != "LTORG" and instruction.mnemonic != "END":
                # 處理 * mnemonic 的特殊情況
                if instruction.mnemonic == "*":
                    instruction.mnemonic = "BYTE"

                # 處理 literal operands
                if instruction.operand.startswith('='):
                    try:
                        instruction.operand = self.literal_pool.add_literal(instruction.operand)
                    except ValueError as e:
                        print(f"Warning: Invalid literal format at instruction {index}: {e}")

            # 處理 LTORG 和 END
            #? 在遇到 LTORG 或 END 指令時，將收集到的字面值轉換為 BYTE 指令
            elif instruction.mnemonic in ("LTORG", "END"):
                # 獲取當前的 literal table
                current_literals_table = self.literal_pool.get_current_literals()
                
                # 為每個 literal 創建指令
                for literal in reversed(current_literals_table):
                    literal_instruction = Instruction(
                        index=index, #! LTORG 後面
                        formatType=0,
                        symbol=literal.name,
                        mnemonic="BYTE",
                        operand=literal.data,
                        objectCode="",
                        location=None,
                    )
                    self.instructions.insert(index, literal_instruction)
                    # 更新後續指令的索引
                    for i in range(index + 1, len(self.instructions)):
                        self.instructions[i].index += 1
                # 清空當前的 literal table
                self.literal_pool.clear_table()

    def _process_program_block(self) -> None:
        """處理 program block"""
        """
        1. 將指令依據不同的區塊（blocks）進行分類和重組
        2. 處理 START、CSECT（Control Section）、USE 和 END 等區塊控制指令
        3. 維護區塊的執行順序（blocks_premutation）
        4. 重新組織指令序列
        """
        blocks = {}  # Dictionary to hold blocks of instructions
        blocks_permutation = []  # List to maintain the order of blocks
        default_block = DEFAULT_BLOCK
        current_block = None
        end_of_block_inst = None
        
        for idx, instruction in enumerate(self.instructions):
            if not instruction or instruction.index is None:
                raise ValueError(f"Instruction at index {idx} is invalid or missing an index")
            # print(f"Processing instruction {idx}: {instruction.symbol} {instruction.mnemonic} {instruction.operand}")
            match instruction.mnemonic:
                case "START":
                    default_block = instruction.symbol
                    blocks.setdefault(default_block, [])
                    current_block = default_block
                    if current_block not in blocks_permutation:
                        blocks_permutation.append(current_block)
                case "CSECT":
                    blocks.setdefault(instruction.symbol, [])
                    current_block = instruction.symbol
                    if current_block not in blocks_permutation:
                        blocks_permutation.append(current_block)
                case "END":
                    if end_of_block_inst:
                        raise ValueError("Multiple END directives found")
                    end_of_block_inst = instruction
                    continue
                case "USE":
                    if not instruction.operand:
                        current_block = default_block
                    else:
                        current_block = instruction.operand
                        if current_block not in blocks:
                            blocks[current_block] = []
                            blocks_permutation.append(current_block)
                case _:  # Default case for other instructions
                    if current_block is None:
                        raise ValueError("Instruction encountered before defining a block")
                    
            if current_block is not None:
                blocks[current_block].append(instruction)
            instruction.index = idx

        # Reorganize instructions
        self.instructions = [inst for block in blocks_permutation for inst in blocks[block]]

        if end_of_block_inst:
            try:
                end_of_block_inst.index = max(self.instructions, key=lambda x: x.index).index + 1
                self.instructions.append(end_of_block_inst)
            except Exception as e:
                raise ValueError(f"Error while calculating max index: {e}")

    def _process_symbol(self) -> None:
        """處理符號（建立 SYMTAB 和 EXTDEF 和 EXTREF，設定 addr）"""
        #! 初始化 symbol table
        for instruction in self.instructions:
            if instruction.symbol:
                self.symbol_table[instruction.symbol] = Symbol(name=instruction.symbol, addr=None, is_external=False)
            match instruction.mnemonic:
                case "EXTDEF":
                    self.extdef_table.update({
                        symbol_name: Symbol(name=symbol_name, addr=None, is_external=True)
                        for symbol_name in instruction.operand.split(",")
                    })

                case "EXTREF":
                    self.extref_table.update({
                        symbol_name: Symbol(name=symbol_name, addr=0, is_external=True)
                        for symbol_name in instruction.operand.split(",")
                    })
            
        while any(symbol.addr is None for symbol in self.symbol_table.values()):
            self.current_location = 0 #! initial 0
            for instruction in self.instructions:
                if instruction.symbol != "":
                    self.symbol_table[instruction.symbol].addr = self.current_location
                    if instruction.symbol in self.extdef_table:
                        self.extdef_table[instruction.symbol].addr = self.current_location
                        
                if instruction.mnemonic == "START":
                    self.current_location = int(instruction.operand, 16)
                    self.symbol_table[instruction.symbol].addr = self.current_location
                elif instruction.mnemonic == "RESW":
                    self.symbol_table[instruction.symbol].addr = self.current_location
                    self._update_location_counter(instruction)
                elif instruction.mnemonic == "RESB":
                    self.symbol_table[instruction.symbol].addr = self.current_location
                    self._update_location_counter(instruction)
                elif instruction.mnemonic == "BYTE":
                    self.symbol_table[instruction.symbol].addr = self.current_location
                    self._update_location_counter(instruction)
                elif instruction.mnemonic == "WORD":
                    self._update_location_counter(instruction) #! Already set symbol talbe in there
                elif instruction.mnemonic == "EQU":
                    result = self._evaluate_operand(instruction.operand, instruction.mnemonic)
                    if result != 0:
                        self.symbol_table[instruction.symbol].addr = result
                        instruction.location = Location(result, is_relative=False)
                elif instruction.mnemonic == "RSUB":
                    instruction.operand = "#0"
                    self._update_location_counter(instruction) #! Don't need to set symbol table
                elif instruction.mnemonic == "BASE":
                    result = self._evaluate_operand(instruction.operand, instruction.mnemonic)
                    if result != 0:
                        self.base_register_value = result
                        instruction.operand = result
                elif instruction.mnemonic == "CSECT":
                    self.current_location = 0
                    self.symbol_table[instruction.symbol].addr = self.current_location
                elif instruction.mnemonic == "ORG":
                    result = self._evaluate_operand(instruction.operand, instruction.mnemonic)
                    if result != 0:
                        self.current_location = result
                        instruction.operand = result
                elif instruction.formatType > 0:
                    self._update_location_counter(instruction) #! Normal instruction for format 1 - 4
        self.current_location = 0
    
    def _calculate_address(self) -> None:
        """計算每個指令的地址"""
        self.current_location = 0
        for instruction in self.instructions:
            # 判斷是否為相對定址
            # is_relative_for_current_instruction = (
            #     instruction.mnemonic not in {"START", "BASE", "END", "CSECT", "EXTREF", "EXTDEF"} and
            #     not (instruction.operand and (instruction.operand.startswith("#") or instruction.operand.startswith("@"))) and
            #     not instruction.mnemonic.startswith("+")  # Extended format (absolute addressing)
            #     and instruction.formatType not in {0, 2}  # 格式 0: 控制指令；格式 2: 寄存器操作
            # )
            if instruction.mnemonic != "EQU":
                instruction.location = Location(self.current_location, is_relative=False)
            
            if instruction.mnemonic == "START":
                start_address = int(instruction.operand, 16)
                instruction.location = Location(start_address, is_relative=False)
                self.current_location = start_address
            elif instruction.mnemonic == "CSECT":
                self.current_location = 0
                instruction.location = Location(0, is_relative=False)
            elif instruction.mnemonic == "WORD":
                self.current_location += 3
            else:
                self._update_location_counter(instruction)
    
    def _set_external_definition_location(self) -> None:
        """設定外部定義的地址"""
        for symbol in self.extdef_table:
            if symbol in self.symbol_table:
                self.extdef_table[symbol].addr = self.symbol_table[symbol].addr
            else:
                raise ValueError(f"External definition symbol {symbol} not found in symbol table")
                
    def _reorder_index(self) -> None:
        """重新排序指令的索引"""
        self.instructions.sort(key=lambda x: x.index)
        
    def _generate_object_code(self) -> None:
        generator = ObjectCodeGenerator(self)
        base_value = 0
        
        for instruction in self.instructions:
            if instruction.mnemonic == "BASE":
                #! 更新 base register 的值
                base_value = self._evaluate_operand(instruction.operand, instruction.mnemonic)
                generator.set_base_value(base_value)
                continue #! Don't need to generate object code
            
            if config.bonus:
                if instruction.operand != "*":
                    if instruction.mnemonic == "WORD":
                        self._makeMrecordSure(instruction.operand, instruction.mnemonic, instruction.location.address)
                    elif instruction.mnemonic in self.opcode_table:
                        if instruction.formatType == 3 or instruction.formatType == 4:
                            if ",X" in instruction.operand:
                                self.x_directive_mode[instruction.mnemonic + instruction.operand[:-2]] = True
                            else:
                                self.x_directive_mode[instruction.mnemonic + instruction.operand[:-2]] = False
                            if "," in instruction.operand:
                                instruction.operand = instruction.operand[:-2]
                            if instruction.operand.startswith("#") or instruction.operand.startswith("@"):
                                self._makeMrecordSure(instruction.operand[1:], instruction.mnemonic, instruction.location.address)
                            else:
                                self._makeMrecordSure(instruction.operand, instruction.mnemonic, instruction.location.address)

            #! Generate object code
            instruction.objectCode = generator.generateOpCode(instruction, instruction.location)
        
    def pass1(self) -> None:
        """第一次掃描"""
        if config.bonus:
            print('-' * 25)
            print('Process Literal Pool')
            self._process_literal_pool()
            analyzer = Analyzer(self)
            analyzer.analyze("LITTAB") #! print on console
            print('Process Literal Pool completed')
            print('-' * 25)
    
            print('Process Program Block')
            self._process_program_block()
            print('Process Program Block completed')
            print('-' * 25)
        
        print('Set symbol table')
        self._process_symbol()
        analyzer = Analyzer(self)
        analyzer.analyze("SYMTAB") #! print on console
        print('Set symbol table completed')
        print('-' * 25)
        
        print('Calculate address of each instruction')
        self._calculate_address()
        print('Calculate address completed')
        print('-' * 25)
        
        if config.bonus:
            print('Set external defintion location')
            self._set_external_definition_location()
            print('Set external defintion location completed')
            analyzer = Analyzer(self)
            analyzer.analyze("EXTREF") #! print on console
            analyzer.analyze("EXTDEF")

    def pass2(self) -> None:
        """第二次掃描"""
        if config.bonus:
            print('Reorder instruction')
            self._reorder_index()
            print('Reorder instruction completed')
        print('Generate object code for each instruction')
        self._generate_object_code()
        analyzer = Analyzer(self)
        analyzer.analyze("MODREC") #! print on console
        analyzer.analyze("INSTR") #! print on console
        print('Generate object code completed')
