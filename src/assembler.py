from typing import List

from .corefunc.section import Section
from .corefunc.analyzer import Analyzer

from .io.preprocessor import Preprocessor
from .io.writer import ObjectFileWriter

from config import output_folder


class MyAssembler:
    """
    SIC/XE 組譯器的主要類別。
    負責協調整個組譯過程，包括：
    - 載入並管理指令處理器
    - 協調預處理、組譯和輸出過程
    - 錯誤處理和日誌記錄
    """
    def __init__(self, input_path: str, output_path: str):
        self.sections: List[Section] = []
        self.preprocessor = Preprocessor()
        self.writer = ObjectFileWriter()
        #! File Path setting
        self.input_path = input_path
        self.output_path = output_path

    def preprocess(self) -> None:
        try:
            print("-------------------------------------------------")
            print(f"Starting preprocessing of {self.input_path}")
            self.sections = self.preprocessor.process(self.input_path)
            print(f"Preprocessing completed. Found {len(self.sections)} sections")
            print("-------------------------------------------------\n")
        except FileNotFoundError:
            print(f"Input file {self.input_path} not found")
            raise
        except ValueError as e:
            print(f"Invalid input format: {str(e)}")
            raise

    def assemble(self) -> None:
        try:
            print("---Starting assembly process---")
            
            for section_index, section in enumerate(self.sections, 1):
                print(f"Processing section {section_index}: {section.name}")
                
                print("-------------------------------------------------")
                #! Pass 1
                print("Pass 1")
                section.pass1()
                print("Pass 1 completed")
                print("-------------------------------------------------")
                
                #! Pass 2
                print("Pass 2")
                section.pass2()
                print("Pass 2 completed")
                print("-------------------------------------------------\n")
                
                #! 分析
                analyzer = Analyzer(section)
                analyzer.analyze("all") #! print on console
                
            print("Assembly process completed successfully")
        except Exception as e:
            print(f"Assembly failed: {str(e)}")
            raise

    def write_object_files(self) -> None:
        try:
            print(f"Writing object files to {self.output_path}")
            
            # 打開一次目標檔案
            with open(self.output_path, "w") as file:
                # 為每個區段寫入同一個目標檔案
                print('\nWrite object file for section...')
                for idx, section in enumerate(self.sections, 1):
                    self.writer.write_section(section, file)
                    file.write("\n")  # 添加區段間的分隔符（可選）
                    print(f"Written section {idx} to {self.output_path}")
                
            print("All object files written successfully")
            print("-------------------------------------------------\n")
            
        except IOError as e:
            print(f"Failed to write object files: {str(e)}")
            raise

    def assemble_file(self) -> None:
        #! 呼叫的 entry point
        print(f"Starting assembly of {self.input_path}")
        
        try:
            self.preprocess()           #! 讀取檔案並產生 sections
            self.assemble()             #! 組譯（處理包含符號表、修改記錄、指令、literal pool、program block）
            self.write_object_files()   #! 寫入目標檔案
            print("Assembly completed successfully !!!!")
            print(f"Please see the object program(s) in the {output_folder}")
            print("-------------------------------------------------\n")
            
        except Exception as e:
            print(f"Assembly failed: {str(e)}")
            raise
        finally:
            # 清理任何暫存資源
            self.sections = []
