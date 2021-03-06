# Copyright (c) 2014, Fundacion Dr. Manuel Sadosky
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import unittest

from barf.arch import ARCH_X86_MODE_32
from barf.arch.x86.x86base import X86ArchitectureInformation
from barf.arch.x86.x86parser import X86Parser
from barf.arch.x86.x86translator import X86Translator
from barf.core.reil import ReilEmulator
from barf.core.reil import ReilMemory
from barf.core.reil import ReilParser


class ReilMemoryTests(unittest.TestCase):

    def test_write_read_byte_1(self):
        address_size = 32
        memory = ReilMemory(address_size)

        addr = 0x00001000
        write_val = 0xdeadbeef

        memory.write(addr, 32, write_val)
        read_val = memory.read(addr, 32)

        self.assertEqual(write_val, read_val)

    def test_write_read_byte_2(self):
        address_size = 32
        memory = ReilMemory(address_size)

        addr = 0x00001000
        write_val = 0xdeadbeef

        memory.write(addr, 32, write_val)
        read_val = memory.read(addr, 32)

        self.assertEqual(write_val, read_val)

        addr = 0x00001001
        write_val = 0x1234

        memory.write(addr, 16, write_val)
        read_val = memory.read(addr, 16)

        self.assertEqual(write_val, read_val)

    def test_write_read_byte_3(self):
        address_size = 32
        memory = ReilMemory(address_size)

        addr = 0x00001000
        write_val = 0xdeadbeefcafecafe

        memory.write(addr, 64, write_val)
        read_val = memory.read(addr, 64)

        self.assertEqual(write_val, read_val)

    def test_write_read_byte_4(self):
        address_size = 32
        memory = ReilMemory(address_size)

        addr0 = 0x00001000
        write_val = 0xdeadbeef

        memory.write(addr0, 32, write_val)
        read_val = memory.read(addr0, 32)

        self.assertEqual(write_val, read_val)

        addr1 = 0x00004000
        write_val = 0xdeadbeef

        memory.write(addr1, 32, write_val)
        read_val = memory.read(addr1, 32)

        self.assertEqual(write_val, read_val)

        addrs = memory.read_inverse(0xdeadbeef, 32)

        self.assertEqual(addr0, addrs[0])
        self.assertEqual(addr1, addrs[1])


class ReilEmulatorTests(unittest.TestCase):

    def setUp(self):
        self._arch_info = X86ArchitectureInformation(ARCH_X86_MODE_32)

        self._emulator = ReilEmulator(self._arch_info.address_size)

        self._emulator.set_arch_registers(self._arch_info.registers_gp_all)
        self._emulator.set_arch_registers_size(self._arch_info.registers_size)
        self._emulator.set_reg_access_mapper(self._arch_info.alias_mapper)

        self._asm_parser = X86Parser()
        self._translator = X86Translator()

    def test_add(self):
        asm_instrs  = self._asm_parser.parse("add eax, ebx")

        self.__set_address(0xdeadbeef, [asm_instrs])

        reil_instrs = self._translator.translate(asm_instrs)

        regs_initial = {
            "eax" : 0x1,
            "ebx" : 0x2,
        }

        regs_final, _ = self._emulator.execute_lite(
            reil_instrs,
            context=regs_initial
        )

        self.assertEqual(regs_final["eax"], 0x3)
        self.assertEqual(regs_final["ebx"], 0x2)

    def test_loop(self):
        # 0x08048060 : b8 00 00 00 00   mov eax,0x0
        # 0x08048065 : bb 0a 00 00 00   mov ebx,0xa
        # 0x0804806a : 83 c0 01         add eax,0x1
        # 0x0804806d : 83 eb 01         sub ebx,0x1
        # 0x08048070 : 83 fb 00         cmp ebx,0x0
        # 0x08048073 : 75 f5            jne 0x0804806a

        asm_instrs_str  = [(0x08048060, "mov eax,0x0", 5)]
        asm_instrs_str += [(0x08048065, "mov ebx,0xa", 5)]
        asm_instrs_str += [(0x0804806a, "add eax,0x1", 3)]
        asm_instrs_str += [(0x0804806d, "sub ebx,0x1", 3)]
        asm_instrs_str += [(0x08048070, "cmp ebx,0x0", 3)]
        asm_instrs_str += [(0x08048073, "jne 0x0804806a", 2)]

        asm_instrs = []

        for addr, asm, size in asm_instrs_str:
            asm_instr = self._asm_parser.parse(asm)
            asm_instr.address = addr
            asm_instr.size = size

            asm_instrs.append(asm_instr)

        reil_instrs = [self._translator.translate(instr)
                        for instr in asm_instrs]

        regs_final, _ = self._emulator.execute(
            reil_instrs,
            0x08048060 << 8,
            context=[]
        )

        self.assertEqual(regs_final["eax"], 0xa)
        self.assertEqual(regs_final["ebx"], 0x0)

    def test_mov(self):
        asm_instrs  = [self._asm_parser.parse("mov eax, 0xdeadbeef")]
        asm_instrs += [self._asm_parser.parse("mov al, 0x12")]
        asm_instrs += [self._asm_parser.parse("mov ah, 0x34")]

        self.__set_address(0xdeadbeef, asm_instrs)

        reil_instrs  = self._translator.translate(asm_instrs[0])
        reil_instrs += self._translator.translate(asm_instrs[1])
        reil_instrs += self._translator.translate(asm_instrs[2])

        regs_initial = {
            "eax" : 0xffffffff,
        }

        regs_final, _ = self._emulator.execute_lite(reil_instrs, context=regs_initial)

        self.assertEqual(regs_final["eax"], 0xdead3412)

    def __set_address(self, address, asm_instrs):
        addr = address

        for asm_instr in asm_instrs:
            asm_instr.address = addr
            addr += 1

class ReilParserTests(unittest.TestCase):

    def setUp(self):
        self._parser = ReilParser()

    def test_add(self):
        instrs  = ["str [eax, EMPTY, t0]"]
        instrs += ["str [ebx, EMPTY, t1]"]
        instrs += ["add [t0, t1, t2]"]
        instrs += ["str [t2, EMPTY, eax]"]

        instrs_parse = self._parser.parse(instrs)

        self.assertEqual(str(instrs_parse[0]), "str   [UNK eax, EMPTY, UNK t0]")
        self.assertEqual(str(instrs_parse[1]), "str   [UNK ebx, EMPTY, UNK t1]")
        self.assertEqual(str(instrs_parse[2]), "add   [UNK t0, UNK t1, UNK t2]")
        self.assertEqual(str(instrs_parse[3]), "str   [UNK t2, EMPTY, UNK eax]")

    def test_parse_operand_size(self):
        instrs  = ["str [DWORD eax, EMPTY, DWORD t0]"]
        instrs += ["str [eax, EMPTY, DWORD t0]"]
        instrs += ["str [eax, EMPTY, t0]"]

        instrs_parse = self._parser.parse(instrs)

        self.assertEqual(instrs_parse[0].operands[0].size, 32)
        self.assertEqual(instrs_parse[0].operands[1].size, 0)
        self.assertEqual(instrs_parse[0].operands[2].size, 32)

        self.assertEqual(instrs_parse[1].operands[0].size, None)
        self.assertEqual(instrs_parse[1].operands[1].size, 0)
        self.assertEqual(instrs_parse[1].operands[2].size, 32)

        self.assertEqual(instrs_parse[2].operands[0].size, None)
        self.assertEqual(instrs_parse[2].operands[1].size, 0)
        self.assertEqual(instrs_parse[2].operands[2].size, None)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
