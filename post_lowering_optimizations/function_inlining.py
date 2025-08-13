#!/usr/bin/env python3

"""It's faster to directly execute function code instead of jumping to one:
when possible, directly replace the function call with its code"""

from copy import deepcopy

from ir import BranchStat, StoreStat, SaveSpaceStat, LoadStat, TYPENAMES, EmptyStat, new_temporary
from logger import green, magenta


MAX_INSTRUCTION_TO_INLINE = 16


# Replace all the temporaries in all the instructions with equivalent ones
def replace_temporaries(instructions):
    mapping = {}  # keep track of already remapped temporaries
    for instruction in instructions:
        instruction.replace_temporaries(mapping, create_new=True)

    return instructions


# Remove all the return instructions and if it's needed, add a branch to
# an exit label to simulate a return
def remove_returns(instructions, returns):
    exit_label = TYPENAMES['label']()
    exit_stat = EmptyStat(instructions[0].parent, symtab=instructions[0].symtab)
    exit_stat.set_label(exit_label)
    exit_stat.marked_for_removal = False
    no_exit_label = True  # decides whether or not to put the label at the end

    for i in range(len(instructions)):
        instruction = instructions[i]
        instruction.marked_for_removal = False

        if isinstance(instruction, BranchStat) and instruction.is_return():
            instruction.marked_for_removal = True

            if i < len(instructions) - 1:  # if this isn't the last istruction, add a jump to an exit label
                no_exit_label = False
                instructions[i] = BranchStat(target=exit_label, symtab=instruction.symtab)
                instructions[i].marked_for_removal = False

    if not no_exit_label:
        instructions.append(exit_stat)

    instructions = list(filter(lambda x: not x.marked_for_removal, instructions))
    return instructions


def remove_save_space_statements(instructions, number_of_parameters, number_of_returns):
    if number_of_parameters > 0 and isinstance(instructions[-(number_of_parameters + 1)], SaveSpaceStat):
        instructions = instructions[:-(number_of_parameters + 1)] + instructions[-(number_of_parameters):]
    if number_of_returns > 0 and isinstance(instructions[-1], SaveSpaceStat):
        instructions = instructions[:-1]
    return instructions


# Remove dontcares: note that this breaks RegisterAllocation, since the
# symbol used for the dontcare is never live; but this gets later solved
# using Dead Variable Elimination
def remove_dont_cares(instructions, returns, returns_destinations):
    i = 0
    instrs = instructions[:]
    for ret in returns:
        instruction = instructions[i]
        if isinstance(instruction, SaveSpaceStat) and instruction.space_needed > 0:  # saving space for a return
            instrs.remove(instruction)
            i += 1
        else:
            i += 2  # not a dontcare, skip the assignment
    return instrs


# Change all StoreStat destinations from variables to temporaries, returning
# the mapping of the variables to the temporaries
def change_stores(instructions, variables):
    destinations = {}
    for var in variables:
        destinations[var] = new_temporary(instructions[0].symtab, var.stype)

    for instruction in instructions:
        if isinstance(instruction, StoreStat) and instruction.dest in destinations:
            instruction.dest = destinations[instruction.dest]
            instruction.killhint = instruction.dest

    return instructions, destinations


# Change all LoadStat symbols from variables to temporaries using the provided mapping
def change_loads(instructions, destinations):
    for instruction in instructions:
        if isinstance(instruction, LoadStat) and instruction.symbol in destinations:
            instruction.symbol = destinations[instruction.symbol]

    return instructions


# If this call-BranchStat can be inlined, get all the instructions of the function,
# apply transformations to them (substituting returns with branches to exit, ...),
# get all the instructions before and after the call, apply transformations to them
# (change store of parameters to store in registers, ...), then put everything together
def inline(self):
    if not self.is_call():
        return

    if len(self.target_definition.body.body.children) < MAX_INSTRUCTION_TO_INLINE:
        target_definition_copy = deepcopy(self.target_definition)

        if self.get_function() != 'main':
            target_definition_copy.symbol = self.get_function().symbol
        else:
            target_definition_copy.symbol = "main"  # TODO: check if this creates problems, it shouldn't since target_definition_copy isn't used after this function

        # split the current function in before:body-of-the-function-to-inline:after
        index = self.parent.children.index(self)
        previous_instructions = self.parent.children[:index]
        function_instructions = target_definition_copy.body.body.children
        next_instructions = self.parent.children[index + 1:]

        function_instructions = replace_temporaries(function_instructions)
        function_instructions = remove_returns(function_instructions, target_definition_copy.returns)
        previous_instructions = remove_save_space_statements(previous_instructions, len(target_definition_copy.parameters), len(target_definition_copy.returns))

        # change parameters stores and loads into movs between registers
        previous_instructions, parameters_destinations = change_stores(previous_instructions, target_definition_copy.parameters)
        function_instructions = change_loads(function_instructions, parameters_destinations)

        # change returns stores and loads into movs between registers
        function_instructions, returns_destinations = change_stores(function_instructions, target_definition_copy.returns)
        next_instructions[:len(target_definition_copy.returns) * 2] = change_loads(next_instructions[:len(target_definition_copy.returns) * 2], returns_destinations)  # this only affects the instructions that load the returned variables

        next_instructions = remove_dont_cares(next_instructions, target_definition_copy.returns, returns_destinations)

        # recompact everything
        self.parent.children = previous_instructions + function_instructions + next_instructions

        for local_symbol in self.target_definition.body.local_symtab:
            self.parent.parent.local_symtab.append(local_symbol)

        for child in self.parent.children:
            child.parent = self.parent

        # reference counting: if no one is calling the inlined function, it can be removed
        self.target_definition.called_by_counter -= 1

        if self.get_function() == 'main':
            print(green(f"Inlining function {magenta(f'{self.target.name}')} {green('inside the')} {magenta('main')} {green('function')}\n"))
        else:
            print(green(f"Inlining function {magenta(f'{self.target.name}')} {green('inside function')} {magenta(f'{self.get_function().symbol.name}')}\n"))


BranchStat.inline = inline


def function_inlining(node):
    try:
        node.inline()
    except AttributeError as e:
        if not str(e).endswith("has no attribute 'inline'"):
            raise RuntimeError(f"Raised AttributeError {e}")
