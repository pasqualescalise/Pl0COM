#!/usr/bin/env python3

"""Using liveness analysis, remove useless instructions; an instruction is
useless if the variable it modifies is not used after it"""

from logger import green


def perform_dead_variable_elimination(bb):
    keep_going = False

    for instruction in bb.instrs:
        live_out_set = instruction.live_out
        kill_set = set(instruction.killed_variables())

        # an instruction is useless if the variable it modifies ("kills")
        # is not used ("live") after it
        if kill_set != set() and kill_set.intersection(live_out_set) == set():
            bb.remove(instruction)
            instruction.parent.remove(instruction)
            print(f"{green('Removed useless instruction')} {instruction}")
            keep_going = True

    return keep_going
