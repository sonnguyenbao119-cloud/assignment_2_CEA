# Mini16 Virtual PC

A small educational virtual computer implementing an 8-bit-addressed memory with 16-bit instruction words, four general-purpose registers, a zero flag, and a fetch-decode-execute interpreter.

## Run

Requires Python 3.10 or later. From this directory:

```powershell
python main.py
python main.py path\to\program.asm --max-steps 1000
```

The included program adds 7 and 5. Its output is `12`. The simulator prints one trace row per instruction and the final register state.

## Instruction format

Each instruction is a 16-bit word: `[opcode:4][field A:4][field B:4][immediate:8]`. Opcodes are `0 HALT`, `1 LDI`, `2 ADD`, `3 SUB`, `4 LOAD`, `5 STORE`, `6 JMP`, `7 JZ`, and `8 OUT`. Registers are R0-R3. LDI accepts signed values -128 through 127 (and their unsigned 8-bit encodings). Memory has 256 words. Arithmetic wraps to signed 16-bit results.

Assembly operands are comma-separated. Labels may be used as jump or memory addresses; addresses and immediates accept decimal or `0x` notation. `JZ` branches when the zero flag set by the most recent ADD or SUB is true.

## Repository files

- `main.py`: assembler, CPU state, instruction execution, trace and command-line entry point.
- `example.asm`: sample program.
- `report.docx` and `report.pdf`: project report.
