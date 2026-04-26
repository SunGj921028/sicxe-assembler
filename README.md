# SIC/XE Assembler

以 Python 實作的 SIC/XE two-pass assembler，支援多數常見指令格式與進階組譯功能（literal pool、program block、control section、external symbol），可輸出標準 object program records。

---

## Project Highlights

- **Two-pass assembler pipeline**：先建表、算位址，再產生 object code
- **SIC/XE format 1-4 完整支援**：包含 format 3/4 的位址模式與 flags 計算
- **Relocatable object program**：輸出 `H/T/M/E`，並支援 `D/R`（EXTDEF/EXTREF）
- **Advanced assembler features**：`USE`、`CSECT`、`LTORG`、`EQU`、`ORG`
- **Built-in analyzer**：可列印 SYMTAB、LITTAB、EXTREF/EXTDEF、Modification Records、Instruction Table 方便除錯與展示

---

## Tech Stack

- **Language**: Python 3.11+
- **CLI**: `argparse`
- **Data Modeling**: `dataclasses`, `typing`
- **Table Visualization**: `tabulate`

---

## How It Works

### 1) Preprocess

- 讀取 source file，去註解、切分欄位（symbol/mnemonic/operand）
- 驗證 mnemonic 是否存在於 opcode/directive table
- 依 `CSECT` 切分為多個 section

### 2) Pass 1

- 建立與更新：
  - `SYMTAB`
  - `EXTDEF` / `EXTREF`
  - `LITTAB`（在 `LTORG`/`END` 時展開）
- 計算 location counter 與每行指令位址
- 處理 `USE` program blocks、`EQU`/`ORG` expression
- 產生部分 modification records（外部參照與可重定位需求）

### 3) Pass 2

- 根據 format 1/2/3/4 產生 object code
- format 3/4 計算 `nixbpe` flags、PC-relative/Base-relative displacement
- 補齊 modification records

### 4) Object File Writing

- 依 section 輸出 object program records：
  - `H` Header
  - `D` External Definition
  - `R` External Reference
  - `T` Text
  - `M` Modification
  - `E` End

---

## Supported Features

### Instruction Formats

- Format 1
- Format 2
- Format 3
- Format 4 (`+` extended format)

### Directives

- `START`, `END`
- `WORD`, `BYTE`
- `RESW`, `RESB`
- `BASE`
- `EQU`, `ORG`
- `LTORG`
- `USE`
- `CSECT`
- `EXTDEF`, `EXTREF`

### Addressing / Relocation

- Immediate (`#`)
- Indirect (`@`)
- Indexed (`,X`)
- PC-relative / Base-relative
- External symbol relocation via modification records

---

## Project Structure

```text
sicxe-assembler/
├── main.py                    # CLI entry point
├── config.py                  # opcode/register/directive tables and global settings
├── requirments.txt            # project dependencies
├── input/                     # sample source files
├── output/                    # assembled object outputs
└── src/
    ├── assembler.py           # orchestration of preprocess/pass1/pass2/write
    ├── models/
    │   └── dataTypes.py       # core dataclasses (Instruction, Symbol, Literal, etc.)
    ├── io/
    │   ├── preprocessor.py    # source parsing and section splitting
    │   └── writer.py          # H/D/R/T/M/E record writing
    └── corefunc/
        ├── section.py         # pass1/pass2 logic per section
        ├── objectCode.py      # opcode generation and format-specific encoding
        ├── literal.py         # literal pool management
        └── analyzer.py        # table/report output for inspection
```

---

### Flow chart of assembler
![image](https://github.com/SunGj921028/sicxe-assembler/blob/main/img/flowChart.png)

---

## Run Locally

### 1) Install dependencies

```bash
pip install -r requirments.txt
```

### 2) Run assembler

```bash
python main.py -i <input_file> -o <output_file> -b
```

Parameters:

- `-i, --input` (required): input file under `input/` (`.asm` or `.txt`)
- `-o, --output` (optional): output file name (default: `object_program_output.txt`)
- `-b, --bonus` (optional flag): enable advanced/bonus processing path

Example:

```bash
python main.py -i code1.asm -o code1_out.txt -b
```

---

## Talking Points

- 將 assembler 分層為 parsing / pass logic / code generation / writer，降低模組耦合
- 用 dataclass 建立清楚的 instruction/symbol/modification record 資料模型
- 在 format 3/4 實作定址模式與 relocation，貼近系統軟體課程的核心能力
- 支援多 section、多 block、external symbol，超越最基本 SIC assembler

---

## Known Limitations

- 錯誤回報仍偏 CLI log 風格，缺乏結構化診斷輸出
- 表達式解析目前以 Python `eval` 邏輯為核心（雖有處理流程，仍可再收斂為更嚴格語法分析器）
- 測試目前以範例檔驗證為主，尚未有完整自動化單元測試

---

## Future Improvements

- 加入 parser/assembler 的單元測試與 golden-file regression tests
- 建立更嚴格的 expression parser（取代通用 eval 型態）
- 強化錯誤定位（檔名、行號、欄位）與 diagnostics 格式
- 增加 listing file 輸出（含 LOC/object code/table snapshot）
