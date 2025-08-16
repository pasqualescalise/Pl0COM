#!/usr/bin/env python3

"""Replicate the body of the loop a LOOP_UNROLLING_FACTOR number of times,
reducing loop overhead (checking the loop condition less times)

For example, if the LOOP_UNROLLING_FACTOR is 2

for i := 0; i < 11; i := i + 1 do begin
    print i
end.

becomes

for i := 0; i < 11 - 1; i := i + 1 do begin
    print i;
    i := i + 1;
    print i
end;

if odd 11 then begin {True}
    print i
end.

while if LOOP_UNROLLING_FACTOR is 4 it becomes

for i := 0; i < 11 - 3; i := i + 1 do begin
    print i;
    i := i + 1;
    print i
    i := i + 1;
    print i
    i := i + 1;
    print i
end;

if 11 % 4 != 0 then begin {True}
    for i := i; i < 11; i := i + 1 do begin
        print i
    end
end.

For now, the LOOP_UNROLLING_FACTOR can only be a power of 2
"""

from copy import deepcopy
from math import log

from ir import ForStat, Const, BinExpr, UnExpr, IfStat, StatList, AssignStat, Var
from logger import red, green, magenta, cyan


LOOP_UNROLLING_FACTOR = 2


def unroll(self):
    # TODO: check if the loop is "normal" -> if (i = 0; i < x; i++)
    original_cond_copy = deepcopy(self.cond)
    original_body_copy = deepcopy(self.body)

    # subtract one to the actual loop condition
    loop_end = self.cond.children[-1]
    loop_unrolling_factor_minus_one = Const(value=LOOP_UNROLLING_FACTOR - 1, symtab=self.symtab)
    sub = BinExpr(parent=self.cond, children=['minus', loop_end, loop_unrolling_factor_minus_one], symtab=self.symtab)

    loop_unrolling_factor_minus_one.parent = sub
    loop_end.parent = sub
    self.cond.children[-1] = sub

    # append all the variable updates and bodies to the body of the loop
    for i in range(LOOP_UNROLLING_FACTOR - 1):
        step_copy = deepcopy(self.step)
        body_copy = deepcopy(original_body_copy)

        self.body.append(step_copy)
        self.body.append(body_copy)

    # epilogue
    if LOOP_UNROLLING_FACTOR == 2:
        # just check if the loop condition is odd or not; if it is, execute the remaining loop body
        loop_end_copy = deepcopy(loop_end)
        odd_cond = UnExpr(children=['odd', loop_end_copy], symtab=self.symtab)
        then = deepcopy(original_body_copy)
        check = IfStat(cond=odd_cond, thenpart=then, elifspart=StatList(), elsepart=None, symtab=self.symtab)
        check.parent = self
        self.epilogue = check
    else:
        # check if the loop condition is a multiple of the LOOP_UNROLLING_FACTOR; if not, execute the remaining loop bodies
        loop_end_copy = deepcopy(loop_end)

        init = AssignStat(target=self.init.symbol, expr=Var(var=self.init.symbol), symtab=self.symtab)
        loop_cond = original_cond_copy
        step = deepcopy(self.step)
        loop_body = deepcopy(body_copy)

        loop = ForStat(parent=None, init=init, cond=loop_cond, step=step, body=loop_body, symtab=self.symtab)

        loop_unrolling_factor = Const(value=LOOP_UNROLLING_FACTOR, symtab=self.symtab)
        modulus = BinExpr(children=['mod', loop_end_copy, loop_unrolling_factor], symtab=self.symtab)
        zero = Const(value=0, symtab=self.symtab)
        if_cond = BinExpr(children=['neq', modulus, zero], symtab=self.symtab)
        check = IfStat(cond=if_cond, thenpart=loop, elifspart=StatList(), elsepart=None, symtab=self.symtab)

        loop.parent = check
        check.parent = self
        self.epilogue = check

    print(green(f"Unrolling loop {magenta(f'{id(self)}')} {green('with an unrolling factor of')} {cyan(f'{LOOP_UNROLLING_FACTOR}')}\n"))


ForStat.unroll = unroll


def loop_unrolling(node):
    try:
        node.unroll()
    except AttributeError as e:
        if not str(e).endswith("has no attribute 'unroll'"):
            raise RuntimeError(f"Raised AttributeError {e}")


def perform_loop_unrolling(program):
    if not log(LOOP_UNROLLING_FACTOR, 2).is_integer():
        raise RuntimeError("Loop Unrolling factor must be a power of 2")

    if LOOP_UNROLLING_FACTOR < 2:
        print(red(f"Skipping Loop Unrolling because the LOOP_UNROLLING_FACTOR is {LOOP_UNROLLING_FACTOR}"))
        return

    program.navigate(loop_unrolling, quiet=True)
