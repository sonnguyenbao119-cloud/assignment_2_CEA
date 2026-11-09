from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path

OUT = Path(__file__).with_name("report.docx")
doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(.72); sec.bottom_margin = Inches(.72)
sec.left_margin = Inches(.82); sec.right_margin = Inches(.82)
styles = doc.styles
styles['Normal'].font.name = 'Aptos'; styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Aptos'); styles['Normal'].font.size = Pt(10)
styles['Normal'].paragraph_format.space_after = Pt(5)
for name, size, color in [('Title', 26, '183153'), ('Heading 1', 17, '183153'), ('Heading 2', 12, '167D9A')]:
    s=styles[name]; s.font.name='Aptos Display'; s._element.rPr.rFonts.set(qn('w:eastAsia'),'Aptos Display'); s.font.size=Pt(size); s.font.bold=True; s.font.color.rgb=RGBColor.from_string(color)

def para(text='', bold_start=None):
    p=doc.add_paragraph()
    if bold_start and text.startswith(bold_start):
        p.add_run(bold_start).bold=True; p.add_run(text[len(bold_start):])
    else: p.add_run(text)
    return p
def bullet(text): doc.add_paragraph(text, style='List Bullet')
def table(headers, rows, widths=None):
    t=doc.add_table(rows=1, cols=len(headers)); t.style='Light Shading Accent 1'
    for c,h in zip(t.rows[0].cells,headers): c.text=h
    for row in rows:
        cells=t.add_row().cells
        for c,v in zip(cells,row): c.text=str(v)
    return t
def page(): doc.add_page_break()

