"""
   ___                          ____    __
  / _ \_______ ____ ____  ___  / __/___/ /  ___ __ _  ___
 / // / __/ _ `/ _ `/ _ \/ _ \_\ \/ __/ _ \/ -_)  ' \/ -_)
/____/_/  \_,_/\_, /\___/_//_/___/\__/_//_/\__/_/_/_/\__/
              /___/

version 0.2.3
a scheme interpreter, written by ori yonay

TODO:
    - add 'let' feature

"""

import copy # for deep copying of lists

# for user-defined symbols
SYMBOLS = {'newline' : '\n'}
GLOBALS = {'NUM_TEMPS' : 0} # global back-end variables
BOOLS = {False : '#f', True: '#t'} # global TRUE and FALSE
SPECIAL_WORDS = ['define', 'if', 'or', 'and', 'lambda']
# a list for in-built functions (used in map() and filter() to verify function)
# (in a separate list to avoid letting user overload these)
INBUILTFUNCTIONS = ['+', '-', '*', '/', '%', 'modulus', '=', 'eq?',
                    '!=', 'neq?', '>', 'greater?', '<', 'smaller?',
                    '>=', 'geq?', '<=', 'leq?', 'list', 'car', 'cdr',
                    'cadr', 'caddr', 'cadddr', 'caddddr', 'reverse',
                    'append', 'cons', 'length', 'at', 'even?', 'odd?',
                    'positive?', 'list?', 'display', 'map', 'filter',
                    'del', 'read', 'read-line'
]

# Error: a class for returning error messages
class Error:
    def __init__(self, message):
        self.message = message

    def __str__(self): # overload print() function
        return self.message

