from __future__ import annotations

import re
import sys
from ast import literal_eval
from enum import IntEnum
from typing import Any, Literal, Union # Required for Literal type hint

class Instruction(IntEnum):
    NOP = 0x00
    POP = 0x01
    ADD = 0x02
    SUB = 0x03
    MUL = 0x04
    DIV = 0x05
    MOD = 0x06
    AND = 0x07
    OR = 0x08
    XOR = 0x09
    NOT = 0x0A
    CALL = 0x0B
    JMP = 0x0C
    LEA = 0x0D
    PUSH1 = 0x0E
    PUSH2 = 0x0F
    PUSH4 = 0x10
    PUSH8 = 0x11
    MODCALL = 0x12
    JZ = 0x13
    JB = 0x14
    JA = 0x15
    DUP = 0x16
    HLT = 0x17
    SWAP = 0x18 # Added in a previous hypothetical change, keeping it for consistency

# Type for parsed instructions
_OpType = tuple[Instruction] | tuple[Instruction, int | str]
# Type for DB directive data
_DbDirectiveType = tuple[Literal["DB_DIRECTIVE"], list[int]]
# Combined type for any parsable item that generates bytecode or occupies space
_ParsedItem = Union[_OpType, _DbDirectiveType]


_LABEL_REGEX = re.compile(r"^\[(?P<name>.*)\]$")
_TIMES_REGEX = re.compile(
    r"^times\s+(?P<times>\d+)\s+(?P<instruction>.+)$", re.IGNORECASE
)
_PUSH_SIZE = {
    Instruction.PUSH1: 1,
    Instruction.PUSH2: 2,
    Instruction.PUSH4: 4,
    Instruction.PUSH8: 8,
}


class AssemblyError(ValueError):
    def __init__(self, message: str, line_num: int | None = None, line_content: str | None = None):
        full_message = message
        if line_num is not None and line_content is not None:
            full_message = f"Error on line {line_num} ('{line_content.strip()}'): {message}"
        elif line_num is not None:
            full_message = f"Error on line {line_num}: {message}"
        super().__init__(full_message)
        self.line_num = line_num
        self.line_content = line_content


def _preprocess_assembly(asm: str, case_sensitive: bool) -> list[tuple[int, str, str]]:
    """
    Preprocesses the assembly code string.
    Removes comments, empty lines, handles case sensitivity, and tracks original line numbers.
    Expands 'times' directives.
    Returns: list of (original_line_number, original_line_text, cleaned_and_case_adjusted_line_content)
    """
    processed_lines_with_meta: list[tuple[int, str, str]] = []
    raw_lines = asm.splitlines()
    
    temp_lines_to_process: list[tuple[int, str, str]] = []
    for i, line_content in enumerate(raw_lines):
        temp_lines_to_process.append((i + 1, line_content, line_content))

    idx = 0
    while idx < len(temp_lines_to_process):
        line_num, original_line_text, current_processing_text = temp_lines_to_process[idx]
        idx += 1

        line_for_logic = current_processing_text.split(';', 1)[0].strip()

        if not case_sensitive:
            line_for_logic = line_for_logic.casefold()
        
        if not line_for_logic:
            continue

        times_match = _TIMES_REGEX.match(line_for_logic)
        if times_match:
            try:
                times_count_str = times_match.group("times")
                times_count = int(times_count_str)
                instruction_to_repeat = times_match.group("instruction").strip()
                if times_count < 0:
                    raise AssemblyError(f"Negative repeat count ({times_count}) for 'times' directive.", line_num, original_line_text)
                
                expansion = [(line_num, original_line_text, instruction_to_repeat)] * times_count
                temp_lines_to_process[idx:idx] = expansion
            except ValueError:
                 raise AssemblyError(f"Invalid number '{times_count_str}' for 'times' directive.", line_num, original_line_text)
            continue
        
        processed_lines_with_meta.append((line_num, original_line_text, line_for_logic))
        
    return processed_lines_with_meta


