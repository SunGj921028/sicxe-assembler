import os
import argparse

import config
from config import output_folder, input_folder
from src.assembler import MyAssembler

def main():
    #! Initial value of variables
    input_path = ""
    output_path = ""
    
    # Parser setting
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-i", "--input", type=str, 
                       help="Input file name in the input folder (Required)\n\n"
                            "Example: python main.py -i source.asm\n")
    parser.add_argument("-o", "--output", type=str, 
                       help="Output file name for the object program (Optional)\n\n"
                            "Default: object_program_output.txt\n",
                       default="object_program_output.txt")
    parser.add_argument("-b", "--bonus", action="store_true", 
                       help="Enable bonus features (Optional)\n\n"
                            "Default: False\n")
    
    try:
        args = parser.parse_args()
        
        #! Check input file
        if not args.input or args.input.strip() == "":  # 檢查是否提供 -i 參數
           parser.error("Input file name (-i/--input) is required")
        #! Check file extension (optional)
        if not args.input.endswith('.asm') and not args.input.endswith('.txt'):
            parser.error("Input file must have a .asm extension")
        
        #! Check output file
        if not args.output or args.output.strip() == "":  # 檢查是否提供 -o 參數
            parser.error("Output file name (-o/--output) is required")
        
        #! Combine input path
        input_path = os.path.join(input_folder, args.input)
        output_path = os.path.join(output_folder, args.output)
        
        if not input_path:
            parser.error("Input file path (-i/--input) is required")
        if not os.path.exists(input_path):
            parser.error(f"Input file '{args.input}' does not exist")
        
        #! Check bonus flag
        config.set_bonus(args.bonus)

        #? Print order information
        print(f"Input file is at: {input_path}")
        print(f"Output file is at: {output_folder}")
        if config.bonus:
            print("Bonus mode is on")
        else:
            print("Bonus mode is off")
            
        #! Start parsing
        my_assembler = MyAssembler(input_path, output_path)
        my_assembler.assemble_file()

    except (argparse.ArgumentError, argparse.ArgumentTypeError) as e:
        parser.error(str(e))
    except Exception as e:
        parser.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()

