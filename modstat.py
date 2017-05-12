"""
modstat.py - Print out statistics for one or more Python source modules.

Usage:
    python modstat.py <zero or more command-line parameters>

Examples:
    python modstat.py    - print statistics for *.py in current working directory
    python modstat.py *    - (Windows) print statistics for *.py in cwd and all nested directories. 
        If a directory doesn't have any .py files, it is silently ignored.
    python modstat.py \*   - (Linux) Same as above, but keeps shell from expanding * character. If
        you don't escape the *, modstat doesn't see it (the Linux shell expands it to the directory
        contents), so modstat won't know to visit cwd and nested directories.
    python modstat.py <dir/file path> ...    - print statistics for specified dir/file. You can have
        multiple dir/file path items, separated by spaces. The path can be absolute or relative. If
        the dir/file path ends in a directory, process *.py in that directory, silently ignore if no
        *.py files found. Directory names can not use wildcard characters. If the dir/file path ends
        in a filename, process those files. The .py suffix is optional, and is assumed if not
        present. A file name can use * and ? wildcard characters with the usual meanings. Note that
        * all by itself (for Windows, \* for Linux) at the end of a dir path means *.py in the 
        terminal directory and all nested directories.
    python modstat.py -h    - print help message
        
Results:
    For each Python module, the program prints the following information, in a compact presentation:
    - filename and full path
    - length of file in bytes
    - the creation date/time (Windows only) and last-modified date/time (Windows & Linux)
    - the names of all modules imported using import/as statements (if any)
    - the names of all modules/identifiers imported using from/import/as statements (if any)
    - line count information for the module: the total number of source lines, then a breakdown into
      executable lines and nonexecutable lines; nonexecutable is further broken down into blank
      lines, comment-only lines, and docstring lines. Blank lines and comment-only lines allow
      leading whitespace. Docstring lines are the first string literal expression of a module, class
      definition, or function definition. Triple-quoted strings that are not docstrings are counted
      as executable lines. The program parser obeys string quoting, so for example, lines inside a
      triple-quoted string that look like blank lines or comment-only lines are counted as part of
      the string, and not as blank lines or comment-only lines.
    - if the program processed more than one Python module, the program prints how may files, grand
      total line counts (same categories as above), and average per module line counts (rounded to
      integers). The average values might not add up correctly due to rounding.

Operation:
    The program works by parsing each Python source module twice. The first time uses the built-in
    parsing capability of the Python interpreter, which produces an Abstract Syntax Tree (AST) for 
    the entire program consisting of a set of nested nodes. The modstat program visits various nodes
    to gather interesting information for later printout. The second time uses a simple parser
    inside the modstat program to compute executable and nonexecutable line counts. Every Python
    source module submitted to modstat must have correct compile-time syntax, or an error is printed
    and the source module is skipped. None of the submitted Python source modules are executed at
    all, so run-time errors, if any, are not discovered and don't impede modstat program operation.
        
License:
    The MIT License (MIT) - Copyright (c) 2015 John Santic - Permission is hereby granted, free of
    charge, to any person obtaining a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including without limitation the
    rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
    Software, and to permit persons to whom the Software is furnished to do so, subject to the
    following conditions:

    The above copyright notice and this permission notice shall be included in all copies or
    substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
    BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Author:
    John Santic, email johnsantic  <at>  g m a i l  <dot>  c o m

Toolset:
    Anaconda3 Python version 3.4.3, standard library, no other packages, running on Windows 7. The 
    program also runs on Ubuntu Linux, but observe the comment above about escaping the * character.

Revision history:
    25-Oct-2015 - create original
"""

import ast
import os
import sys
import time
import glob
import platform

### Global Variables ###

# Counts how many source code lines in a Python file for the various categories indicated. Note
# that docstring lines are counted separately by a different mechanism, but all docstring lines
# are also counted in the executable line count below. This applies only to the internal program
# variables. In the program printout, docstring lines are NOT executable lines, but one category
# of nonexecutable lines. At time of printout, the line counts are recomputed accordingly.
# Grand totals for all Python files processed.
total_blank_lines = 0
total_comment_lines = 0
total_executable_lines = 0
total_docstring_lines = 0
docstring_lines = 0  # must be global because several functions use it

