#!/usr/bin/env python3

"""Sometimes because of other optimizations load-store chains are created,
where symbols are copied one into the other for no apparent reason. This
optimization eliminates these useless instruction, substituting the correct
symbols in all the subsequent instructions

For example:
    t2 <- t1
    t3 <- t2
    t4 <- t3
    t5 <- t4

Becomes:
    t5 <- t1
"""

from ir import StoreStat, LoadStat, PointerType
from logger import green


def perform_chain_load_store_elimination(bb):
    keep_going = False
    mapping = {}

    for instruction in bb.instrs:
        if not isinstance(instruction, (StoreStat, LoadStat)):
            continue

        # do not delete chains involving pointers
        if not (instruction.dest.alloct == 'reg' and instruction.symbol.alloct == 'reg' and not isinstance(instruction.dest.stype, PointerType) and not isinstance(instruction.symbol.stype, PointerType)):
            continue

        # XXX: can we do this also for non temporaries?
        if isinstance(instruction, StoreStat):
            if not instruction.dest.is_temporary:
                continue

        if isinstance(instruction, LoadStat):
            if not instruction.symbol.is_temporary:
                continue

        if instruction.dest in bb.live_out:  # do not overwrite symbols used in next BasicBlocks
            continue

        mapping[instruction.dest] = instruction.symbol

        index = bb.instrs.index(instruction)

        for instr in bb.instrs[index + 1:]:
            instr.replace_temporaries(mapping, create_new=False)

        bb.remove(instruction)
        instruction.parent.remove(instruction)
        print(f"{green('Removed chained instruction')} {instruction}")
        keep_going = True

    return keep_going
