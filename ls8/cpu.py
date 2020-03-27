"""CPU functionality."""

import sys

HLT =  0b00000001
LDI =  0b10000010
PRN =  0b01000111
PUSH = 0b01000101
POP =  0b01000110
CALL = 0b01010000
RET =  0b00010001

JMP =  0b01010100

JEQ =  0b01010101
JNE =  0b01010110


# alu opcodes
alu_codes = {
    0b10100000: 'ADD',
    0b10100010: 'MUL',
    0B10101000: 'AND',
    0B01101001: 'NOT',
    0B10101010: 'OR',
    0B10101011: 'XOR',
    0B10101100: 'SHL',
    0B10101101: 'SHR',
    0b10100111: 'CMP'
}


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        # internal registers
        self.pc = 0
        self.sp = 7
        self.FL = 0b00000000

        #memory
        self.reg = [0] * 8
        self.ram = [0] * 256 

        #setup branchtable
        self.branchtable = {}
        self.branchtable[LDI] = self.handle_LDI
        self.branchtable[PRN] = self.handle_PRN
        self.branchtable[PUSH] = self.handle_PUSH
        self.branchtable[POP] = self.handle_POP
        self.branchtable[CALL] = self.handle_CALL
        self.branchtable[RET] = self.handle_RET
        self.branchtable[JMP] = self.handle_JMP
        self.branchtable[JEQ] = self.handle_JEQ
        self.branchtable[JNE] = self.handle_JNE


    def ram_read(self, address):
        return self.ram[address]

    def ram_write(self, address, value):
        self.ram[address] = value

    def load(self, filename):
        """Load a program into memory."""
        self.ram = [0] * 256
        try:
            with open(filename) as f:
                program = []
                for line in f:
                    # remove comments
                    comment_split = line.split('#')

                    machine_code = comment_split[0].strip()

                    #remove spaces
                    if machine_code == '':
                        continue
                    num = int(machine_code,2)
                    program.append(num)

        except FileNotFoundError:
            print('file not found')
            sys.exit(2)
        address = 0
        for instruction in program:
            self.ram_write(address,instruction)
            address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        value_a = self.reg[reg_a]
        value_b = self.reg[reg_b]
        
        if op == "ADD":
            self.reg[reg_a] = (value_a + value_b)

        elif op == "MUL":
            self.reg[reg_a] = (value_a * value_b)

        elif op == 'AND':
            self.reg[reg_a] = (value_a & value_b)

        elif op == 'OR':
            self.reg[reg_a] = (value_a | value_b)

        elif op == 'XOR':
            self.reg[reg_a] = (value_a ^ value_b)

        elif op == 'NOT':
            self.reg[reg_a] = ~value_a

        elif op == 'SHL':
            self.reg[reg_a] = (value_a << value_b)

        elif op == 'SHR':
            self.reg[reg_a] = (value_a >> value_b)
            
        elif op == 'MOD':
            self.reg[reg_a] = (value_a % value_b)
        
        elif op == "CMP":

            if value_a < value_b:
                self.FL = 0b00000100

            elif value_a > value_b:
                self.FL = 0b00000010

            elif value_a == value_b:
                self.FL = 0b00000001

        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()


    def handle_LDI(self, a=None, b=None):
        self.reg[a] = b
        self.pc += 3

    def handle_PRN(self, a=None, b=None):
        print(self.reg[a])
        self.pc += 2

    def handle_PUSH(self, a=None, b=None):
        self.reg[self.sp] -= 1
        self.ram[self.reg[self.sp]] = self.reg[a]
        self.pc += 2

    def handle_POP(self, a=None, b=None):
        memory = self.ram[self.reg[self.sp]]
        self.reg[a] = memory
        self.reg[self.sp] += 1
        self.pc += 2

    def handle_CALL(self, a=None, b=None):
        # The address of the ***instruction*** _directly after_ `CALL` is
        # pushed onto the stack.
        self.reg[self.sp] -= 1
        self.ram[self.reg[self.sp]] = self.pc + 2
        # The PC is set to the address stored in the given register.
        self.pc = self.reg[a]

    def handle_RET(self, a=None, b=None):
        self.pc = self.ram[self.reg[self.sp]]
        self.reg[self.sp] += 1

    def handle_JMP(self, a=None, b=None):
        self.pc = self.reg[a]

    def handle_JNE(self, a=None, b=None):
        # If `E` flag is clear (false, 0), 
        # jump to the address stored in the given register.

        if self.FL & 0b00000001 == 0:
            self.pc = self.reg[a]
        else: 
            self.pc += 2

    def handle_JEQ(self, a=None, b=None):
        # If `equal` flag is set (true), 
        # jump to the address stored in the given register.
        if self.FL & 0b00000001 == 1:
            self.pc = self.reg[a]
        else: 
            self.pc += 2

    def run(self):
        """Run the CPU."""
        self.reg = [0] * 8
        self.reg[self.sp] = 0xf3


        while True:
            IR = self.ram[self.pc]

            operand_a = self.ram_read(self.pc + 1)
            operand_b = self.ram_read(self.pc + 2)

            if IR == HLT:
                sys.exit()
                break
            elif IR in alu_codes:
                self.alu(alu_codes[IR], operand_a, operand_b)
                self.pc += 3

            elif IR in self.branchtable:
                self.branchtable[IR](operand_a, operand_b)

            else:
                print(f'Unknown instruction: {IR}')
                sys.exit(1)