# Functions: a class with IN-BUILT FUNCTIONS
class Functions:
    def f_add(args):
        result = 0
        for a in args:
            # add the symbolic value (or literal value) of each:
            if a in SYMBOLS:
                result += Utils.attempt_float(SYMBOLS[a])
            else: result += Utils.attempt_float(a)
        # convert result to integer if it's an integer:
        if result.is_integer():
            return Utils.attempt_int(result)
        #otherwise, return the result as a float:
        return result

    def f_subtract(args):
        result = Utils.attempt_float(SYMBOLS[args[0]]) if args[0] in SYMBOLS else float(args[0])

        for a in args[1:]:
            if a in SYMBOLS:
                result -= Utils.attempt_float(SYMBOLS[a])
            else: result -= Utils.attempt_float(a)
        # convert result to integer if it's an integer:
        if result.is_integer():
            return Utils.attempt_int(result)
        #otherwise, return the result as a float:
        return result

    def f_multiply(args):
        result = Utils.attempt_float(SYMBOLS[args[0]]) if args[0] in SYMBOLS else float(args[0])
        for a in args[1:]:
            if a in SYMBOLS:
                result *= Utils.attempt_float(SYMBOLS[a])
            else: result *= Utils.attempt_float(a)

        # convert result to integer if it's an integer:
        if result.is_integer():
            return Utils.attempt_int(result)
        #otherwise, return the result as a float:
        return result

    def f_divide(args):
        result = Utils.attempt_float(SYMBOLS[args[0]]) if args[0] in SYMBOLS else Utils.attempt_float(args[0])
        for a in args[1:]:
            if a in SYMBOLS:
                result /= Utils.attempt_float(SYMBOLS[a])
            else: result /= Utils.attempt_float(a)

        # convert result to integer if it's an integer:
        if result.is_integer():
            return Utils.attempt_int(result)
        #otherwise, return the result as a float:
        return result

    def f_modulus(args):
        result = Utils.attempt_float(SYMBOLS[args[0]]) if args[0] in SYMBOLS else Utils.attempt_float(args[0])
        for a in args[1:]:
            if a in SYMBOLS:
                result %= Utils.attempt_float(SYMBOLS[a])
            else: result %= Utils.attempt_float(a)

        # convert result to integer if it's an integer:
        if result.is_integer():
            return Utils.attempt_int(result)
        #otherwise, return the result as a float:
        return result

    def f_equal(x):
        for i in range(len(x) - 1):
            if x[i] != x[i+1]: return BOOLS[False]
        return BOOLS[True]

    def f_notequal(x):
        return BOOLS[True] if (Functions.f_equal(x) == BOOLS[False]) else BOOLS[False]

    def f_greater(args):
        args = Functions.replaceWithSymbolValues(args)
        for i in range(len(args) - 1):
            try:
                if Utils.attempt_float(args[i]) <= Utils.attempt_float(args[i+1]):
                    return BOOLS[False]
            except:
                return Error('(>) error: invalid symbol.')
        return BOOLS[True]

    def f_smaller(args):
        args = Functions.replaceWithSymbolValues(args)
        for i in range(len(args) - 1):
            try:
                if Utils.attempt_float(args[i]) >= Utils.attempt_float(args[i+1]):
                    return BOOLS[False]
            except:
                return Error('(<) error: invalid symbol.')
        return BOOLS[True]

    def f_greater_or_equal(args):
        args = Functions.replaceWithSymbolValues(args)
        for i in range(len(args) - 1):
            try:
                if Utils.attempt_float(args[i]) < Utils.attempt_float(args[i+1]):
                    return BOOLS[False]
            except:
                return Error('(>=) error: invalid symbol.')
        return BOOLS[True]

    def f_smaller_or_equal(args):
        args = Functions.replaceWithSymbolValues(args)
        for i in range(len(args) - 1):
            try:
                if Utils.attempt_float(args[i]) > Utils.attempt_float(args[i+1]):
                    return BOOLS[False]
            except:
                return Error('(<=) error: invalid symbol.')
        return BOOLS[True]

    def f_define(args):
        # split args into 2 arguments:
        if args.startswith('('):
            # then this is a function definition:
            Functions.f_definefunction(args)
            return
        else:
            args = args.split(' ', 1)

        if args[1].startswith('('):
            # then we have to evaluate args[1]:
            args[1] = evaluate(args[1])

        # in the case of a list or a copy (define a b):
        if args[1] in SYMBOLS:
            SYMBOLS[args[0]] = SYMBOLS[args[1]]
        # otherwise, treat the definition normally:
        else: SYMBOLS[args[0]] = args[1]

    def f_definefunction(args):
        # defines a function.
        # first, split function declaration from definition:
        # (so '(square x) (* x x)' becomes 'square x' and '(* x x)')
        args = args.split(') ', 1)
        declaration = args[0][1:]
        definition = args[1]

        # split function declaration by space:
        declaration = declaration.split()

        # create a new Function object for this function:
        SYMBOLS[declaration[0]] = Function(declaration[1:], definition)

    def handle_if(cmd):
        # tokenize command:
        cmd = Utils.tokenize(cmd)

        # make sure we only have 2 or 3 args:
        if len(cmd) < 2:
            return Error('If-statement error: not enough arguments! (%s provided.)' %len(cmd))
        if len(cmd) > 3:
            return Error('If-statement error: too many arguments! (%s provided).' %len(cmd))

        if evaluate(cmd[0]) == BOOLS[True]: # if the statement is true
            return evaluate(cmd[1])
        elif len(cmd) == 3: # if an 'else' statement was provided
            return evaluate(cmd[2])

    def handle_or(cmd):
        tokens = Utils.tokenize(cmd)
        # if any tokens evaluate to true, then OR is true:
        for token in tokens:
            if evaluate(token) == BOOLS[True]:
                return BOOLS[True]
        # if none of the tokens evaluated to true, then it's false:
        return BOOLS[False]

    def handle_and(cmd):
        tokens = Utils.tokenize(cmd)
        # if any tokens evaluate to false, then AND is false:
        for token in tokens:
            if evaluate(token) == BOOLS[False]:
                return BOOLS[False]
        # if none of the tokens were false, then it's true:
        return BOOLS[True]

    def handle_lambda(expr):
        # all we're doing is defining a temporary function that'll be garbage-collected
        # after its execution:
        Functions.f_define('(<TEMP_' + str(GLOBALS['NUM_TEMPS']) + '> ' + expr[1:])
        GLOBALS['NUM_TEMPS'] += 1
        return '<TEMP_' + str(GLOBALS['NUM_TEMPS']-1) + '>' # -1 since we just incremented it

    def make_list(elements):
        # replace any symbols (including <TEMP_X>):
        for i in range(len(elements)):
            # if this element is in the symbol table (so can't be a list):
            if not isinstance(elements[i], list) and elements[i] in SYMBOLS:
                elements[i] = SYMBOLS[elements[i]]
        # store list temporarily in symbols as <TEMP_X>:
        listname = '<TEMP_' + str(GLOBALS['NUM_TEMPS']) + '>'
        SYMBOLS[listname] = elements
        GLOBALS['NUM_TEMPS'] += 1
        return listname

    def f_car(arg):
        # make sure exactly one argument was given:
        if len(arg) != 1:
            return Error('(car) error: expected 1 argument, %s provided.' % len(arg))
        if arg[0] not in SYMBOLS:
            return Error('(car) error: symbol %s not found.' % arg[0])

        return SYMBOLS[arg[0]][0]

    def f_cdr(arg):
        # make sure exactly one argument was given:
        if len(arg) != 1:
            return Error('(cdr) error: expected 1 argument, %s provided.' % len(arg))
        # make sure argument exists in symbols:
        if arg[0] not in SYMBOLS:
            return Error('(cdr) error: symbol %s not found.' % arg[0])
        if len(SYMBOLS[arg[0]]) == 0: # we can't cdr an empty list:
            return Error('(cdr) error: list provided is empty.')
        return Functions.make_list(SYMBOLS[arg[0]][1:])

    def f_cadr(arg): # useless since we have 'at' function, but still here
        if arg[0] not in SYMBOLS:
            return Error('(cadr) error: symbol %s not found.' % arg[0])
        try:
            return SYMBOLS[arg[0]][1]
        except:
            return Error('(cadr) error: index out of bounds')

    def f_caddr(arg): # useless since we have 'at' function, but still here
        if arg[0] not in SYMBOLS:
            return Error('(caddr) error: symbol %s not found.' % arg[0])
        try:
            return SYMBOLS[arg[0]][2]
        except:
            return Error('(caddr) error: index out of bounds')

    def f_cadddr(arg): # useless since we have 'at' function, but still here
        if arg[0] not in SYMBOLS:
            return Error('(cadddr) error: symbol %s not found.' % arg[0])
        try:
            return SYMBOLS[arg[0]][3]
        except:
            return Error('(cadddr) error: index out of bounds')

    def f_caddddr(arg): # useless since we have 'at' function, but still here
        if arg[0] not in SYMBOLS:
            return Error('(caddddr) error: symbol %s not found.' % arg[0])
        try:
            return SYMBOLS[arg[0]][4]
        except:
            return Error('(caddddr) error: index out of bounds')

    def f_reverse(arg):
        # make sure exactly one argument was given:
        if len(arg) != 1:
            return Error('(reverse) error: expected 1 argument, %s provided.' % len(arg))

        # make sure arg is in symbol table:
        if arg[0] not in SYMBOLS:
            return Error('(reverse) error: symbol %s not found.' % arg[0])

        if len(SYMBOLS[arg[0]]) == 0: # we can't reverse an empty list:
            return Functions.make_list([])

        # return the reversed list:
        return Functions.make_list(SYMBOLS[arg[0]][::-1])

    def f_append(args):
        print(args)
        newlist = []
        for arg in args:
            newlist.extend(SYMBOLS[arg] if arg in SYMBOLS else arg)
        return Functions.make_list(newlist)

    def f_cons(args):
        newlist = []
        for arg in args:
            newlist.append(SYMBOLS[arg] if arg in SYMBOLS else arg)
        return Functions.make_list(newlist)

    def f_length(arg):
        # make sure exactly one argument was given:
        if len(arg) != 1:
            return Error('(length) error: expected 1 argument, %s provided.' % len(arg))
        if arg[0] not in SYMBOLS:
            return Error('(length) error: symbol %s not found.' % arg[0])

        return len(SYMBOLS[arg[0]])

    def f_at(args):
        # make sure arg[0] in symbol table:
        if args[0] not in SYMBOLS:
            return Error('(at) error: symbol %s not found.' % args[0])

        # if 2 arguments provided:
        if len(args) == 2:
            try:
                return SYMBOLS[args[0]][Utils.attempt_int(args[1])]
            except:
                return Error('(at) error: index out of bounds or invalid: %s' % args[1])

        indices = []
        for idx in args[1:]:
            try:
                indices.append(SYMBOLS[args[0]][Utils.attempt_int(idx)])
            except:
                return Error('(at) error: index out of bounds or invalid: %s' % idx)

        return Functions.make_list(indices)

    def printlist(mylist):
        # if the list is empty:
        if len(mylist) == 0:
            print('()', end='')
            return

        # otherwise:
        print('(', end='')
        for i in range(len(mylist)-1):
            if isinstance(mylist[i], list):
                Functions.printlist(mylist[i])
                print(', ', end='')
            else: print(mylist[i], end=', ')
        if isinstance(mylist[-1], list):
            Functions.printlist(mylist[-1])
        else: print(mylist[-1], end='')
        print(')', end='')

    def iseven(x):
        x = Functions.replaceWithSymbolValues(x)
        if isinstance(x, list):
            for i in x:
                temp = Functions.iseven(i)
                if temp == BOOLS[False]: return BOOLS[False]
                elif temp == None: return None
            return BOOLS[True]
        else:
            x = Utils.attempt_float(x)
            if x == None: return None
            return BOOLS[(x % 2 == 0)]

    def isodd(x):
        x = Functions.replaceWithSymbolValues(x)
        if isinstance(x, list):
            for i in x:
                temp = Functions.isodd(i)
                if temp == BOOLS[False]: return BOOLS[False]
                elif temp == None: return None
            return BOOLS[True]
        else:
            x = Utils.attempt_float(x)
            if x == None: return None
            return BOOLS[(x % 2 != 0)]

    def ispositive(x):
        x = Functions.replaceWithSymbolValues(x)
        if isinstance(x, list):
            for i in x:
                temp = Functions.ispositive(i)
                if temp != BOOLS[True]:
                    return temp
            return BOOLS[True]
        else:
            x = Utils.attempt_float(x)
            if x == None: return None
            return BOOLS[(x > 0)]

    def islist(arg):
        # make sure exactly one argument was given:
        if len(arg) != 1:
            return Error('(list?) error: expected 1 argument, %s provided.' % len(arg))

        if arg[0] in SYMBOLS:
            return BOOLS[isinstance(SYMBOLS[arg[0]], list)]

        # if the argument is not in our symbol table currently, it can't be a list:
        return BOOLS[False]

    def display(args):
        args = Functions.replaceWithSymbolValues(args)
        for i in args:
            if isinstance(i, list):
                Functions.printlist(i)
                print()
            else:
                print(i)

    def replaceWithSymbolValues(x):
        if isinstance(x, list):
            for i in range(len(x)):
                if isinstance(x[i], list):
                    x[i] = Functions.replaceWithSymbolValues(x[i])
                elif x[i] in SYMBOLS:
                    x[i] = SYMBOLS[x[i]]
            return x
        else:
            if x in SYMBOLS:
                return SYMBOLS[x]
        return x

    def printsymbols():
        Functions.printlist(list(SYMBOLS.keys()))
        print()

    def map(args):
        # args[0] is the function name that we're applying on args[1].
        # make sure exactly 2 arguments were provided:
        if len(args) != 2:
            return Error('(map) error: expected 2 arguments, got %s.' % len(args))

        # make sure first argument is actually a function:
        if (args[0] in SYMBOLS and not isinstance(SYMBOLS[args[0]], Function)) and args[0] not in INBUILTFUNCTIONS:
            return Error('(map) error: symbol %s is not a function.' % args[0])

        # make sure second argument (list) is actually a list and is in our symbol table:
        if args[1] not in SYMBOLS:
            return Error('(map) error: symbol %s not found.' % args[1])
        if not isinstance(SYMBOLS[args[1]], list):
            return Error('(map) error: symbol %s is not a list.' % args[1])

        # make a copy of the list:
        elements_copy = copy.deepcopy(SYMBOLS[args[1]])

        # apply the function to each:
        for i in range(len(elements_copy)):
            elements_copy[i] = apply([args[0], elements_copy[i]])

        return Functions.make_list(elements_copy)

    def filter(args):
        # args[0] is the function name that we're applying on args[1].
        # make sure exactly 2 arguments were provided:
        if len(args) != 2:
            return Error('(filter) error: expected 2 arguments, got %s.' % len(args))

        # make sure first argument is actually a function:
        if (args[0] in SYMBOLS and not isinstance(SYMBOLS[args[0]], Function)) and args[0] not in INBUILTFUNCTIONS:
            return Error('(filter) error: symbol %s is not a function.' % args[0])

        # make sure second argument (list) is actually a list and is in our symbol table:
        if args[1] not in SYMBOLS:
            return Error('(filter) error: symbol %s not found.' % args[1])
        if not isinstance(SYMBOLS[args[1]], list):
            return Error('(filter) error: symbol %s is not a list.' % args[1])

        # make an empty list:
        elements = []

        # apply the function to each, and only add element to our list
        # if the function returns true:
        for element in SYMBOLS[args[1]]:
            if apply([args[0], element]) == BOOLS[True]:
                elements.append(element)

        return Functions.make_list(elements)

    def f_delete(args):
        # delete symbols from our symbol table
        for arg in args:
            if arg not in SYMBOLS:
                return Error('Error: %s not found in symbol table.' % arg)

        # now that we're sure that all our args are in the symbol table, delete them:
        for arg in args:
            del SYMBOLS[arg]

    def f_read():
        return input()

