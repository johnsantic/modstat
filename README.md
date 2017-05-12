==========
modstat.py
==========

modstat.py is a Python program that displays useful statistics for one or more Python source 
modules, including *import* and *from...import* module dependencies, and categorized source code line 
counts.


Usage and examples
------------------

How to run modstat:

    ``python modstat.py <zero or more command-line parameters>``

Command-line parameters:

    ``python modstat.py``

    Display statistics for all Python files (that is, *\*.py*) in the current working directory.

    ``python modstat.py *``

    (Windows) Display statistics for all Python files in the current working directory and all
    nested subdirectories. If a directory/subdirectory doesn't have any *.py* files, it is 
    silently ignored.

    ``python modstat.py \*``

    (Linux) Same as above, but keeps the Linux shell from expanding the \* character. If you 
    don't escape the \*, modstat doesn't see it (the Linux shell expands it to the directory 
    contents), so modstat won't know to visit the current working directory and nested 
    subdirectories. Instead, modstat will only process the expanded directory contents provided
    by the shell. This only happens with Linux, not with Windows.

    ``python modstat.py <dir/file path> ...``
    
    Display statistics for the specified directories or files. You can have multiple 
    *<dir/file path>* items, separated by one or more spaces. The path can be absolute or 
    relative. If *<dir/file path>* ends in a directory, modstat processes *\*.py* in that directory,
    but silently ignores it if no Python files are found. A directory name can not use wildcard
    characters. If *<dir/file path>* ends in a file name, modstat processes that file. For file 
    names, the *.py* suffix is optional, and is assumed if not present. A file name can use the
    \* and \? wildcard characters with the usual meanings. Note that \* all by itself (for
    Windows, or *\\\** for Linux) at the end of a *<dir/file path>* means *\*.py* in the terminal
    directory and all nested subdirectories.

    ``python modstat.py -h``
    
    Display a help message, which is the modstat.py module docstring.
    
Examples:

    ``python modstat.py joe``
    
    If *joe* is a directory, display statistics for *joe\\\*.py*, if  any such files exist. modstat
    uses the appropriate path separator for Windows or Linux. If *joe* is not a directory, display
    statistics for *joe.py* in the current working directory, if the file exists.

    ``python modstat.py ..\..\mydir\*  subdir1  subdir2\fname*``
    
    Follow the relative path to *mydir* then display statistics for *\*.py* in *mydir* and all
    nested subdirectories. Then display statistics for *\*.py* in the subdirectory *subdir1*. Then 
    display statistics for all file names that match the pattern *fname\*.py* in the subdirectory
    *subdir2*.
        
Statistics displayed
--------------------

As it runs, modstat displays module statistics on the console. Naturally, the output can be redirected
to a file using *\>file.txt*. For each Python source module, modstat displays the following information:

- File name and full path.

- Length of file in bytes.

- Creation date/time (Windows only, not available on Linux) and last-modified date/time (Windows and Linux).

- Names of all modules imported using *import/as* statements (if any), sorted in alphanumeric
  order.

- Names of all modules/identifiers imported using *from/import/as* statements (if any), sorted
  in alphanumeric order

- Line count information for the module: the total number of source lines, then a breakdown into
  executable lines and nonexecutable lines; then nonexecutable is further broken down into blank lines,
  comment-only lines, and docstring lines.
  
  Blank lines and comment-only lines can have leading whitespace. Whitespace is space, tab, or
  formfeed. Docstring lines are the first expression of a module, class definition,
  or function definition, if it is a string literal expression. Docstring lines count as nonexecutable lines.
  
  Triple-quoted strings that are not docstrings are counted as executable lines. The program parser
  obeys string quoting, so for example, lines inside a triple-quoted string that look like blank
  lines or comment-only lines are counted as part of the string (that is, as executable lines), and 
  not as blank lines or comment-only lines.

If modstat processed more than one Python source module, the program displays a summary at the
end:

- How may files successfully processed.

- Grand total line counts, same categories as above.

- Average per module line counts, rounded to integers. The average values might not add up 
  correctly due to rounding.

Here is the resulting output when running modstat on a Windows computer, requesting statistics
for the *modstat.py* source module itself::

    modstat - Python source module statistics; report generated Mon Nov  2 23:11:39 2015
    ----------------------------------------------------------------------------------------------
    File: modstat.py  Full path: C:\Users\John\Projects\modstat\modstat.py
    Size: 38691  Created: Fri Oct  2 18:21:26 2015  Modified: Mon Nov  2 23:09:00 2015
    Import: ast, glob, os, platform, sys, time
    From/Import: none
    Lines: 689  Executable: 343  Nonexecutable: 346  (Blank: 60  Comment: 120  Docstring: 166)

