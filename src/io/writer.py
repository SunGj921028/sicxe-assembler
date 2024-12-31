
class ObjectFileWriter:
    def __init__(self):
        self.H_header = ""
        self.D_extdef = ""
        self.R_extref = ""
        self.T_text = ""
        self.M_modification = ""
        self.E_end = ""
        self.text_record_template = "T{:06X}{:02X}{}\n"
    
    #! 寫入 section 的 header (H) 記錄
    def _write_section_header(self, section, output_file):
        start_loc = section.instructions[0].location.address
        end_loc = section.instructions[-1].location.address
        self.H_header = (
            f"H{section.instructions[0].symbol.ljust(6)}"
            f"{start_loc:06X}"
            f"{end_loc - start_loc:06X}\n" # Length of program
        )
        output_file.write(self.H_header)
    
    #! 寫入 EXTDEF (D) 記錄
    def _write_extdef(self, section, output_file):
        self.D_extdef = ""
        if not section.extdef_table:
            return
        
        # 將符號和地址配對並分組（每組5個）
        symbols = [(name, symbol.addr) for name, symbol in section.extdef_table.items()]
        groups = [symbols[i : i + 5] for i in range(0, len(symbols), 5)]
    
        # 寫入每一組
        for group in groups:
            output_file.write("D")
            for name, addr in group:
                if addr is not None:  # 確保地址不是 None
                    output_file.write(f"{name.ljust(6)}{addr:06X}")
            output_file.write("\n")

    #! 寫入 EXTREF (R) 記錄
    def _write_extref(self, section, output_file):
        self.R_extref = ""
        if not section.extref_table:
            return
    
        # 將符號分組（每組5個）
        symbols = list(section.extref_table.keys())
        groups = [symbols[i : i + 5] for i in range(0, len(symbols), 5)]

        # 寫入每一組
        for group in groups:
            output_file.write("R")
            for name in group:
                output_file.write(name.ljust(6))
            output_file.write("\n")

    #! 寫入 Text (T) 記錄
    def _write_text_records(self, section, output_file):
        cur_start = None
        cur_text = ""
        for instruction in section.instructions:
            if (instruction.mnemonic in ["RESW", "RESB", "USE"]):
                if cur_text != "":
                    self._write_single_text_record(output_file, cur_start, cur_text)
                    cur_text = ""
                continue
            
            #TODO 不確定會不會有沒有目標碼的指令
            if not instruction.objectCode:  # 跳過沒有目標碼的指令
                continue
            
            if cur_text == "":
                cur_start = instruction.location.address
            if len(cur_text) + len(instruction.objectCode) > 60:
                self._write_single_text_record(output_file, cur_start, cur_text)
                cur_text = ""
                cur_start = instruction.location.address
            cur_text += instruction.objectCode
            
        if cur_text != "":
            self._write_single_text_record(output_file, cur_start, cur_text)

    #! 寫入單一個 Text record
    def _write_single_text_record(self, output_file, start, text):
        record = self.text_record_template.format(start, len(text)//2, text)
        output_file.write(record)

    #! 寫入 Modification (M) 記錄
    def _write_modification_records(self, section, output_file):
        self.M_modification = ""
        if not section.modification_records:
            return
        
        sorted_records = sorted(section.modification_records, key=lambda x: x.location)
        for record in sorted_records:
            output_file.write(f"M{record.location:06X}{record.length:02X}{record.sign}{record.reference}\n")

    #! 寫入 End (E) 記錄
    def _write_section_end(self, section, output_file):
        output_file.write("E")
        last_instruction = section.instructions[-1]
        if last_instruction.mnemonic == "END" and last_instruction.operand != "":
            #TODO 在 section 的符號表中尋找該符號的位址(這個部分需要再確認)
            entry_symbol = last_instruction.operand
            if entry_symbol in section.symbol_table:
                entry_address = section.symbol_table[entry_symbol].addr
                output_file.write(f"{entry_address:06X}")
            else:
                raise ValueError(f"Symbol {entry_symbol} not found in symbol table")
        output_file.write("\n\n")
        
    def write_section(self, section, output_file):
        """
        主要的寫入函數，負責協調各個子函數來寫入完整的 section
        """
        self._write_section_header(section, output_file)
        self._write_extdef(section, output_file)
        self._write_extref(section, output_file)
        self._write_text_records(section, output_file)
        self._write_modification_records(section, output_file)
        self._write_section_end(section, output_file)
    
    
    
