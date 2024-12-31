from typing import TextIO, TYPE_CHECKING, Dict
from tabulate import tabulate

if TYPE_CHECKING:
    from src.corefunc.section import Section

import os
class Analyzer:
    def __init__(self, section: "Section"):
        self.section = section
        
    def print_symbol_table(self, file: TextIO = None) -> None:
        """輸出符號表"""
        headers = ["Symbol", "Address", "is_external"]
        rows = [
            [name, f"{symbol.addr:04X}" if symbol.addr is not None else "NONE", symbol.is_external]
            for name, symbol in self.section.symbol_table.items()
        ]
        
        print("\n=== Symbol Table ===", file=file)
        print(tabulate(rows, headers=headers, tablefmt="grid"), file=file)
        
    def print_extref_table(self, file: TextIO = None) -> None:
        """輸出外部參考表"""
        headers = ["Symbol", "Address", "is_external"]
        rows = [
            [name, f"{symbol.addr:04X}" if symbol.addr is not None else "NONE", symbol.is_external]
            for name, symbol in self.section.extref_table.items()
        ]
        
        print("\n=== External Reference Table ===", file=file)
        print(tabulate(rows, headers=headers, tablefmt="grid"), file=file)
        
    def print_extdef_table(self, file: TextIO = None) -> None:
        """輸出外部定義表"""
        headers = ["Symbol", "Address", "is_external"]
        rows = [
            [name, f"{symbol.addr:04X}" if symbol.addr is not None else "NONE", symbol.is_external]
            for name, symbol in self.section.extdef_table.items()
        ]
        
        print("\n=== External Definition Table ===", file=file)
        print(tabulate(rows, headers=headers, tablefmt="grid"), file=file)
        
    def print_modification_records(self, file: TextIO = None) -> None:
        """輸出修改記錄"""
        headers = ["Location", "Length", "Sign", "Reference"]
        rows = [
            [f"{record.location:06X}", record.length, record.sign, record.reference]
            for record in self.section.modification_records
        ]
        
        print("\n=== Modification Records ===", file=file)
        print(tabulate(rows, headers=headers, tablefmt="grid"), file=file)
        
    def print_instructions(self, file: TextIO = None) -> None:
        """輸出指令列表資訊"""
        headers = ["Index", "Format", "Symbol", "Mnemonic", "Operand", "Object Code", "Location", "is_relative_addressing"]
        rows = [
            [
                inst.index,
                inst.formatType,
                inst.symbol,
                inst.mnemonic if inst.formatType != 4 else f"+{inst.mnemonic}",
                "" if inst.mnemonic == "RSUB" else (
                    inst.operand + ",X" if (inst.mnemonic + inst.operand) in self.section.x_directive_mode and self.section.x_directive_mode[inst.mnemonic + inst.operand] else inst.operand
                ),
                inst.objectCode,
                f"{inst.location.address:04X}" if inst.mnemonic != "LTORG" and inst.mnemonic != "END" and inst.mnemonic != "BASE" and inst.mnemonic != "EXTDEF" and inst.mnemonic != "EXTREF" else "",
                inst.location.is_relative if inst.location is not None else False
            ]
            for inst in self.section.instructions
        ]
        
        print("\n=== Instructions ===", file=file)
        print(tabulate(rows, headers=headers, tablefmt="grid"), file=file)
        
    def print_literal_table(self, file: TextIO = None) -> None:
        """輸出 Literal 表"""
        headers = ["Name", "Data", "Used Count"]
        # 取得當前的 literal table
        literal_manager = self.section.literal_pool
        rows = [
            [literal.name, literal.data, literal.used_count]
            for literal in literal_manager.get_literals_to_print()
        ]
        
        print("\n=== Literal Table ===", file=file)
        print(tabulate(rows, headers=headers, tablefmt="grid"), file=file)
        
    def analyze(self, phase: str) -> None:
        """執行完整分析並輸出所有資訊"""
        if phase == "all":
            print(f"\nAnalysis for Section: {self.section.name}")
            print("=" * 25)
            self.print_symbol_table()
            self.print_extref_table()
            self.print_extdef_table()
            self.print_literal_table()
            self.print_modification_records()
            self.print_instructions()
        elif phase == "SYMTAB":
            self.print_symbol_table()
        elif phase == "EXTREF":
            self.print_extref_table()
        elif phase == "EXTDEF":
            self.print_extdef_table()
        elif phase == "LITTAB":
            self.print_literal_table()
        elif phase == "MODREC":
            self.print_modification_records()
        elif phase == "INSTR":
            self.print_instructions()