# Function: a type for USER-DEFINED FUNCTIONS
class Function:
    def __init__(self, args, cmd):
        self.args = args
        self.cmd = cmd

    def run(self, f_args):
        # error-checking:
        if len(f_args) != len(self.args):
            return Error('User-defined function runtime error: expected %s arguments, received %s.' % (len(self.args), len(f_args)))

        # create local variable symbol table:
        FUNCTIONVARS = {}
        for arg, val in zip(self.args, f_args):
            FUNCTIONVARS[arg] = val

        # replace all occurrences of arguments in command as values and run them:
        cmdcpy = self.cmd.replace(')', ' ) ').replace('(', ' ( ').split()
        for t in range(len(cmdcpy)):
            if cmdcpy[t] in FUNCTIONVARS:
                cmdcpy[t] = str(FUNCTIONVARS[cmdcpy[t]])
        cmdcpy = ' '.join(cmdcpy)

        # execute cmd:
        return evaluate(cmdcpy)

    def __str__(self): # overload print() operator
        return self.cmd

class Utils:
  def tokenize(cmd):
    # first of all, strip cmd of any leading or trailing whitespace:
    cmd = cmd.lstrip().rstrip()

    # base case: if no spaces or parentheses (except outer), return cmd:
    # note: cmd is returned as a list because the recursive case's extend()
    #       only accepts lists
    if cmd.count(' ') == 0 or cmd.count('(') == cmd.count(')') == 0:
        return cmd.split()

    # now we determine which comes first, a space or an open parentheses:
    tokens = []
    if cmd.find(' ') < cmd.find('('):
        temp = cmd.split(' ', 1)
        tokens.append(temp[0])
        tokens.extend(Utils.tokenize(temp[1]))
    else:
        # otherwise, split by matching parentheses:
        l = cmd.find('(')
        r = l
        ct = 0
        for i in range(l+1, len(cmd)):
            if cmd[i] == ')':
                if ct == 0:
                    r = i+1
                    break
                ct += 1
            elif cmd[i] == '(':
                ct -= 1

        tokens.append(cmd[l:r]) # NOTE: WE ASSUME NOTHING IN cmd[:l]
        tokens.extend(Utils.tokenize(cmd[r:]))

    # remove any occurrences of '' from tokens:
    return list(filter(lambda a: a != '', tokens))

  def clean(cmd):
      # cut everything after semicolon, if present:
      if cmd.find(';') > 0:
          cmd = cmd[:cmd.find(';')]

      # deal with extra whitespaces:
      return ' '.join(cmd.split())

  def isnumber(x):
      if x.isnumeric(): return True
      try:
          float(x)
          return True
      except ValueError:
          return False

  def attempt_int(x):
      # error-checked int cast:
      try:
          return int(x)
      except:
          # we're not returning an error here, other functions will take care of this:
          print('Error: could not perform int conversion.')

  def attempt_float(x):
      # error-checked float cast:
      try:
          return float(x)
      except:
          # we're not returning an error here, other functions will take care of this:
          print('Error: could not perform float conversion.')

  def unbalanced(cmd):
      return cmd.count('(') != cmd.count(')')