def _parse_single_line(
    line_num: int,
    line_content: str, 
    original_line_text: str, 
    constants: dict[str, int],
    case_sensitive_constants: bool
) -> tuple[Literal["instruction", "label", "constant_def", "db_directive"], Any]:
    """
    Parses a single preprocessed line of assembly.
    Returns a tuple indicating type and parsed data.
    """
    label_match = _LABEL_REGEX.match(line_content)
    if label_match:
        label_name = label_match.group("name")
        return "label", label_name

    components = [comp.strip() for comp in line_content.split(maxsplit=1)] # Split only on the first space for DB
    if not components:
        raise AssemblyError("Line became empty after splitting, unexpected.", line_num, original_line_text)

    keyword_raw = components[0]
    keyword_upper = keyword_raw.upper()

    # Constant definition: e.g., MY_CONST EQU 10
    # Need to split fully for this. Re-split if keyword might be a const name.
    full_components = [comp.strip() for comp in line_content.split()]
    if len(full_components) == 3 and full_components[1].upper() == "EQU":
        const_name_from_source = full_components[0]
        const_name_key = const_name_from_source if case_sensitive_constants else const_name_from_source.casefold()
        try:
            const_value_str = full_components[2]
            const_value = int(literal_eval(const_value_str))
            return "constant_def", (const_name_key, const_value, const_name_from_source)
        except (ValueError, SyntaxError) as e:
            raise AssemblyError(f"Invalid value '{full_components[2]}' for constant '{const_name_from_source}'. Details: {e}", line_num, original_line_text)

    # DB Directive: e.g., DB 10, 0xFF, 'A', "Hello"
    if keyword_upper == "DB":
        if len(components) < 2 or not components[1].strip():
            raise AssemblyError("DB directive requires arguments.", line_num, original_line_text)
        
        args_str = components[1]
        byte_values: list[int] = []
        
        # Simple comma-separated parser, allowing strings to contain commas if quoted.
        # This regex splits by comma, but respects commas inside quotes.
        # More robust parsing might be needed for complex escape sequences within strings.
        # For now, rely on literal_eval for individual items.
        
        # This is a tricky part: "DB 'a,b', 'c'" vs "DB 'a', 'b', 'c'"
        # A full CSV parser or more sophisticated regex is better.
        # Let's use a simpler split by comma and then try to stitch quoted strings.
        # This is a basic approach and might have limitations.
        
        raw_args = []
        current_arg = ""
        in_single_quote = False
        in_double_quote = False
        for char in args_str:
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            
            if char == ',' and not in_single_quote and not in_double_quote:
                raw_args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        raw_args.append(current_arg.strip()) # Add the last argument

        for arg_item_str in raw_args:
            if not arg_item_str:
                continue # Skip empty items that might result from trailing commas
            try:
                val = literal_eval(arg_item_str)
                if isinstance(val, int):
                    if not (0 <= val <= 255):
                        raise AssemblyError(f"Byte value '{arg_item_str}' out of range (0-255).", line_num, original_line_text)
                    byte_values.append(val)
                elif isinstance(val, str):
                    for char_in_str in val:
                        byte_val = ord(char_in_str)
                        if not (0 <= byte_val <= 255) : # Should not happen for typical strings
                             raise AssemblyError(f"Character '{char_in_str}' in string \"{val}\" is not a valid byte.", line_num, original_line_text)
                        byte_values.append(byte_val)
                else:
                    raise AssemblyError(f"Unsupported type for DB argument: '{arg_item_str}' (evaluates to {type(val)}).", line_num, original_line_text)
            except (ValueError, SyntaxError, TypeError) as e:
                raise AssemblyError(f"Invalid DB argument: '{arg_item_str}'. Details: {e}", line_num, original_line_text)
        return "db_directive", byte_values


    # Instruction parsing (use full_components for this)
    try:
        op = Instruction[keyword_upper] # keyword_upper is from components[0]
    except KeyError:
        raise AssemblyError(f"Unknown instruction or directive: '{keyword_raw}'", line_num, original_line_text)

    if len(full_components) == 1:
        return "instruction", (op,)
    elif len(full_components) == 2:
        arg_str = full_components[1]
        try:
            arg_val = int(literal_eval(arg_str))
        except (ValueError, SyntaxError): 
            constant_lookup_key = arg_str if case_sensitive_constants else arg_str.casefold()
            arg_val = constants.get(constant_lookup_key, arg_str) 
        return "instruction", (op, arg_val)
    else:
        raise AssemblyError(f"Invalid line format or too many components for instruction '{keyword_raw}'.", line_num, original_line_text)