# List of module names from all import statements of a Python file; the name includes an "as" name
# if provided by the source statement.
import_names = []

# List of module, identifier, and "as" names from all from/import statements of a Python file.
# Each list item is a 2-tuple providing information for one from/import statement: (module name, 
# identifier/as names). Module name is a string which can include relative path dots (if any).
# Indentifier/as names is a list of strings giving the identifiers (plus "as" name if provided) for 
# that particular from/import statement.
from_import_names = []

class NodePicker(ast.NodeVisitor):
    """
    This class inherits from NodeVisitor in the module ast.py, which visits all nodes in the AST
    (Abstract Syntax Tree) for a Python source module. We override the visitor function for several
    AST nodes that are of interest to the modstat program. For more information about AST nodes and
    how to use them, see the following excellent website:
    https://greentreesnakes.readthedocs.org/en/latest/index.html
    """

    def visit_Module(self, node):
        """
        For nodes that represent a top-level module (there should be only one in the AST), see if
        the module has a docstring, and if so, count how many source code lines are in the 
        docstring. Adding one to the count takes care of the case when the closing triple quote is 
        on a line by itself. Other placements of triple quotes work out as intended.
        """
        global docstring_lines
        docstring = get_docstring(node)
        if docstring:
            line_count = docstring.count("\n") + 1
            docstring_lines += line_count
        # Since a Module node will have other important AST nodes nested under it, basically the
        # whole program, visit all the nested nodes so we don't miss anything important.
        self.generic_visit(node)
        return

    def visit_ClassDef(self, node):
        """
        For nodes that represent a class definition, see if the class definition has a docstring,
        and if so, count how many source code lines are in the docstring. Adding one to the count 
        takes care of the case when the closing triple quote is on a line by itself. Other
        placements of triple quotes work out as intended.
        """
        global docstring_lines
        docstring = get_docstring(node)
        if docstring:
            line_count = docstring.count("\n") + 1
            docstring_lines += line_count
        # Since a ClassDef node can have other important AST nodes nested under it, including
        # function definitions, visit all the nested nodes so we don't miss anything important.
        self.generic_visit(node)
        return

    def visit_FunctionDef(self, node):
        """
        For nodes that represent a function definition, see if the function has a docstring, and
        if so, count how many source code lines are in the docstring. Adding one to the count takes
        care of the case when the closing triple quote is on a line by itself. Other placements of
        triple quotes work out as intended.
        """
        global docstring_lines
        docstring = get_docstring(node)
        if docstring:
            line_count = docstring.count("\n") + 1
            docstring_lines += line_count
        # Since a FunctionDef node can have other important AST nodes nested under it, including
        # nested functions, visit all the nested nodes so we don't miss anything important.
        self.generic_visit(node)
        return 
    
    def visit_Import(self, node):
        """
        For nodes that represent an import statement, collect all the module names and "as" names
        for this one import statement.
        """
        global import_names
        for alias in node.names:
            mod_name = alias.name  # the module that is being imported
            if alias.asname:  # is there an "as" phrase?
                mod_name = mod_name + " as " + alias.asname  # yes, tack it on to the module name
            import_names.append(mod_name)  # save the info for later printout
        # Import doesn't have nested nodes, so no need to call generic visitor.
        return
        
    def visit_ImportFrom(self, node):
        """
        For nodes that represent a from/import statement, collect the module name (which can include
        relative path dots) plus all the identifers (each of which can have an "as" name) for this
        one from/import statement. This version of the import statement supports both absolute and
        relative module names, so it's a little more complicated.
        """
        global from_import_names
        mod_name = "." * node.level  # set up relative path dots, if any
        if node.module:
            mod_name += node.module  # tack on module name, if any
        identifier_list = []  # the items imported from this module
        for alias in node.names:
            identifier_name = alias.name  # get the item
            if alias.asname:
                identifier_name = identifier_name + " as " + alias.asname  # tack on "as" name
            identifier_list.append(identifier_name)  # save for later printout
        # All done extracting identifier names from node, sort the list for convenience.
        identifier_list.sort()
        from_import_names.append((mod_name, identifier_list))  # append info as a 2-tuple
        return