p=doc.add_paragraph(style='Title'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run('MINI16 VIRTUAL PC')
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run('A Small Instruction Set Simulator'); r.bold=True; r.font.size=Pt(15); r.font.color.rgb=RGBColor.from_string('167D9A')
para('Computer Architecture Project Report').alignment=WD_ALIGN_PARAGRAPH.CENTER
para('Implementation language: Python 3').alignment=WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('')
table(['Project item','Description'],[
    ('Processor','16-bit instruction words; four 16-bit general-purpose registers'),
    ('Memory','256 addressable 16-bit words'),
    ('Instruction set','Nine instructions: HALT, LDI, ADD, SUB, LOAD, STORE, JMP, JZ, OUT'),
    ('Program demonstration','Load 7 and 5, add, display 12, then halt'),
])
doc.add_paragraph('Prepared as a compact, explainable educational model of a computer system.')

doc.add_heading('Abstract',1)
para('Mini16 is a software model of a simple stored-program computer. It combines a small assembler with an interpreter that models registers, memory, a program counter, a zero flag, input/output behavior, and the fetch-decode-execute cycle. A sample assembly program loads two values, adds them, and displays the result. The design favors clarity: each instruction is one 16-bit word, memory has 256 words, and each executed instruction produces a trace line that exposes the processor state.')
doc.add_heading('1. Project goals and scope',1)
para('The project demonstrates how instruction encoding connects software to hardware organization. A program is assembled into machine words, placed in memory, and executed one instruction at a time. The model supports arithmetic, memory access, conditional and unconditional control flow, and an output operation. It is a teaching simulator rather than a full PC: it omits peripherals, operating systems, interrupts, protection, and cycle-accurate timing.')
doc.add_heading('2. System architecture',1)
para('The virtual processor contains four general-purpose registers (R0-R3), a program counter (PC), and one zero-status flag (Z). Main memory stores 256 words, each 16 bits. Instructions and data share this memory, which is the defining stored-program arrangement. The interpreter fetches an instruction from memory at PC, increments PC, decodes its fields, performs the operation, and records the updated state.')
table(['Component','Role'],[
    ('PC','Address of the next instruction; branch instructions replace it.'),
    ('R0-R3','Temporary operands and results for programs.'),
    ('Z flag','Set by ADD or SUB when the result is zero; read by JZ.'),
    ('Memory','256 words addressed 0 through 255; contains code and data.'),
    ('Output list','Collects integer values emitted by OUT.'),
    ('Control logic','Decodes the opcode and selects the operation and state updates.'),
])

doc.add_heading('3. Instruction set design',1)
para('Each instruction is a 16-bit word in the form [opcode:4][field A:4][field B:4][immediate:8]. The opcode selects the operation. Field A usually identifies a register, field B identifies a second register where needed, and the low byte holds an immediate value or address. Unused fields are zero. The assembler accepts readable mnemonics and labels, then encodes the corresponding words.')
table(['Opcode','Mnemonic','Operation'],[
    ('0','HALT','Stop execution.'),('1','LDI Rd, imm8','Load a signed 8-bit immediate into Rd.'),
    ('2','ADD Rd, Rs','Rd = Rd + Rs; update Z.'),('3','SUB Rd, Rs','Rd = Rd - Rs; update Z.'),
    ('4','LOAD Rd, addr','Rd = memory[addr].'),('5','STORE Rs, addr','memory[addr] = Rs.'),
    ('6','JMP addr','Set PC to addr.'),('7','JZ addr','Set PC to addr if Z is set.'),('8','OUT Rs','Append Rs to output.'),
])
para('Arithmetic results wrap to signed 16-bit values. LOAD and STORE address a single 16-bit memory word. LDI encodes its immediate in the low byte; values from -128 to 127 are directly expressible as signed immediates. The zero flag is updated only by ADD and SUB, so a JZ instruction tests the most recent arithmetic result.')

doc.add_heading('4. Execution process',1)
para('The fetch stage reads memory[PC] and increments PC so that it points to the sequential next instruction. The decode stage separates the opcode, register fields, and immediate byte using bit shifts and masks. The execute stage applies the decoded operation to registers, memory, flags, PC, output, or the halt state. A trace row records the fetched address, machine word, operation, and resulting processor state.')
table(['Step','Example: ADD R0, R1'],[
    ('Fetch','Read instruction word 0x2010 at the current PC.'),
    ('Decode','Opcode 2 means ADD; fields select destination R0 and source R1.'),
    ('Execute','Add R1 to R0, keep the low 16 bits, and set Z if result is zero.'),
    ('Next state','Continue at the already incremented PC and record the trace.'),
])

doc.add_heading('5. Demonstration program',1)
para('The included example.asm program performs five instructions:')
for line in ['LDI R0, 7','LDI R1, 5','ADD R0, R1','OUT R0','HALT']:
    p=doc.add_paragraph(); p.paragraph_format.left_indent=Inches(.3); r=p.add_run(line); r.font.name='Consolas'; r.font.size=Pt(10)
para('After execution, R0 contains 12, R1 contains 5, the output list contains [12], and the halted state is true. The trace lets a learner follow PC and register changes instruction by instruction. The command-line runner also enforces a maximum step count to stop accidental infinite loops.')

doc.add_heading('6. Implementation and limitations',1)
para('The implementation is in main.py. VirtualPC stores machine state and implements one instruction per step. assemble performs a two-pass assembly: the first pass assigns addresses to labels, and the second pass encodes instructions. The command-line interface loads an assembly file, runs it, and prints the trace and final values. Invalid opcodes, registers, addresses, oversized programs, and step-limit exhaustion produce explicit errors.')
para('The model uses a single memory space and a single execution stream. It has no pipeline or cache, so it does not represent instruction overlap or cache timing. It also has no interrupt system or general-purpose input device. These are possible extensions, but keeping the first version small makes its core architecture easier to inspect and explain.')
doc.add_heading('7. Conclusion',1)
para('Mini16 connects an instruction set to a working processor model. Its compact encoding, explicit state, simple assembler, and execution trace show how a CPU interprets instructions and moves data. The example confirms the complete path from assembly source to encoded instructions, arithmetic execution, and observable output.')
doc.add_heading('References',1)
para('Patterson, D. A., & Hennessy, J. L. (2021). Computer Organization and Design RISC-V Edition: The Hardware/Software Interface (2nd ed.). Morgan Kaufmann.')
para('Mano, M. M., & Ciletti, M. D. (2017). Digital Design (6th ed.). Pearson.')
para('Python Software Foundation. (2026). Python 3 documentation. https://docs.python.org/3/ (accessed 9 November 2026).')

# Page number field in footer
footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
footer.add_run('Mini16 Virtual PC  |  ')
field=OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'PAGE'); footer._p.append(field)
doc.save(OUT)
print(OUT)