def processSpecial(cmd):
    if cmd.startswith('define '):
        Functions.f_define(cmd[7:])
    elif cmd.startswith('if '):
        return Functions.handle_if(cmd[3:])
    elif cmd.startswith('or '):
        return Functions.handle_or(cmd[3:])
    elif cmd.startswith('and '):
        return Functions.handle_and(cmd[4:])
    elif cmd.startswith('lambda '):
        return Functions.handle_lambda(cmd[7:])

def runCmd(cmd):
    # split by whitespace:
    cmd = cmd.split()

    # if nothing in command, return nothing:
    if len(cmd) == 0:
        return None

    # if length of command = 1 then we just have to print symbol requested
    if len(cmd) == 1:
        # if the no-argument command is in our symbol table:
        if cmd[0] in SYMBOLS:
            # if this is a function name:
            if isinstance(SYMBOLS[cmd[0]], Function):
                # if this function takes no arguments, run it:
                if len(SYMBOLS[cmd[0]].args) == 0:
                    return SYMBOLS[cmd[0]].run([])
            # if it's a list, print it:
            if isinstance(SYMBOLS[cmd[0]], list):
                # we print lists using a custom function to avoid
                # showing '' marks on numeric values:
                Functions.printlist(SYMBOLS[cmd[0]])
                print()
            else: print(SYMBOLS[cmd[0]])
        elif cmd[0] == '$SYMBOLS': # only valid non-symbol command
            return Functions.printsymbols()
        elif cmd[0] == 'read' or cmd[0] == 'read-line':
            return Functions.f_read()
        else:
            return Error('Error: symbol %s not found.' %cmd[0])

        return None

    # otherwise, the first token in cmd is the function, and we need to apply it:
    return apply(cmd)

