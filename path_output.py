
import json
import sys
from slither.slither import Slither
from colorama import Fore, Back, Style, init

if len(sys.argv) != 2:
    print("python variable_in_condition.py variable_in_condition.sol")
    sys.exit(-1)

slither = Slither(sys.argv[1])
contracts = slither.contracts
sol_path = {}

for contract in contracts:
    contract_path = {}
    if_assert_path = {}
    send_path = {}
    suicide_path = {}

    read_vars_func = {}
    write_vars_func = {}
    func_by_modifier = {}
    function_call = {}
    function_all_call = {}
    
    var_in_con = {}

    variables = contract.state_variables
    functions = contract.functions

    for f in functions:
        func_by_modifier[f.name] = f.modifiers
        if f.internal_calls:
            function_call[f.name] = f.internal_calls
        if f.all_internal_calls():
            function_all_call[f.name] = f.all_internal_calls()

    for v in variables:
        var_a = contract.get_state_variable_from_name(v.name)
        var_in_con[v.name] = [f for f in functions if f.is_reading_in_conditional_node(var_a) or f.is_reading_in_require_or_assert(var_a)]
        write_vars_func[v.name] = [f for f in contract.get_functions_writing_to_variable(var_a)]
        read_vars_func[v.name] = [f for f in contract.get_functions_reading_from_variable(var_a)]

    funcs_call_suicide = []
    for f in functions:
        if f.name in function_call:
            if "suicide(address)" in [c.name for c in function_call[f.name]] or "selfdestruct(address)" in [c.name for c in function_call[f.name]]:
                funcs_call_suicide.append(f)

    funcs_send_eth = [f for f in functions if f.can_send_eth()]

    for f in funcs_send_eth:
        in_value = [v for v in read_vars_func if f in read_vars_func[v]]
        modifier_var = []
        if (f.name in func_by_modifier) and len(func_by_modifier[f.name])!=0:
            modifiers = func_by_modifier[f.name]
            modifier = modifiers[0]
            modifier_call = modifier.all_internal_calls()
            if modifier_call:
                for call in modifier_call:
                    pass
        for state_value in in_value:
            if write_vars_func[state_value]:    
                for fw in write_vars_func[state_value]:
                    if fw == f or func_by_modifier.get(fw.name):
                        continue
                    path =  f"writing:{fw.name},reading:{f.name}"
                    if path not in send_path:
                        send_path[path] = []
                    if state_value not in send_path[path]:
                        send_path[path].append(state_value)

        for state_value in modifier_var:
            if write_vars_func[state_value]:
                for fw in write_vars_func[state_value]:
                    if fw == f or func_by_modifier.get(fw.name):
                        continue
                    path =  f"writing:{fw.name},reading in modifier {modifier.name} of {f.name}"
                    if path not in send_path:
                        send_path[path] = []
                    if state_value not in send_path[path]:
                        send_path[path].append(state_value)
    for f in funcs_call_suicide:
        in_value = [v for v in read_vars_func if f in read_vars_func[v]]
        modifier_var = []
        if f.name in func_by_modifier:
            modifiers = func_by_modifier[f.name]
            modifier = modifiers[0]
            modifier_call = modifier.all_internal_calls()
            if modifier_call:
                for call in modifier_call:
                    pass
        for state_value in in_value:
            if write_vars_func[state_value]:    
                for fw in write_vars_func[state_value]:
                    if fw == f or func_by_modifier.get(fw.name):
                        continue
                    path =  f"writing:{fw.name},reading:{f.name}"
                    if path not in suicide_path:
                        suicide_path[path] = []
                    if state_value not in suicide_path[path]:
                        suicide_path[path].append(state_value)

        for state_value in modifier_var:
            if write_vars_func[state_value]:
                for fw in write_vars_func[state_value]:
                    if fw == f or func_by_modifier.get(fw.name):
                        continue
                    path =  f"writing:{fw.name},reading in modifier {modifier.name} of {f.name}"
                    if path not in suicide_path:
                        suicide_path[path] = []
                    if state_value not in suicide_path[path]:
                        suicide_path[path].append(state_value)

    for v in var_in_con:
        funcs_con = var_in_con[v]
        funcs_w = write_vars_func[v]
        for f_con in funcs_con:
            if f_con in funcs_call_suicide or f_con in funcs_send_eth:
                continue
            for f_w in funcs_w:
                if f_w.visibility not in ["public","external"] or f_w == f_con or func_by_modifier.get(f_w.name):
                    continue
                path =  f"writing:{f_w.name},reading:{f_con.name}"
                if path not in if_assert_path:
                    if_assert_path[path] = []
                if v not in if_assert_path[path]:
                    if_assert_path[path].append(v)

    contract_path["if_assert_path"] = if_assert_path
    contract_path["send_path"] = send_path
    contract_path["suicide_path"] = suicide_path
    sol_path[contract.name] = contract_path

file_name = sys.argv[1] + ".json"
with open(file_name,"w") as fw:
    json.dump(sol_path, fw, indent=4, ensure_ascii=False)
