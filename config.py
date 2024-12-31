import os

#! variables
input_folder = "input"
output_folder = "output"

bonus = False

# 定義全域的暫存器表
REGISTER_TABLE = {
    "A": "0",
    "X": "1",
    "L": "2",
    "B": "3",
    "S": "4",
    "T": "5",
    "F": "6",
    "PC": "8",
    "SW": "9"
}

directive_table = [
    "START",
    "END",
    "WORD",
    "BYTE",
    "BASE",
    "RESW",
    "RESB",
    "USE",
    "EXTDEF",
    "EXTREF",
    "CSECT",
    "LTORG",
    "EQU"
]

opcode_table = {
    "ADD": {
        "obj": "18",
        "format": 3
    },
    "ADDF": {
        "obj": "58",
        "format": 3
    },
    "ADDR": {
        "obj": "90",
        "format": 2
    },
    "AND": {
        "obj": "40",
        "format": 3
    },
    "CLEAR": {
        "obj": "B4",
        "format": 2
    },
    "COMP": {
        "obj": "28",
        "format": 3
    },
    "COMPF": {
        "obj": "88",
        "format": 3
    },
    "COMPR": {
        "obj": "A0",
        "format": 2
    },
    "DIV": {
        "obj": "24",
        "format": 3
    },
    "DIVF": {
        "obj": "64",
        "format": 3
    },
    "DIVR": {
        "obj": "9C",
        "format": 2
    },
    "FIX": {
        "obj": "C4",
        "format": 1
    },
    "FLOAT": {
        "obj": "C0",
        "format": 1
    },
    "HIO": {
        "obj": "F4",
        "format": 1
    },
    "J": {
        "obj": "3C",
        "format": 3
    },
    "JEQ": {
        "obj": "30",
        "format": 3
    },
    "JGT": {
        "obj": "34",
        "format": 3
    },
    "JLT": {
        "obj": "38",
        "format": 3
    },
    "JSUB": {
        "obj": "48",
        "format": 3
    },
    "LDA": {
        "obj": "00",
        "format": 3
    },
    "LDB": {
        "obj": "68",
        "format": 3
    },
    "LDCH": {
        "obj": "50",
        "format": 3
    },
    "LDF": {
        "obj": "70",
        "format": 3
    },
    "LDL": {
        "obj": "08",
        "format": 3
    },
    "LDS": {
        "obj": "6C",
        "format": 3
    },
    "LDT": {
        "obj": "74",
        "format": 3
    },
    "LDX": {
        "obj": "04",
        "format": 3
    },
    "LPS": {
        "obj": "D0",
        "format": 3
    },
    "MUL": {
        "obj": "20",
        "format": 3
    },
    "MULF": {
        "obj": "60",
        "format": 3
    },
    "MULR": {
        "obj": "98",
        "format": 2
    },
    "NORM": {
        "obj": "C8",
        "format": 1
    },
    "OR": {
        "obj": "44",
        "format": 3
    },
    "RD": {
        "obj": "D8",
        "format": 3
    },
    "RMO": {
        "obj": "AC",
        "format": 2
    },
    "RSUB": {
        "obj": "4C",
        "format": 3
    },
    "SHIFTL": {
        "obj": "A4",
        "format": 2
    },
    "SHIFTR": {
        "obj": "A8",
        "format": 2
    },
    "SIO": {
        "obj": "F0",
        "format": 1
    },
    "SSK": {
        "obj": "EC",
        "format": 3
    },
    "STA": {
        "obj": "0C",
        "format": 3
    },
    "STB": {
        "obj": "78",
        "format": 3
    },
    "STCH": {
        "obj": "54",
        "format": 3
    },
    "STF": {
        "obj": "80",
        "format": 3
    },
    "STI": {
        "obj": "D4",
        "format": 3
    },
    "STL": {
        "obj": "14",
        "format": 3
    },
    "STS": {
        "obj": "7C",
        "format": 3
    },
    "STSW": {
        "obj": "E8",
        "format": 3
    },
    "STT": {
        "obj": "84",
        "format": 3
    },
    "STX": {
        "obj": "10",
        "format": 3
    },
    "SUB": {
        "obj": "1C",
        "format": 3
    },
    "SUBF": {
        "obj": "5C",
        "format": 3
    },
    "SUBR": {
        "obj": "94",
        "format": 2
    },
    "SVC": {
        "obj": "B0",
        "format": 2
    },
    "TD": {
        "obj": "E0",
        "format": 3
    },
    "TIO": {
        "obj": "F8",
        "format": 1
    },
    "TIX": {
        "obj": "2C",
        "format": 3
    },
    "TIXR": {
        "obj": "B8",
        "format": 2
    },
    "WD": {
        "obj": "DC",
        "format": 3
    }
}



def set_bonus(value):
    global bonus
    bonus = value
    print(f"bonus: {bonus}")