# apply: a separate function to apply the function to the arguments
#        so it can be used by map() and filter() without rewriting this code
def apply(cmd):
    # in case a function called another function & returned None:
    if cmd[0] == 'None': return None

    if cmd[0] == '+':
        return Functions.f_add(cmd[1:])
    if cmd[0] == '-':
        return Functions.f_subtract(cmd[1:])
    if cmd[0] == '*':
        return Functions.f_multiply(cmd[1:])
    if cmd[0] == '/':
        return Functions.f_divide(cmd[1:])
    if cmd[0] == '%' or cmd[0] == 'modulus':
        return Functions.f_modulus(cmd[1:])
    if cmd[0] == '=' or cmd[0] == 'eq?':
        return Functions.f_equal(cmd[1:])
    if cmd[0] == '!=' or cmd[0] == 'neq?':
        return Functions.f_notequal(cmd[1:])
    if cmd[0] == '>' or cmd[0] == 'greater?':
        return Functions.f_greater(cmd[1:])
    if cmd[0] == '<' or cmd[0] == 'smaller?':
        return Functions.f_smaller(cmd[1:])
    if cmd[0] == '>=' or cmd[0] == 'geq?':
        return Functions.f_greater_or_equal(cmd[1:])
    if cmd[0] == '<=' or cmd[0] == 'leq?':
        return Functions.f_smaller_or_equal(cmd[1:])
    if cmd[0] == 'list':
        return Functions.make_list(cmd[1:])
    if cmd[0] == 'car':
        return Functions.f_car(cmd[1:])
    if cmd[0] == 'cdr':
        return Functions.f_cdr(cmd[1:])
    if cmd[0] == 'cadr':
        return Functions.f_cadr(cmd[1:])
    if cmd[0] == 'caddr':
        return Functions.f_caddr(cmd[1:])
    if cmd[0] == 'cadddr':
        return Functions.f_cadddr(cmd[1:])
    if cmd[0] == 'caddddr':
        return Functions.f_caddddr(cmd[1:])
    if cmd[0] == 'reverse':
        return Functions.f_reverse(cmd[1:])
    if cmd[0] == 'append':
        return Functions.f_append(cmd[1:])
    if cmd[0] == 'cons':
        return Functions.f_cons(cmd[1:])
    if cmd[0] == 'length':
        return Functions.f_length(cmd[1:])
    if cmd[0] == 'at':
        return Functions.f_at(cmd[1:])
    if cmd[0] == 'even?':
        return Functions.iseven(cmd[1:])
    if cmd[0] == 'odd?':
        return Functions.isodd(cmd[1:])
    if cmd[0] == 'positive?':
        return Functions.ispositive(cmd[1:])
    if cmd[0] == 'list?':
        return Functions.islist(cmd[1:])
    if cmd[0] == 'display':
        return Functions.display(cmd[1:])
    if cmd[0] == 'map':
        return Functions.map(cmd[1:])
    if cmd[0] == 'filter':
        return Functions.filter(cmd[1:])
    if cmd[0] == 'del':
        return Functions.f_delete(cmd[1:])
    if cmd[0] == 'read' or cmd[0] == 'read-line':
        # no other arguments should be given here
        print('(read) Error: no arguments expected, received %s.' % len(cmd[1:]))
        return None
    if cmd[0] in SYMBOLS:
        # make sure this is actually a function call:
        if not isinstance(SYMBOLS[cmd[0]], Function):
            return Error('Error: %s is not a function.' % cmd[0])
        # run the function:
        return SYMBOLS[cmd[0]].run(cmd[1:])

    # otherwise, we haven't recognized the function:
    return Error('Error: function %s not found.' %cmd[0])

