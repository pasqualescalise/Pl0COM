# PLe0COM

Optimizing (toy) compiler for a modified and extended version of the [PL/0 language](https://en.wikipedia.org/wiki/PL/0)

This is a fork of pl0com, a toy compiler for the [Code Optimization and Transformation course held at Politecnico di Milano](https://cto-course-polimi.github.io/)

It features a hand-written recursive-descent parser, an AST and an IR, various optimization stages and a code generation stage which produces (hopefully) valid 32 bit ARMv6 code

I'm using it to experiment and have fun with compiler stuff

## Extended features

+ Functions can accept parameters and can return values; callers can ignore return values
+ Support for ints, shorts, bytes and strings (char arrays)
+ Explicit logging: it's clear what the compiler does and why (with colors!)
+ More ControlFlowGraph analysis
+ Optimizations
	+ Function inlining
	+ Dead code elimination
	+ Memory-to-register promotion
+ Fully working test suite
+ PEP8 compliant (except E501)

## Dependencies

The code generated should work on CPU that supports ARMv6, like any Raspberry PI

### On non-ARM Linux machines

```sh
sudo apt install qemu-user gcc-arm-linux-gnueabi
```

### On ARM Linux machines

```sh
sudo apt install gcc
```

To use the Makefile on ARM, the variables `$(CC)` and `$(RUN_COMMAND)` must be changed

## Compile and run

### Compile

You can run the compiler with

```sh
python3 main.py -i <input_file> [-o <output_file> -O{0,1,2}]
```

to generate an ARMv6 assembly file

To compile to an actual binary, just use

```sh
make compile test=<input_file> [EXECUTABLE=<executable> (default: out)]
```

### Execute

To run the binary on a non-ARM Linux machine, then use

```sh
make execute [EXECUTABLE=<executable> (default: out)]
```

### Compile and Execute

Or just do both with

```sh
make test=<input_file> [EXECUTABLE=<executable> (default: out)]
```

If the input file is present in the `tests` directory, it also checks if its output (in the `tests/expected`) directory is correct

### Debugger

To debug the executable on a non-ARM machine, use

```sh
make test=<input_file> dbg=True [EXECUTABLE=<executable> (default: out)]
```

and in another terminal

```sh
make dbg
```

The debugger can be set in the Makefile or using the variable `$(DEBUGGER)`; I use [pwndbg](https://github.com/pwndbg/pwndbg/), if you want standard gdb on a non-ARM machine use gdb-multiarch

## Testing

```sh
make -s testall
```

compiles and executes all tests, checking if their output is the expected one

To add a new test, put it in the `tests` directory, then add its expected output in the `tests/expected/` directory in a file with the same name as the test and extension ".expected"; you can check if tests file with a specific message by putting that error message in the `.expected` file
