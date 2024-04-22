from collections import namedtuple
from dataclasses import dataclass
from enum        import Enum
from typing      import NamedTuple

from DependencyTable import DependencyTable

RegType = Enum('RegType', ['GENERAL', 'PREDICATE', 'LC', 'EC', 'RRB'])
Reg = namedtuple('Reg', ['type', 'idx'])

@dataclass
class Instruction:
    opcode: str
    rd : NamedTuple
    rs1: NamedTuple
    rs2: NamedTuple
    imm: int

class VLIW470:
    @dataclass
    class ExUnit:
        ALU = 2
        MUL = 1
        MEM = 1
        BR  = 1
    
    iCache: list[Instruction]

    rrb: int # rotating register base
    lc : int # loop   count register
    ec : int # epilog count register
    depTable: DependencyTable

    def __init__(self, insts: list[str]) -> None:
        for inst in insts:
            self.iCache.append(self.decode(inst))
        self.depTable = DependencyTable(self.iCache)
    
    def parseReg(self, reg: str) -> Reg:
        ''' parse a register '''
        if reg[0] == 'x':
            return Reg(RegType.GENERAL, int(reg[1:]))
        elif reg[0] == 'p':
            return Reg(RegType.PREDICATE, int(reg[1:]))
        elif reg == 'LC':
            return Reg(RegType.LC, None)

    def decode(self, inst: str) -> Instruction:
        ''' decode an instruction '''
        opcode, regs = inst.split(' ', 1)
        if opcode == 'add' or \
           opcode == 'sub' or \
           opcode == 'mulu':
           rd, rs1, rs2 = map(lambda x : self.parseReg(x.strip()), regs.split(','))
           return Instruction(opcode = opcode,
                              rd = rd,
                              rs1 = rs1,
                              rs2 = rs2,
                              imm = None) 
        elif opcode == 'addi':
            rd, rs1, imm = map(lambda x : x.strip(), regs.split(','))
            return Instruction(opcode = 'addi',
                               rd = self.parseReg(rd),
                               rs1 = self.parseReg(rs1),
                               rs2 = None,
                               imm = int(imm))
        elif opcode == 'ld':
            rd, addr = regs.split(',', 1)
            offset, base = addr.split('(', 1)
            return Instruction(opcode = 'ld',
                               rd = self.parseReg(rd.strip()),
                               rs1 = self.parseReg(base.strip()[ :-1]), # get rid of ')'
                               rs2 = None,
                               imm = int(offset, 0)) # Offset may be a hex.
        elif opcode == 'st':
            # semantics of `st rs2, offset(rs1)`: MEM[rs1 + offset] ← rs2
            content, addr = regs.split(',', 1)
            offset, base = addr.split('(', 1)
            return Instruction(opcode = 'st',
                               rd = None,
                               rs1 = self.parseReg(base.strip()[ :-1]), # get rid of ')'
                               rs2 = self.parseReg(content.strip()),
                               imm = int(offset, 0)) # Offset may be a hex.
        elif opcode == 'loop':
            return Instruction(opcode = 'loop',
                               rd = None,
                               rs1 = None,
                               rs2 = None,
                               imm = int(regs.strip())) # jump address
        elif opcode == 'mov':
            rd, rs1 = map(lambda x : x.strip(), regs.split(','))
            if rs1[0] == 'x' or rs1 == 'LC': # `mov rd, rs1`
                return Instruction(opcode = 'mov',
                                   rd = self.parseReg(rd),
                                   rs1 = self.parseReg(rs1),
                                   rs2 = None,
                                   imm = None)
            else: # `mov rd, imm`
                return Instruction(opcode = 'mov',
                                   rd = self.parseReg(rd),
                                   rs1 = None,
                                   rs2 = None,
                                   imm = int(rs1))