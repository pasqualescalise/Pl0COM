#!/usr/bin/env python3

"""The main function of the compiler, AKA the compiler driver"""

from argparse import ArgumentParser

import lexer
import parser
from support import get_node_list, flattening, lowering
from datalayout import perform_data_layout
from cfg import ControlFlowGraph
from regalloc import LinearScanRegisterAllocator
from codegen import generate_code
from logger import initialize_logger, h1, h2, remove_formatting, green, yellow, cyan, bold, italic, underline
from pre_lowering_optimizations import perform_pre_lowering_optimizations
from post_lowering_optimizations import perform_post_lowering_optimizations
from control_flow_graph_optimizations import perform_control_flow_graph_optimizations
from control_flow_graph_analyses import perform_control_flow_graph_analyses


def compile_program(text, optimization_level):
    print(h1("FRONT-END"))

    print(h2("PARSING"))
    lex = lexer.Lexer(text)
    pars = parser.Parser(lex)
    program = pars.program()
    print(f"\n{green('Parsed program:')}\n{program}")

    print(h2("NODE LIST"))
    node_list = get_node_list(program, quiet=True)
    for node in node_list:
        if node.parent is not None:
            print(f"{yellow(f'{node.type()}, {id(node)}')} is child of {yellow(f'{node.parent.type()}, {id(node.parent)}')}")
        else:
            print(f"{yellow(f'{node.type()}, {id(node)}')} is {bold('root')} node")
    print(f"\nTotal nodes in IR: {cyan(len(node_list))}")

    print(h2("STATEMENT LISTS"))
    for node in node_list:
        try:
            print(f"{bold(node.get_content())}")
        except AttributeError:
            pass  # not a StatList

    ##############################################

    print(h1("MIDDLE-END"))

    # XXX: SOME OPTIMIZATIONS GO HERE
    print(h2("PRE-LOWERING OPTIMIZATIONS"))
    perform_pre_lowering_optimizations(program, optimization_level)

    print(f"\n{green('Optimized program:')}\n{program}")

    print(h2("LOWERING"))
    program.navigate(lowering, quiet=False)

    print(h2("FLATTENING"))
    program.navigate(flattening, quiet=False)

    print(f"\n{green('Lowered and flattened program:')}\n{program}")

    # XXX: OTHER OPTIMIZATIONS GO HERE
    print(h2("POST-LOWERING OPTIMIZATIONS"))
    perform_post_lowering_optimizations(program, optimization_level)

    print(f"\n{green('Optimized program:')}\n{program}")

    ##############################################

    print(h1("CONTROL FLOW GRAPH ANALYSES"))
    cfg = ControlFlowGraph(program)

    perform_control_flow_graph_analyses(cfg)

    # XXX: AND OTHER OPTIMIZATIONS GO HERE
    print(h2("CONTROL FLOW GRAPH OPTIMIZATIONS"))
    cfg = perform_control_flow_graph_optimizations(program, cfg, optimization_level)

    print(f"\n{green('Optimized program:')}\n{program}")

    cfg.print_cfg_to_dot("cfg.dot")
    print(f"\n{underline('A dot file representation of the ControlFlowGraph can be found in the cfg.dot file')}\n")

    ##############################################

    print(h1("BACK-END"))

    print(h2("DATALAYOUT"))
    print(italic("Allocating variables on the stack frame or in the global section\n"))
    perform_data_layout(program)
    print(f"\n{green('Program after datalayout:')}\n{program}")

    print(h2("REGISTER ALLOCATION"))
    register_allocator = LinearScanRegisterAllocator(cfg, 11)
    register_allocation = register_allocator()
    print(register_allocator.get_liveness_intervals())
    print(register_allocation)

    print(h2("CODE GENERATION"))
    code = generate_code(program, register_allocation)
    print(f"\n{green('Final compiled code: ')}\n\n{code}")

    return remove_formatting(code)


def driver_main():
    parser = ArgumentParser(prog="Pl0COM", description="Optimizing compiler for the (modified) PL/0 language", epilog="")

    parser.add_argument('-i', '--input_file', required="True")
    parser.add_argument('-o', '--output_file', default="out.s")
    parser.add_argument('-O', '--optimization_level', default="2", choices=["0", "1", "2"])

    args = parser.parse_args()

    # get a test program from the arguments
    with open(args.input_file, 'r') as inf:
        test_program = inf.read()

    code = compile_program(test_program, int(args.optimization_level))

    # write the code in the file specifed in the arguments
    with open(args.output_file, 'w') as outf:
        outf.write(code)

    print(green(bold(f"\nThe code can be found in the '{args.output_file}' file")))


if __name__ == '__main__':
    initialize_logger()
    driver_main()