def evaluate(cmd):
    # first, wrap cmd around parentheses if its first non-whitespace character
    # is NOT a '('
    for i in cmd:
        if not i.isspace():
            if i != '(':
                cmd = '(%s)' % cmd
            break

    # strip opening and closing parentheses, if any:
    if cmd.count('(') > 0:
        # ERROR CHECK FIRST: make sure first occurrence of '(' comes before ')':
        if cmd.find('(')+1 > cmd.rfind(')'):
            return Error('Error: invalid parentheses.')

        # now strip the parentheses
        cmd = cmd[cmd.find('(')+1 : cmd.rfind(')')]

    # strip cmd of any leading and trailing whitespace:
    cmd = cmd.lstrip().rstrip()

    # if this is a number or a special symbol, return itself:
    if Utils.isnumber(cmd) or cmd in BOOLS.values():
        return cmd

    # if the command starts with any special words (define, if, cond, etc.), process it differently:
    if cmd.startswith(tuple(SPECIAL_WORDS)):
        return processSpecial(cmd)

    # if there are no parentheses left, evaluate & return result:
    elif cmd.count('(') == 0:
        return runCmd(cmd)

    # find first matching parentheses:
    # NOTE: can't use find() and rfind() here because of situations like (foo (bar) (fib))
    l = cmd.find('(')
    r = l
    ct = 0
    for i in range(l+1, len(cmd)):
        if cmd[i] == ')':
            if ct == 0:
                r = i+1
                break
            ct += 1
        elif cmd[i] == '(':
            ct -= 1

    cmd = cmd[:l] + str(evaluate(cmd[l:r])) + cmd[r:]
    return evaluate(cmd)