def get_docstring(node):
    """
    Return the docstring for a given AST node or None if no docstring was found.  Must only be 
    called for nodes of type Module, FunctionDef, and ClassDef, as these are the only node types
    that allow a docstring. A docstring is defined as the very first executable line of the Module,
    FunctionDef, or ClassDef, if that line is an expression and the expression type is a string
    literal. Note that comment-only lines or blank lines immediately preceding the docstring are 
    permitted, since they are swallowed up by the parser and the syntax analyzer never sees them.
    This function is based on the same-named funtion in the ast.py library module.
    """
    # The AST node must be a body node and the first element must be a string literal expression.
    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
        return node.body[0].value.s  # s is the string literal
    return None

# Parsing states for the line-counting function (see below).
PS_START        = 0  # at the first char of a line, not within a string or comment
PS_COMMENT      = 1  # processing a comment-only line
PS_EXECUTABLE   = 2  # processing an executable line, but not in a string or trailing comment
PS_EXEC_COMMENT = 3  # in the trailing comment of an executable line
PS_START_STRING = 4  # processing one or more quotes that start a string on an executable line
PS_EXEC_STRING  = 5  # in a string within an executable line
PS_END_STRING   = 6  # processing closing quote (or quotes) on an executable line

def count_lines(source):
    """
    Parse the Python source code for comment-only lines or blank lines, each of which are separately
    counted. In both cases, leading whitespace (space, tab, formfeed) is permitted; the line
    terminates with a newline. If there are any other characters on a line, it is considered to be
    an executable line, and counted as such. While parsing, we need to pay attention to quoted 
    strings, and ignore lines that appear to be comment-only or blank lines within a quoted string.
    All lines that make up a quoted string are considered to be executable lines. We also need to
    pay attention to Python comments, and ignore quote characters inside a comment.

    Inputs: source = string containing entire source code for one Python module
    Outputs: 3-tuple of integers containing line counts:
      blank_lines - count of all blank lines not in a string (leading whitespace allowed)
      comment_lines - count of all comment-only lines not in a string (leading whitespace allowed)
      executable_lines - count of every newline that is not in a blank or comment-only line
    """
    blank_lines = 0  # note that these are NOT the global variables, these are local to this function
    comment_lines = 0
    executable_lines = 0
    parse_state = PS_START
    
    # Loop through every character in the source file, processing each character according to the
    # current parsing state.
    for char in source:

        if parse_state == PS_START:  # at the very start of a line (not in string or comment)
            if char in " \t\f":  # if line starts with whitespace, skip over it
                continue
            if char == "\n":  # if newline, this is a blank line
                blank_lines += 1
                continue
            if char == "#":  # if hash character, this is a comment-only line
                parse_state = PS_COMMENT  # dump rest of line
                continue
            if char in "\"\'":  # if single or double quote, starting a string
                quote_char = char  # remember what type of quote
                quote_count = 1  # and how many we got in a row
                escape_active = False  # initialize so we process string backslashes correctly
                parse_state = PS_START_STRING
                continue
            parse_state = PS_EXECUTABLE  # any other char, treat as executable line
            continue
            
        if parse_state == PS_COMMENT:  # dumping the remainder of a comment-only line
            if char == "\n":  # if newline, done with comment-only line, else ignore character
                comment_lines += 1
                parse_state = PS_START
            continue

        if parse_state == PS_EXECUTABLE:  # this is an executable line, check for a few things
            if char == "\n":  # if newline, all done with this line (note: technically, an executable
                executable_lines += 1  # line can be continued with backslash, but that continued
                parse_state = PS_START  # line's chars will kick us back into executable state 
                continue               # anyway)
            if char in "\"\'":  # if single or double quote, starting a string
                quote_char = char  # remember what type of quote
                quote_count = 1  # and how many we got in a row
                escape_active = False  # initialize so we process string backslashes correctly
                parse_state = PS_START_STRING
                continue
            if char == "#":  # if hash character, this is a comment on an executable line
                parse_state = PS_EXEC_COMMENT  # dump remainder of executable line
            continue
            
        if parse_state == PS_EXEC_COMMENT:  # dumping the remainder of a commented executable line
            if char == "\n":  # if newline, all done with this line
                executable_lines += 1  # comment on an executable line counts as executable
                parse_state = PS_START
            continue

        # Come here if we already got one quote on an executable line, we are starting a string.
        if parse_state == PS_START_STRING:
            if char == quote_char:  # got another quote of same type?
                quote_count += 1  # yes
                if quote_count == 3:  # confirmed to be a triple quote, now in a string
                    parse_state = PS_EXEC_STRING
                continue
            # Not another opening quote character, see if we just ended an empty string. If so,
            # the string was "" or '' and the present character must be processed not as a string
            # character but as a non-string executable line character.
            if quote_count == 2:  # if got two quotes, string all done already, was "" or ''
                if char == "\n":
                    executable_lines += 1
                    parse_state = PS_START
                    continue
                if char == "#":  # if hash character, this is a comment on an executable line
                    parse_state = PS_EXEC_COMMENT
                    continue
                parse_state = PS_EXECUTABLE  # two quotes followed by normal char
                continue
            # We are now in a quoted string, either "string" or 'string'.
            if char == "\\":
                escape_active = True  # watch out for escaped quotes inside a string
            parse_state = PS_EXEC_STRING
            continue

        # If an executable line contains a quoted string (single, double, or triple), ignore what's
        # inside the string up to and including the closing quote (or quotes). In particular, don't
        # react to lines that look like blank lines or comment lines inside a triple-quoted string.
        # They are properly counted as executable lines since they are inside a quoted string.
        # We also need to watch out for escaped quotes, that is \" or \', since an escaped quote
        # is inert and can not end a string. The following escaped quote patterns are valid:
        #   "aaaaa\\"  or  "aaaaa\\\\"  or any even number of backslashes
        #   "aaaaa\""  or  "aaaaa\\\""  or any odd number of backslashes
        # We don't have to worry about parsing incorrect syntax. The AST parser will detect that
        # earlier, and we give the modstat user an error message, so we never have to try to parse
        # Python modules with syntax errors.
        if parse_state == PS_EXEC_STRING:
            if escape_active:  # if previous char was backslash
                escape_active = False
                if char == quote_char or char == "\\":  # consider these chars to be inert
                    continue  # swallow them, fall thru for others so newline can be processed
            if char == "\\":  # is this char a backslash?
                escape_active = not escape_active  # yes, special handling for next character
            if char == "\n":  # if newline, count string line as executable line
                executable_lines += 1
                continue  # stay in string state until closing quote
            if char == quote_char:  # if a quote, this might be the closing quote
                quote_count -= 1
                if quote_count == 0:  # if opening quote was " or ', the string is now done
                    parse_state = PS_EXECUTABLE  # back to regular executable line parsing
                    continue
                # See if we get the remaining two quotes of a closing triple quote.
                parse_state = PS_END_STRING
            continue
        
        # Last state, see if we get the remaining two quotes of closing triple quote.
        if char == quote_char:
            quote_count -= 1
            if quote_count == 0:  # if got all three, the string is now done
                parse_state = PS_EXECUTABLE  # back to regular executable line parsing
            continue
        # Anything other than a quote, false alarm, go back to string processing.
        if char == "\\":
            escape_active = True
        if char == "\n":
            executable_lines += 1
        quote_count = 3  # since this was a false alarm, we still need three closing quotes
        parse_state = PS_EXEC_STRING
        continue
 
    # Drop out of "for" loop when entire source file processed, return the results.
    return blank_lines, comment_lines, executable_lines
      
