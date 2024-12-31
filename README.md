# SIC/XE-assembler
A SIC/XE assembler made from python.

---

### How to use
- Windows, Linux 環境
- 請準備 **python 3.11** 以上的環境，並安裝所需套件（tabulate）
  - 可以執行 `pip install -r requirements.txt` 來自動安裝

- 程式執行方式可以直接下指令，如下
  ```py
  python main.py -i [輸入檔案名稱] -o [輸出檔案名稱] -b
  ```

---

### File architecture
```
SICXE_assembler/
├── main.py                         # 程式進入點
├── config.py                       # 設定檔（放一些全域變數或 table）
├── requirements.txt                # 專案依賴安裝（包含 tabulate）
├── src/
│   ├── __init__.py
│   ├── assembler.py                # 主要的組譯器 class，用來呼叫其他的功能
│   ├── corefunc/
│   │   ├── __init__.py
│   │   ├── analyzer.py             # 新增的分析器
│   │   ├── literal.py              # Literal 管理與 LITTAB 更新
│   │   ├── objectCode.py           # object code 生成
│   │   └── section.py              # 每個 section 的處理
│   ├── io/
│   │   ├── __init__.py
│   │   ├── preprocessor.py         # 預處理器
│   │   └── writer.py               # 寫 object program
│   └── models/
│       ├── __init__.py
│       └── dataTypes.py            # 資料型別定義
├── input/                          # 輸入檔案（測試檔案）的資料夾
│   └── *.asm or *.txt              # 組合語言檔案 .asm(txt)
└── output/                         # 輸出檔案的資料夾
    └── *.txt                       # Object program 結果
```

---

### Flow chart of assembler
![image](https://github.com/SunGj921028/sicxe-assembler/blob/main/img/flowChart.png)

---


### Class architecture
- **Location**：
  - 定義每個指令的記憶體位置相關資訊
- **Symbol**：
  - 定義標籤的儲存內容（name, address, is_external）
- **ModificationRecord**：
  - 定義修改紀錄的儲存內容（location, length, sign, reference）
- **Literal**：
  - 定義 literal 的儲存內容（name, data, used_count）
- **OpcodeEntry（OpcodeTable）**：
  - 定義 objectCode 的指令儲存資訊（opCode, format, description, type）
- **Instruction**：
  - 定義每個指令的儲存內容（index, formatType, symbol, mnemonic, operand, objectCode, location）

---

### Implementation Includes
- Format 1, 2, 3, 4 instruction
- Assembly Directive
  - START
  - WORD
  - BYTE
  - BASE
  - RESW
  - RESB
  - USE
  - EXTDEF
  - CSECT
  - EXTREF
  - LTORG
  - END
  - EQU
- **Object Programs**
  - H, T, M, D, R records
- **Table**
  - SYMTAB
  - LITTAB
  - EXTREF Table
  - EXTDEF Table
  - Instruction Table
- **Literals**
  - =C'EOF', =X'01'
  - LTORG
- **Symbol-defining Statements**
  - EQU
  - ORG
- **Program Blocks**
  - USE
  - USE CBLCKS
  - USE CDATA
- **Control Sections**
  - CSECT
