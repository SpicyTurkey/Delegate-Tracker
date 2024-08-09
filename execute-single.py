from manticore.ethereum import ManticoreEVM, ABI
from manticore.core.plugin import Plugin
import json
import sys
from colorama import Fore, Back, Style, init


source_code = """
pragma solidity ^0.4.18;


contract Conductor
{
    address public Owner = msg.sender;
    address public DataBase;
    uint256 public Limit;
    
    
    function Set(address dataBase, uint256 limit)
    {
        require(msg.sender == Owner);
        Limit = limit;
        DataBase = dataBase;
    }
    
    function()payable{}
    
    function transfer(address adr)
    payable
    {
        if(msg.value>Limit)
        {        
            DataBase.delegatecall(bytes4(sha3("AddToDB(address)")),msg.sender);
            adr.transfer(this.balance);
        }
    }
    
}
"""

call_fun2 = 'Set'
call_fun = 'transfer'

init(autoreset=True)
class StorageAccessDetector(Plugin):
    allw = 0
    allr = 0
    tx_counter_r = 0
    tx_counter_w = 0
    def __init__(self):
        super().__init__()
        self.reads = {}
        self.writes = {}
        self.selfdestruct_triggered = False

    def will_open_transaction_callback(self, state, transaction):
        # print("clear")
        self.reads.clear()
        self.writes.clear()

    def did_evm_read_storage_callback(self, state, address, offset, value):#读取回调函数中正常情况不会修改value，可以不使用，但是参数必须存在
        print("    读 slot: ",Fore.GREEN + f"{offset}   ",Fore.YELLOW + f"值: {value}")
        if address not in self.reads:
            self.reads[address] = set()
        self.reads[address].add((offset, value))

    def did_evm_write_storage_callback(self, state, address, offset, value):
        print(f"写     slot: ",Fore.GREEN + f"{offset}   ",Fore.YELLOW + f"值: {value}")
        if address not in self.writes:
            self.writes[address] = set()
        self.writes[address].add((offset, value))

    def will_evm_execute_instruction_callback(self, state, instruction, arguments):
        pc = instruction.pc
        mnemonic = instruction.mnemonic
        semantics = instruction.semantics
        # print(f"pc = {pc}, mnemonic = {mnemonic}, semantics = {semantics}")

        if instruction.semantics == 'SELFDESTRUCT':
            print(f"Detected SELFDESTRUCT at PC: {instruction.pc}")
        if mnemonic == 'CALL':
            data = state.platform.current_transaction.data
            print(f"CALL Instruction triggered, and data :{data}")
            if len(arguments)>2:
                call_value = arguments[2]
                # print(f"arguments0 = {arguments[0]}",f", arguments0 = {arguments[1]}",f", arguments0 = {arguments[2]}")
                
                if call_value != 0:
                    print(f"Detected sending Ether at PC: {pc}, Value: {call_value}")

m = ManticoreEVM()
p = StorageAccessDetector()
m.register_plugin(p)

user_account = m.create_account(balance=1000000000000000000)
# contract_account = m.solidity_create_contract(source_code, owner=user_account,contract_name = "WalletLibrary")
contract_account = m.solidity_create_contract(source_code, owner=user_account, contract_name="Conductor")
# print("contract_account",contract_account)
md = m.get_metadata(contract_account)
arg_type_by_name = {}
sig_by_name = {}
selector = md.function_selectors

for se in selector:
    func_name = md.get_func_name(se)
    # print(func_name)
    arg_type_by_name[func_name] = md.get_func_argument_types(se)
    # print(arg_type_by_name[func_name])
    sig_by_name[func_name] = md.get_func_signature(se)
    # print(sig_by_name[func_name])
    # print('')

if md is None:
    print(f"Metadata not found in address {contract_account}.")
else:
    selector = md.function_selectors

#可以反过来试一下


arg_type = arg_type_by_name[call_fun]
arg_type2 = arg_type_by_name[call_fun2]

bool_arg = False
boo2 = boo = False
if('address[]' in arg_type2):
    boo2 = True
    bool_arg = True
    print("address[]存在于",call_fun2,"，将尝试限制符号化大小。")
if('address[]' in arg_type):
    boo = True
    bool_arg = True
    print("address[]存在于",call_fun,"，将尝试限制符号化大小。")

if boo2:
    symbolic_length = 2
    symbolic_bytes2 = m.make_symbolic_buffer(4)
    symbolic_value2 = m.make_symbolic_value()
    tx_data2 = ABI.function_call(str(sig_by_name[call_fun2]), symbolic_bytes2, symbolic_value2)
    print(str(sig_by_name[call_fun2]))


    pass
else:
    args2 = m.make_symbolic_arguments(arg_type2)
    # print("-->符号化数据arg_data2  = ",args2)
    tx_data2 = ABI.function_call(str(sig_by_name[call_fun2]), *args2)
    symbolic_value2 = m.make_symbolic_value()

    pass

if boo:
    args = m.make_symbolic_arguments(arg_type)
    symbolic_length1 = 3           
    symbolic_bytes1 = m.make_symbolic_buffer(symbolic_length1)
    # print("-->符号化数据symbolic_bytes  = ",symbolic_bytes1," .type:", type(symbolic_bytes1))

    symbolic_value1 = m.make_symbolic_value()

    tx_data = ABI.function_call(str(sig_by_name[call_fun]), symbolic_bytes1, symbolic_value1)
    print(str(sig_by_name[call_fun]))

    #测试用
    # m.transaction(caller=user_account, address=contract_account, value=symbolic_value4, data=tx_data)
    pass
else:
    args = m.make_symbolic_arguments(arg_type)
    # print("-->符号化数据arg_data  = ",args)
    tx_data = ABI.function_call(str(sig_by_name[call_fun]), *args)
    symbolic_value1= m.make_symbolic_value()

    pass
print("---tx2开始")
m.transaction(caller=user_account, address=contract_account, value=symbolic_value2, data=tx_data2)
print("---tx2结束")
print("---tx1开始")
m.transaction(caller=user_account, address=contract_account, value=symbolic_value1, data=tx_data)
print("---tx1结束")

m.finalize()