def print_import_info():
    """
    Print out, in compact form, all the module names from the various import/as statements of
    the current Python source file.
    
    Inputs: global import_names = list of all info, see definition above for full description.
    """
    global import_names

    import_len = len(import_names)  # may be zero if no modules imported
    if import_len > 0:  # any module names?
    
        import_names.sort()  # alphabetize the list
        lead_in = "Import: "  # lead-in words for the printout
        print(lead_in, end="")
        line_len = len(lead_in)  # keep track of line length, to insert a newline when necessary
        while import_len > 0:
            mod_name = import_names.pop(0)
            if import_len == 1:  # last module name
                print(mod_name)  # end with newline instead of comma
                return  # all done printing import statements
            print(mod_name, end=", ")
            line_len += len(mod_name) + 2
            if line_len > 80:
                print("\n    ", end="")
                line_len = 4  # continuation lines indent four spaces
            import_len -= 1
        # end while
    else:
        print("Import: none")
    return

def print_from_import_info():
    """
    Print out, in compact form, all the module and identifier names from the various from/import/as
    statements of the current Python source file.
    
    Inputs: global from_import_names = list of all info, see definition above for full description.
    """
    global from_import_names

    # Helper function to print out information for one from/import/as statement. Pass in a flag to
    # indicate if this is the last module from the statement, so we can omit the final comma.
    def print_info(last_module):
        nonlocal line_len, identifier_list
        print("module", mod_name + ": ", end="")
        line_len += len(mod_name) + 9
        if line_len > 80:
            print("\n    ", end="")
            line_len = 4  # continuation lines indent four spaces
        while len(identifier_list) > 0:
            ident_name = identifier_list.pop(0)
            if len(identifier_list) == 0 and last_module:  # if last identifier of last module
                print(ident_name)  # finalize printout, end with newline instead of comma
                return  # all done printing from/import/as statements
            print(ident_name, end=", ")  # not last identifier of last module, keep printing
            line_len += len(ident_name) + 2
            if line_len > 80:
                print("\n    ", end="")
                line_len = 4  # continuation lines indent four spaces
        # end while
        return

    # Print from/import/as info, if there were any statements like that.
    import_len = len(from_import_names)  # may be zero if no from/import statements
    if import_len > 0:
        from_import_names.sort(key = lambda data: data[0])  # sort based on the module name
        lead_in = "From/Import: "
        print(lead_in, end="")
        line_len = len(lead_in)  # keep track of line length to break up lines that get too long
        
        # Loop to process each module from the list.
        while import_len > 0:
            (mod_name, identifier_list) = from_import_names.pop(0)
            print_info(import_len == 1)  # pass in True/False flag to indicate last module status
            import_len -= 1
        # end while import_len > 0, drop out when done
    else:
        print("From/Import: none")
    return