def _resolve_addresses(
    parsed_items: list[tuple[int, str, _ParsedItem]], 
    labels_info: dict[int, tuple[int, str, str]], 
    case_sensitive_labels: bool
) -> dict[str, int]:
    """Calculates the bytecode address for each label, considering instructions and DB directives."""
    final_label_offsets: dict[str, int] = {} 
    current_address = 0
    label_definitions_meta: dict[str, tuple[int, str, str]] = {}

    for idx, (line_num, original_line, item_data) in enumerate(parsed_items):
        if idx in labels_info:
            label_line_num, label_original_line, label_name_from_source = labels_info[idx]
            label_key = label_name_from_source if case_sensitive_labels else label_name_from_source.casefold()
            
            if label_key in final_label_offsets:
                first_def_line_num, _, first_def_name = label_definitions_meta[label_key]
                raise AssemblyError(f"Label '{label_name_from_source}' redefined. First defined as '{first_def_name}' on line {first_def_line_num}.",
                                    label_line_num, label_original_line)
            final_label_offsets[label_key] = current_address
            label_definitions_meta[label_key] = (label_line_num, label_original_line, label_name_from_source)
        
        # Check if item_data is an _OpType (instruction)
        if isinstance(item_data, tuple) and len(item_data) > 0 and isinstance(item_data[0], Instruction):
            op = item_data[0]
            args = item_data[1:]
            current_address += 1  # Opcode
            if op in _PUSH_SIZE:
                if not args: 
                    raise AssemblyError(f"Instruction {op.name} expects an argument.", line_num, original_line)
                current_address += _PUSH_SIZE[op]
            elif args: 
                current_address += 1 + 8  # PUSH8 opcode + 8 bytes
        # Check if item_data is a _DbDirectiveType
        elif isinstance(item_data, tuple) and len(item_data) == 2 and item_data[0] == "DB_DIRECTIVE":
            byte_list = item_data[1]
            current_address += len(byte_list)
        else:
            # This case should not be reached if parsing is correct
            raise AssemblyError(f"Unknown item type encountered during address resolution on line {line_num}.", line_num, original_line)
            
    return final_label_offsets


def _generate_bytecode_for_item(
    item_data: _ParsedItem,
    final_label_offsets: dict[str, int],
    case_sensitive_labels: bool,
    line_num: int, 
    original_line_text: str 
) -> bytes:
    """Generates bytecode for a single parsed item (instruction or DB directive)."""
    bytecode_segment = bytearray()

    # Handle Instructions (_OpType)
    if isinstance(item_data, tuple) and len(item_data) > 0 and isinstance(item_data[0], Instruction):
        op_tuple = item_data # item_data is _OpType here
        op = op_tuple[0]
        args = op_tuple[1:] 
        arg_value_runtime = args[0] if args else None

        is_push_variant = op in _PUSH_SIZE
        has_argument_value = arg_value_runtime is not None

        if has_argument_value and not is_push_variant: 
            bytecode_segment.append(Instruction.PUSH8)
            resolved_numeric_arg: int
            if isinstance(arg_value_runtime, str): 
                label_name_for_lookup = arg_value_runtime
                label_key = label_name_for_lookup if case_sensitive_labels else label_name_for_lookup.casefold()
                resolved_address = final_label_offsets.get(label_key)
                if resolved_address is None:
                    raise AssemblyError(f"Undefined label: '{arg_value_runtime}'", line_num, original_line_text)
                resolved_numeric_arg = resolved_address
            elif isinstance(arg_value_runtime, int):
                resolved_numeric_arg = arg_value_runtime
            else: 
                raise AssemblyError(f"Invalid argument type '{type(arg_value_runtime).__name__}' for implicit PUSH8.", line_num, original_line_text)
            bytecode_segment += resolved_numeric_arg.to_bytes(8, "little")

        bytecode_segment.append(op) 

        if is_push_variant:
            if not has_argument_value: 
                raise AssemblyError(f"Instruction {op.name} expects an argument but none provided.", line_num, original_line_text)
            
            resolved_numeric_arg_push: int
            if isinstance(arg_value_runtime, str): 
                label_name_for_lookup = arg_value_runtime
                label_key = label_name_for_lookup if case_sensitive_labels else label_name_for_lookup.casefold()
                resolved_address = final_label_offsets.get(label_key)
                if resolved_address is None:
                    raise AssemblyError(f"Undefined label: '{arg_value_runtime}' used with {op.name}.", line_num, original_line_text)
                resolved_numeric_arg_push = resolved_address
            elif isinstance(arg_value_runtime, int):
                resolved_numeric_arg_push = arg_value_runtime
            else: 
                raise AssemblyError(f"Argument for {op.name} must be an integer or a resolvable label, got type '{type(arg_value_runtime).__name__}'.", line_num, original_line_text)
            bytecode_segment += resolved_numeric_arg_push.to_bytes(_PUSH_SIZE[op], "little")
    
    # Handle DB Directives (_DbDirectiveType)
    elif isinstance(item_data, tuple) and len(item_data) == 2 and item_data[0] == "DB_DIRECTIVE":
        byte_list = item_data[1]
        bytecode_segment.extend(byte_list)
    else:
        # This case should not be reached if parsing and item structure are correct
        raise AssemblyError(f"Unknown item type encountered during bytecode generation on line {line_num}.", line_num, original_line_text)
        
    return bytes(bytecode_segment)