Here is the resulting output when running modstat for three Python source modules (note that the
module *pyasttest.py* is just for parsing test purposes, it is not an executable file)::

    modstat - Python source module statistics; report generated Mon Nov  2 23:09:03 2015
    ----------------------------------------------------------------------------------------------
    File: cashflow.py  Full path: C:\Users\John\Projects\cashflow\cashflow.py
    Size: 52156  Created: Wed Sep 23 01:44:19 2015  Modified: Wed Oct 28 23:23:17 2015
    Import: datetime, sys
    From/Import: module calendar: isleap, month_name, module enum: Enum, module os: remove, 
        module os.path: abspath, isfile
    Lines: 905  Executable: 501  Nonexecutable: 404  (Blank: 84  Comment: 115  Docstring: 205)
    ----------------------------------------------------------------------------------------------
    File: modstat.py  Full path: C:\Users\John\Projects\modstat\modstat.py
    Size: 38691  Created: Fri Oct  2 18:21:26 2015  Modified: Mon Nov  2 23:09:00 2015
    Import: ast, glob, os, platform, sys, time
    From/Import: none
    Lines: 689  Executable: 343  Nonexecutable: 346  (Blank: 60  Comment: 120  Docstring: 166)
    ----------------------------------------------------------------------------------------------
    File: pyasttest.py  Full path: C:\Users\John\Projects\modstat\pyasttest.py
    Size: 5826  Created: Sun Oct 18 00:31:40 2015  Modified: Tue Oct 27 20:03:57 2015
    Import: a1, a1, a10, a2, a3, a4 as bbb, a5, a5 as bb, a6 as cc, a7, a8, a9, anothername, 
        anothername2, characters, characters2, hereisanother, hereisanother2, keepgoing, 
        keepgoing2, longname, longname2, morethan, morethan2, ninety, ninety2, os, os.path.google, 
        path.rem.ext, re, re, sys, thisonetoo, thisonetoo2, tryingfor, tryingfor2, trythat, 
        trythis
    From/Import: module .: carnot as jjj, carp, terp as terp1, module ...: arch, blueb, 
        nogo, module .....: blob, module ....jane: dog as cat, pet as dog, module bill.dan.ed: 
        black, blue as green, red as orange, module carry: *, module joe: b1, b2, b3, 
        b4 as yahoo, b5 as bahoo, module rezz: *
    Lines: 215  Executable: 127  Nonexecutable: 88  (Blank: 22  Comment: 38  Docstring: 28)
    ----------------------------------------------------------------------------------------------
    Total Python source files successfully processed: 3
    Grand total line counts:
    Lines: 1809  Executable: 971  Nonexecutable: 838  (Blank: 166  Comment: 273  Docstring: 399)
    Average lines per Python source file: (values might not add correctly due to rounding)
    Lines: 603  Executable: 324  Nonexecutable: 279  (Blank: 55  Comment: 91  Docstring: 133)

modstat internal operation
--------------------------

The modstat program works by parsing each Python source module twice.

The first time uses the built-in parsing capability of the Python interpreter, using functions from
the Python library module *ast.py*. Function *ast.parse()* produces an Abstract Syntax Tree 
(AST) for the entire Python source module. The AST consists of a set of nested node objects, 
each of which describes one component of one statement of the module's Python source code. 
The modstat program uses function *ast.visit()* to examine various AST nodes to collect certain
information required for later printout. For example, this is how modstat finds out where the
docstrings are, and which external modules are imported by the source code.

The second time uses a simple parser inside the modstat program to compute executable and 
nonexecutable line counts. The line counts are adjusted before printout to account for docstrings.

Every Python source module submitted to modstat must have correct compile-time syntax, or modstat
displays an error message and the offending source module is skipped. None of the submitted 
Python source modules are executed at all, so run-time errors, if any, are not discovered 
and don't impede modstat program operation.

Development toolset
-------------------

- Anaconda3 Python version 3.4.3, standard library, no other packages.

- Spyder and IPython for testing and debugging.

- Edited with notepad++.

- All running on Windows 7. 

The modstat program has been tested under Windows 7 and Linux Ubuntu 14.4. For Linux, observe the 
comment above about escaping the \* character in command-line parameters.

Installation
------------

The entire program consists of a single file, *modstat.py*. There is no formal installation
procedure, merely copy the file from the repository to your local hard drive.

License
-------

The MIT License (MIT) - Copyright (c) 2015 John Santic

Permission is hereby granted, free of
charge, to any person obtaining a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

The Software is provided "as is", without warranty of any kind, express or implied, including
but not limited to the warranties of merchantability, fitness for a particular purpose and
noninfringement. In no event shall the authors or copyright holders be liable for any claim,
damages or other liability, whether in an action of contract, tort or otherwise, arising from,
out of or in connection with the Software or the use or other dealings in the Software.

Author
------

John Santic, email johnsantic  <at>  g m a i l  <dot>  c o m.

Revision history
----------------

25-Oct-2015 - Completed release 1.0 version of the program.

02-Nov-2015 - Completed release 1.0 version of the documentation.