def process_file(file_name):
    """
    Process one Python source file: read it, parse it to produce an Abstract Syntax Tree, extract
    useful information from the AST, then parse the source file again to extract line count
    information. Finally, print a report for this source file. For serious errors, just print an
    error message and skip this file - don't kill the modstat program.
    
    Inputs: file_name = file name of source module, must end in .py and include path if necessary
            global xxx_lines = line count information is updated
    Returns: True/False flag indicating if the source module was successfully processed
    """
    global total_blank_lines, total_comment_lines, total_executable_lines, total_docstring_lines
    global docstring_lines

    # Counts how many source code lines in a Python file for the various categories indicated. Note
    # that docstring lines are counted separately by a different mechanism, but all docstring lines
    # are also counted in the executable line count below. This applies only to the internal program
    # variables. In the program printout, docstring lines are NOT executable lines, but one category
    # of nonexecutable lines. At time of printout, the line counts are recomputed accordingly.
    blank_lines = 0
    comment_lines = 0
    executable_lines = 0
    docstring_lines = 0
    
    # Print a line to separate individual module printouts.
    print("-----------------------------------------------"  \
          "-----------------------------------------------")

    # Collect some basic information about the file before we try to parse it. This also verifies
    # that we can access the file. If not, print error message but keep processing other modules.
    if not os.path.isfile(file_name):  # is this a real file?
        print("Unable to access file", file_name, "- file ignored")  # exit if no
        return False
    try:
        base_name = os.path.basename(file_name)
        full_name = os.path.abspath(file_name)
        size = os.path.getsize(file_name)
        ctime = os.path.getctime(file_name)
        mtime = os.path.getmtime(file_name)

        fp = open(file_name, "rt", errors="replace")  # read the entire source module into a string,
        program = fp.read()                           # for future parsing, ignore encoding errors
        fp.close()
    except OSError as exception:
        print("Error accessing file", file_name, "- file ignored")
        return False

    # Parse the program to create an AST (Abstract Syntax Tree) that will allow us to easily extract
    # useful information like module/class/function docstrings and the two types of import
    # statements. Watch out for parsing errors - we don't want the modstat program to crash due to 
    # syntax errors in the Python program being examined. We mostly care about compile-time syntax 
    # errors. Since the Python program is never executed, we never have to worry about run-time
    # errors.
    try:
        tree = ast.parse(program)
    except (SyntaxError, TypeError, ValueError) as exception:
        if isinstance(exception, SyntaxError):
            print("File", file_name, "can not be processed, it has a syntax error on line",
                exception.lineno)
            return False
        print("File", file_name, "can not be processed due to a type or value error"  \
            " while parsing its source code")
        return False

    # Visit every node of the abstract syntax tree to collect the information we desire (all the
    # docstrings and import statements in the program).
    NodePicker().visit(tree)
    total_docstring_lines += docstring_lines  # docstrings are counted during AST node visiting
    
    # After using AST to parse the program, we know the syntax is good, so use our own simple parser
    # to count how many blank lines, comment-only lines, and executable lines.
    blank_lines, comment_lines, executable_lines = count_lines(program)
    total_blank_lines += blank_lines  # update grand totals
    total_comment_lines += comment_lines
    total_executable_lines += executable_lines
    
    # Print basic information about the Python source module.
    print("File:", base_name, " Full path:", full_name)
    if platform.system() == "Windows":
        print("Size:", size, " Created:", time.ctime(ctime), " Modified:", time.ctime(mtime))
    else:
        print("Size:", size, " Modified:", time.ctime(mtime))
    
    # Print information about import/as and from/import/as statements, if any.
    print_import_info()
    print_from_import_info()
    
    # Print line count information for this module. Note that the parser's executable line count is
    # adjusted to omit docstring lines, which are listed separately.
    print("Lines:", blank_lines + comment_lines + executable_lines,
          " Executable:", executable_lines - docstring_lines,
          " Nonexecutable:", blank_lines + comment_lines + docstring_lines,
          " (Blank:", blank_lines, 
          " Comment:", comment_lines,
          " Docstring:", str(docstring_lines)+")")
    return True  # indicate source module was successfully processed
    