def assemble(asm: str, case_sensitive: bool = False) -> bytes:
    case_sensitive_labels = case_sensitive
    case_sensitive_constants = case_sensitive

    try:
        preprocessed_asm_lines = _preprocess_assembly(asm, case_sensitive)
    except AssemblyError: 
        raise 

    parsed_items_with_meta: list[tuple[int, str, _ParsedItem]] = []
    constants: dict[str, int] = {} 
    labels_by_item_index: dict[int, tuple[int, str, str]] = {} 

    for line_num, original_line_text, cleaned_line_content in preprocessed_asm_lines:
        try:
            parse_type, parsed_data = _parse_single_line(
                line_num, cleaned_line_content, original_line_text, constants, case_sensitive_constants
            )

            if parse_type == "instruction":
                parsed_items_with_meta.append((line_num, original_line_text, parsed_data))
            elif parse_type == "db_directive":
                # parsed_data is the list of byte values
                parsed_items_with_meta.append((line_num, original_line_text, ("DB_DIRECTIVE", parsed_data)))
            elif parse_type == "label":
                label_name_from_parser = parsed_data 
                current_item_index = len(parsed_items_with_meta)
                labels_by_item_index[current_item_index] = (line_num, original_line_text, label_name_from_parser)
            elif parse_type == "constant_def":
                const_key, const_value, const_name_from_source = parsed_data
                if const_key in constants: 
                    raise AssemblyError(f"Constant '{const_name_from_source}' redefined.", line_num, original_line_text)
                constants[const_key] = const_value
        except AssemblyError: 
            raise
        except Exception as e: 
            raise AssemblyError(f"Unexpected parsing error: {e}", line_num, original_line_text)

    try:
        final_label_offsets = _resolve_addresses(parsed_items_with_meta, labels_by_item_index, case_sensitive_labels)
    except AssemblyError: 
        raise

    final_bytecode = bytearray()
    for line_num, original_line_text, item_data in parsed_items_with_meta:
        try:
            item_bytes = _generate_bytecode_for_item(
                item_data, final_label_offsets, case_sensitive_labels, line_num, original_line_text
            )
            final_bytecode.extend(item_bytes)
        except AssemblyError: 
            raise
        except Exception as e: 
             raise AssemblyError(f"Unexpected bytecode generation error: {e}", line_num, original_line_text)
             
    return bytes(final_bytecode)


if __name__ == "__main__":
    program_name, *argv = sys.argv
    if len(argv) not in [2, 3]: 
        print(f"Usage: {program_name} [--case-sensitive] <input file> <output file>")
        sys.exit(1)

    case_sensitive_arg = False
    input_file_arg = ""
    output_file_arg = ""

    if len(argv) == 3:
        if argv[0].lower() == "--case-sensitive":
            case_sensitive_arg = True
            input_file_arg = argv[1]
            output_file_arg = argv[2]
        else:
            print(f"Usage: {program_name} [--case-sensitive] <input file> <output file>")
            print(f"Unknown option: {argv[0]}")
            sys.exit(1)
    else: 
        input_file_arg = argv[0]
        output_file_arg = argv[1]

    try:
        with open(input_file_arg, "rt", encoding="utf-8") as file:
            asm_code_content = file.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file_arg}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file '{input_file_arg}': {e}")
        sys.exit(1)
    
    print(f"--- Assembling code from {input_file_arg} (Case-sensitive: {case_sensitive_arg}) ---")
    try:
        result_bytecode = assemble(asm_code_content, case_sensitive=case_sensitive_arg)
        print(f"Assembly successful. Outputting {len(result_bytecode)} bytes to {output_file_arg}")
        
        with open(output_file_arg, "wb") as file:
            file.write(result_bytecode)
        print(f"Successfully wrote bytecode to {output_file_arg}")

    except AssemblyError as e: 
        print(f"{e}") # Custom error already includes "Assembly Error:" and context
        sys.exit(1)
    except Exception as e: 
        print(f"An unexpected critical error occurred: {e}")
        sys.exit(1)