if __name__ == '__main__':
    cmd = 'pass'

    while cmd != 'exit':
        # print prompt:
        print('--> ', end='')
        # take user input:
        cmd = input()

        # ignore comments in user input:
        if cmd.find(';') > 0:
            cmd = cmd[:cmd.find(';')]

        # if user typed 'exit', break out of the loop:
        if cmd == 'exit': break

        # variable to keep track of whether user typed 'scratch' in the loop:
        isScratch = False

        # if cmd has unbalanced parentheses, wait until they're balanced:
        while Utils.unbalanced(cmd):
            # print extra prompt:
            print('... ', end='')

            # accept extra input:
            extraInput = ' ' + input() + ' '
            # cut everything after semicolon, if present:
            if extraInput.find(';') > 0:
                extraInput = extraInput[:extraInput.find(';')]

            # did the user type 'scratch'?
            if extraInput == ' scratch ':
                isScratch = True
                break

            cmd += extraInput

        # if the user entered 'scratch', then we reset the entire command & start over:
        if isScratch: continue

        # evaluate cmd:
        try:
            result = evaluate(Utils.clean(cmd))
        except:
            print('Error: invalid input.')
            continue

        # if result wasn't None, print it out:
        if result != None:
            if result in SYMBOLS:
                runCmd(result)
            else: print(result)

        # GARBAGE COLLECTION: clear symbol table of all temps:
        while GLOBALS['NUM_TEMPS'] >= 0:
            temp_name = '<TEMP_' + str(GLOBALS['NUM_TEMPS']) + '>'
            if temp_name in SYMBOLS:
                del SYMBOLS[temp_name]
            GLOBALS['NUM_TEMPS'] -= 1
        GLOBALS['NUM_TEMPS'] = 0 # after the loop it'll be -1