def main ():
    """
    This is the main function for the modstat program. Process the command-line parameters to see
    for which Python source files the user wants statistics. Then call the file processing function 
    for each source file, which parses the file and prints relevant information for that file.
    If more than one file was processed, print a final tally below.
    """
    global total_blank_lines, total_comment_lines, total_executable_lines, total_docstring_lines

    file_count = 0  # no files processed yet
    
    # Keep a list of path/file parameters from the command line that we iterate through. These items
    # might refer to an exact file, or the filename might have wildcards characters.
    todo = []
    
    # If Help command, print module documentation string at top of modstat.py file.
    if (len(sys.argv) == 2) and (sys.argv[1] == "-h"):
        print(__doc__)
        sys.exit(0)  # exit modstat program, all done

    # If no command-line parameters, default to *.py for current working directory.
    if len(sys.argv) == 1:  # ignore the script name
        sys.argv.append("*.py")

    # At this point, we know len(sys.argv) is at least 2, with sys.argv[0] being "modstat.py" and
    # sys.argv[1] being the first real cmd-line parm. Even if there had been no real parms, we put
    # "*.py" into sys.argv[1] in the absence of anything else.
    
    # In the next section of code, we loop to process each command-line parameter. We process each
    # parameter and put the resulting path/file string in the todo list for later further modstat
    # processing. Each parm in the todo list will be a path/file with an exact file name ending in
    # .py, or a file name containing wildcard characters then ending in .py.
    
    # Here are the possible command-line parameter variations, for each sys.argv[] item:
    #  Case: a file name (possibly with wildcards) ending in .py, possibly with a leading dir path:
    #    Action: put it in todo list as-is
    #  Case: a single * (for Windows, \* for Linux), possibly with a leading dir path:
    #    Action: visit terminal dir and all nested dirs, put dir/*.py in todo if any .py files in dir
    #  Case: a dir path ending in a directory:
    #    Action: put dir/*.py in todo list
    #  Otherwise, assume it's a file name without trailing .py, append .py and put in todo list
    
    for idx in range(1, len(sys.argv)):  # process all cmd line parms, there's at least one
    
        arg = sys.argv[idx].strip()  # get next cmd line parm, without whitespace
        if arg.endswith(".py"):  # does arg already end with .py suffix?
            todo.append(arg)  # yes, use it as-is
            continue  # go back to the top to process next command-line parameter
            
        # See if the arg is a single *, or a * at the end of a path (such as basedir/mydir/*).
        # This is a special case that requires a nested directory search for .py files.
        if (len(arg) == 1 and arg[0] == "*") or (arg[-1] == "*" and arg[-2] == os.sep):
            if len(arg) == 1:
                start_dir = os.curdir  # arg was solitary *, start search from cwd
            else:
                start_dir = arg.rstrip("*")  # otherwise start from end of provided dir path
                
            # Loop through initial dir and all nested dirs, looking for .py files.    
            for dirpath, dirnames, filenames in os.walk(start_dir):
                found_py_flag = False
                for file in filenames:  # for every visited dir, look thru all files
                    if file.endswith(".py"):  # look for Python files
                        found_py_flag = True
                        break  # break out of inner for loop
                    # end if
                # end for
                # If found Python files, at this point we don't need to remember each .py name. Just 
                # save dirpath/*.py in todo, and later we will find the .py file names again.
                if found_py_flag:
                    py_dir = os.path.join(dirpath, "*.py")
                    todo.append(py_dir)
            # end for, loop through remaining nested dirs
            continue  # go back to the top to process next command-line parameter
            
        # If the arg is a path ending in a directory, put path/*.py in todo.
        if os.path.isdir(arg):
            py_dir = os.path.join(arg, "*.py")
            todo.append(py_dir)
            continue  # go back to the top to process next command-line parameter
            
        # If we get here, this is a general catch-all, assume the arg is an incomplete file name,
        # possibly containing wildcard characters, but not ending in .py. There also may be a
        # leading dir path. Just add .py and put in todo, hopefully it will match some files.
        todo.append(arg + ".py")
        
    # end for, loop until all command-line parameters processed

    # Print modstat program header before processing any files.
    print("modstat - Python source module statistics; report generated", time.ctime())
    
    # Now that we have processed all cmd-line parms and created a todo list of dir/file names, 
    # process all the resulting names. The todo filename definitely can have wildcard characters, 
    # so we must use glob to do filename pattern matching.
    for pattern in todo:
        for match in glob.glob(pattern):
            # Print module statistics for each Python source file that we find.
            if process_file(match):
                file_count += 1  # inc file counter if file processed successfully
        # end for, *.py matches in current todo item
    # end for, all todo items
    
    # If we processed more than one source file, print separator and final tally for all files.
    if file_count > 1:
        final_lines = total_blank_lines + total_comment_lines + total_executable_lines
        final_executable = total_executable_lines - total_docstring_lines
        final_nonexecutable = total_blank_lines + total_comment_lines + total_docstring_lines
        final_blank = total_blank_lines
        final_comment = total_comment_lines
        final_docstring = total_docstring_lines
        print("-----------------------------------------------"  \
              "-----------------------------------------------")
        print("Total Python source files successfully processed:", file_count)
        print("Grand total line counts:")
        print("Lines:", final_lines,
              " Executable:", final_executable,
              " Nonexecutable:", final_nonexecutable,
              " (Blank:", final_blank, 
              " Comment:", final_comment,
              " Docstring:", str(final_docstring)+")")
        print("Average lines per Python source file: (values might not add correctly due to rounding)")
        print("Lines:", round(final_lines/file_count),
              " Executable:", round(final_executable/file_count),
              " Nonexecutable:", round(final_nonexecutable/file_count),
              " (Blank:", round(final_blank/file_count), 
              " Comment:", round(final_comment/file_count),
              " Docstring:", str(round(final_docstring/file_count))+")")
        # end if file_count > 1
    return

# This program is not a library so you would not normally import it into another module. You usually
# run the program by itself on the python command line, for example: "python modstat.py". Therefore,
# the module name will normally be __main__ so the lines below are what actually run the program.
if __name__ == '__main__':
    main()
# Once main() returns, drop out of the bottom and the program is done. 
