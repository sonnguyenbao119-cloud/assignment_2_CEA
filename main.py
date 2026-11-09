"""A small 16-bit virtual computer with a fetch-decode-execute cycle."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VirtualPC:
    memory: list[int] = field(default_factory=lambda: [0] * 256)
    registers: list[int] = field(default_factory=lambda: [0] * 4)
    pc: int = 0
    zero: bool = False
    halted: bool = False
    output: list[int] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)

    def load(self, words: list[int], start: int = 0) -> None:
        if start < 0 or start + len(words) > len(self.memory):
            raise ValueError("Program does not fit in memory")
        for offset, word in enumerate(words):
            self.memory[start + offset] = word & 0xFFFF
        self.pc = start
        self.halted = False

    def _signed(self, value: int) -> int:
        value &= 0xFFFF
        return value - 0x10000 if value & 0x8000 else value

    def step(self) -> None:
        if self.halted:
            return
        if not 0 <= self.pc < len(self.memory):
            raise RuntimeError(f"Program counter out of range: {self.pc}")
        address = self.pc
        instruction = self.memory[self.pc]
        self.pc += 1
        opcode = (instruction >> 12) & 0xF
        a = (instruction >> 8) & 0xF
        b = (instruction >> 4) & 0xF
        imm = instruction & 0xFF
        detail = ""

        if opcode == 0x0:  # HALT
            self.halted = True
            detail = "halt"
        elif opcode == 0x1:  # LDI rd, imm8 (signed)
            self._check_reg(a)
            self.registers[a] = self._signed(imm)
            detail = f"R{a} <- {self.registers[a]}"
        elif opcode == 0x2:  # ADD rd, rs
            self._check_reg(a); self._check_reg(b)
            self.registers[a] = self._signed(self.registers[a] + self.registers[b])
            self.zero = self.registers[a] == 0
            detail = f"R{a} <- R{a} + R{b} = {self.registers[a]}"
        elif opcode == 0x3:  # SUB rd, rs
            self._check_reg(a); self._check_reg(b)
            self.registers[a] = self._signed(self.registers[a] - self.registers[b])
            self.zero = self.registers[a] == 0
            detail = f"R{a} <- R{a} - R{b} = {self.registers[a]}"
        elif opcode == 0x4:  # LOAD rd, [address]
            self._check_reg(a); self._check_addr(imm)
            self.registers[a] = self._signed(self.memory[imm])
            detail = f"R{a} <- M[{imm}] = {self.registers[a]}"
        elif opcode == 0x5:  # STORE rs, [address]
            self._check_reg(a); self._check_addr(imm)
            self.memory[imm] = self.registers[a] & 0xFFFF
            detail = f"M[{imm}] <- R{a} = {self.registers[a]}"
        elif opcode == 0x6:  # JMP address
            self._check_addr(imm); self.pc = imm
            detail = f"PC <- {imm}"
        elif opcode == 0x7:  # JZ address
            if self.zero:
                self._check_addr(imm); self.pc = imm
                detail = f"zero flag set; PC <- {imm}"
            else:
                detail = "zero flag clear; continue"
        elif opcode == 0x8:  # OUT rs
            self._check_reg(a); self.output.append(self.registers[a])
            detail = f"output {self.registers[a]}"
        else:
            raise RuntimeError(f"Invalid opcode 0x{opcode:X} at address {address}")
        self.trace.append(
            f"{address:03d}: {instruction:04X} op={opcode:X} {detail} | "
            f"PC={self.pc:03d} R={self.registers} Z={int(self.zero)}"
        )

    def run(self, max_steps: int = 1000) -> list[str]:
        steps = 0
        while not self.halted:
            if steps >= max_steps:
                raise RuntimeError(f"Execution stopped after {max_steps} steps (possible loop)")
            self.step()
            steps += 1
        return self.trace

    def _check_reg(self, index: int) -> None:
        if not 0 <= index < len(self.registers):
            raise RuntimeError(f"Invalid register R{index}")

    def _check_addr(self, address: int) -> None:
        if not 0 <= address < len(self.memory):
            raise RuntimeError(f"Memory address out of range: {address}")


def assemble(source: str) -> list[int]:
    """Assemble labels and the documented mnemonic syntax into 16-bit words."""
    lines = []
    labels: dict[str, int] = {}
    pc = 0
    for raw in source.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" in line:
            label, line = line.split(":", 1)
            labels[label.strip()] = pc
            line = line.strip()
            if not line:
                continue
        lines.append(line)
        pc += 1
    words = []
    for line in lines:
        parts = line.replace(",", " ").split()
        op, args = parts[0].upper(), parts[1:]
        if op == "HALT": words.append(0x0000)
        elif op == "LDI":
            rd, value = _reg(args[0]), int(args[1], 0)
            if not -128 <= value <= 255: raise ValueError("LDI immediate must fit in 8 bits")
            words.append(0x1000 | rd << 8 | (value & 0xFF))
        elif op in ("ADD", "SUB"):
            rd, rs = _reg(args[0]), _reg(args[1])
            words.append((0x2000 if op == "ADD" else 0x3000) | rd << 8 | rs << 4)
        elif op in ("LOAD", "STORE"):
            reg = _reg(args[0]); target = args[1]
            address = labels[target] if target in labels else int(target, 0)
            words.append((0x4000 if op == "LOAD" else 0x5000) | reg << 8 | _byte(address))
        elif op in ("JMP", "JZ"):
            target = args[0]
            address = labels[target] if target in labels else int(target, 0)
            words.append((0x6000 if op == "JMP" else 0x7000) | _byte(address))
        elif op == "OUT": words.append(0x8000 | _reg(args[0]) << 8)
        else: raise ValueError(f"Unknown instruction: {op}")
    return words


def _reg(token: str) -> int:
    token = token.upper()
    if not token.startswith("R") or not token[1:].isdigit() or not 0 <= int(token[1:]) < 4:
        raise ValueError(f"Register must be R0-R3: {token}")
    return int(token[1:])


def _byte(value: int) -> int:
    if not 0 <= value <= 255: raise ValueError(f"Value must fit in 8 bits: {value}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Mini16 Virtual PC assembly program")
    parser.add_argument("program", nargs="?", type=Path, default=Path(__file__).with_name("example.asm"))
    parser.add_argument("--max-steps", type=int, default=1000)
    args = parser.parse_args()
    machine = VirtualPC()
    machine.load(assemble(args.program.read_text(encoding="utf-8")))
    machine.run(args.max_steps)
    print("Execution trace")
    print("\n".join(machine.trace))
    print(f"\nFinal registers: {machine.registers}")
    print(f"Output: {machine.output}")


if __name__ == "__main__":
    main()
