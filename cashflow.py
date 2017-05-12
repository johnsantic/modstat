""" cashflow.py - Process cashflow journal and category files, produce report of income and expenses.

Usage: python cashflow.py <optional command line parameter>

Command line parameters (only one allowed for any invocation of the program):

  -c <pathname>  Config: specify path where category file is located, including file name, then exit.
                 Example: -c C:\\Users\\John\\Documents\\financial\\cashflow_categories.txt
                 (The program was written for Windows and may require file changes for Linux/Mac.)
  -s             Show where program thinks category file is located, exit.
  -h             Print help message, exit.
  <year>         Four-digit year, which year's cashflow file to process, for example 2015; defaults
                 to current year.

There are two required input files:

  cashflow_categories.txt - contains a list of all the cashflow categories. Default location is
  DEFAULT_CAT_DIR (see string definition below), but if a config file DEFAULT_CONFIG_FILE exists in
  current working directory, the path/name to the category file is obtained from the config file.
  Valid category file contents:
  
    # <comment line, ignored, line must start with #, leading spaces OK> <newline>       - Or -
    <blank line, ignored, only contains newline, leading spaces OK> <newline>            - Or -
    <cat code> <descr> <optional comment> <newline> - Cat code line, fields separated by one or more
       spaces -
    <cat code> is defined as:           (leading spaces OK)
       <digit 1 to 9>                                                     - Level 1, Or -
       <digit 1 to 9>.<digits 1 to 99>  (leading 0, e.g. 08, not allowed) - Level 2, Or -
       <digit 1 to 9>.<digits 1 to 99>.<digits 1 to 99>                   - Level 3, Or -
       <digit 1 to 9>.<digits 1 to 99>.<digits 1 to 99>.<digits 1 to 99>  - Level 4 -
    <descr> is mandatory description field, unquoted text
    <optional comment> is optional comment field, starting with #

  Example cat file lines: (normally, the lines start in column 1)
  
    # Expense categories
   
    2 Expenses # money going out, for all purposes
    2.1 Housing
    2.1.1 Mortgage & rent # home, apartment, storage unit
    2.1.2 Regular maintenance # including supplies/materials but not general-purpose tools
    2.1.2.1 Grounds maintenance # lawn & garden & driveway, materials, services, equipment/tools
    2.1.2.2 Major systems # HVAC, water, electrical
    2.1.3 Repair # including supplies/materials but not general-purpose tools

  <year>_cashflow_journal.txt - contains a list of individual income/expense transactions records,
  <year> is four-digit year, journal file is always in current working directory. The journal file
  is similar to a CSV file; valid journal file contents:
  
    # <comment line, ignored, line must start with #, leading spaces OK> <newline>       - Or -
    <blank line, ignored, only contains newline, spaces OK> <newline>                    - Or -
    <date>, <descr>, <amt>, <type>, <cat code>  - transaction line, fields sep. by comma and one or
        more spaces -
    <date> is m/d, m/dd, mm/d, or mm/dd - to minimize typing, use the shortest form, leading zeros 
        not required
    <descr> is mandatory description field, unquoted text, must not contain embedded commas
    <amt> is dollar amount: [optional negative sign]<at least one digit 0 to 9>.<exactly two digits
        00 to 99>
    <type> is an unquoted text string, a single word without spaces, not used by program
    <cat code> is a category code, the same definition as for the category file
    Note that no comments can appear at the end of a transaction line.

  Example journal file lines: (leading spaces OK)
  
    ###################################################
    # Union Checking Account
    ###################################################

    3/9, Rappahannock Electric (Union chk), 292.03, xfr, 2.2.1
    3/10, Sale of Delta power tools (Union chk), 1275.00, cash, 1.12
    3/10, Deposit most of sale proceeds (Union chk), 1000.00, dep, 3.2
    3/13, Interest (Union chk), 0.25, xfr, 1.2.1
    4/3, Anthem health insurance (Union chk), 277.82, xfr, 2.5.3
    4/6, Rappahannock Electric (Union chk), 319.65, xfr, 2.2.1
    4/12, U.S. Treasury income tax (Union chk #3057), 639.00, chk, 2.14.1

The program generates one output file in the current working directory with a name
YYYYMMDD_cashflow_report.txt where YYYYMMDD is the date the report was generated. If such an output
file already exists, the program asks you if it is OK to overwrite it ('No' quits the program).
    
The program reads and processes the category and journal files, and generates a report in the output
file consisting of detailed information followed by summary information. The detailed information 
lists all transactions from the journal file under their respective category code, "empty" category 
codes are also printed. For each category, the program computes and displays subtotal dollar amounts
for that category, as well as categories nested under that category. The summary information at the
end of the report reprints the category data, omitting "empty" categories and journal transactions.
The first category summary shows the year-to-date totals, then there is a separate category summary
for each month (for any month that has transactions in the journal file) showing the totals for that
month, followed by a final category summary that shows the average monthly totals. To compute the 
averages, the program divides the year-to-date category totals by the number of months that have
transactions in the journal file.

License:

The MIT License (MIT) - Copyright (c) 2015 John Santic
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and 
associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
 ubject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT 
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Author: John Santic, email johnsantic  <at>  g m a i l  <dot>  c o m

Toolset: Anaconda3 python version 3.4.3, standard library, no other packages, running on Windows 7.

Revision history:
    30-Sep-2015 - create original
"""

import sys
import datetime
from os import remove
from os.path import isfile, abspath
from enum import Enum
from calendar import isleap, month_name

# Define some default file names and directories for Windows, change them if it suits you.
DEFAULT_CONFIG_FILE = "cashflow_config.txt"
DEFAULT_JOURNAL_FILE = "_cashflow_journal.txt"  # YYYY prefix added later
DEFAULT_CAT_FILE = "cashflow_categories.txt"
DEFAULT_CAT_DIR = "C:\\Users\\John\\Documents\\financial\\"  # use your own folder names
DEFAULT_OUTPUT_FILE = "_cashflow_report.txt"  # YYYYMMDD prefix added later

# Global variables used by any function in the program.
cat_list = []  # list of hierarchical category code objects
cat_dict = {}  # translates category code from text string to cat_list index
journal_list = []  # list of transaction journal objects

# Classes created for the program.

class CatCode(object):
    """ Define a class for category code objects, which are stored in cat_list. Each CatCode object
    remembers the attributes of one category code. Some attributes come from the respective line
    in the cat code file, other attributes are dynamically created by the program.
    """
    # Instantiate new object, initialize attributes.
    def __init__(self, cat_code, descr, comment, level, line_num):
        self.cat_str = cat_code  # text string version of a category code (example: "3.2.6.10")
        self.descr = descr  # text string of description from file line
        self.comment = comment  # text string of comment, including the #
        self.level = level  # level 1 to 4 (example: "3" is level 1, "3.2.6.10" is level 4)
        self.line_nbr = line_num  # line where cat code was defined in cat code file
        self.parent = None  # int. idx in cat_list of parent category (not used by level 1 cat code)
        self.children = []  # integer indices in cat_list for all child categories
        self.total = 0.0  # dollar value for this cat when tallying journal transactions
        self.nested_total = 0.0 # dollar value for child categories under this cat code
        self.monthly = [0.0] * 12  # monthly dollar value totals
        self.nested_monthly = [0.0] * 12  # and for nested child categories
        self.journal = []  # integer indices in journal_list for all transactions in this category
        self.longest = 0  # len of longest journal descr string, to help in formatting printout
        return

class Journal(object):
    """ Define a class for transaction journal objects, which are stored in journal_list. Each 
    Journal object remembers the attributes of one journal transaction. Some attributes come from 
    the respective line in the journal file, other attributes are dynamically created by the program.
    """
    # Instantiate new object, initialize attributes.
    def __init__(self, date, descr, amt, type, cat_code, cat_idx, line_num):
        self.date = date  # text string of expanded date (example: "04/29/2015")
        self.descr = descr  # text string of description from file line
        self.amt = amt  # floating point dollar amount
        self.type = type  # text string of transaction type (example: "chk" or "cash")
        self.cat_code = cat_code  # text string version of category code (example: "3.2.6.10")
        self.cat_idx = cat_idx  # integer index of category code in cat_list
        self.line_nbr = line_num  # line where transaction was defined in journal file
        return

def do_startup_activity():
    """ Basic program startup activity - process command line options, set up files for accessing.

    Inputs: sys.argv[] - optional command line parameters
            DEFAULT_CONFIG_FILE - optional config file in cwd containing path where cat code file is
                located (note that I am showing the named constant, see above for the actual string)
                
    Returns: cat_file_name - confirmed path to category code file, can be anywhere
             journal_file_name - confirmed path to transaction journal file, always in cwd
             output_file_name - confirmed path to output file, always in cwd
             (All files are in closed state upon return/exit)
             working_year - integer value of current journal year (example: 2015)
    
    All errors are fatal. If any errors are detected, print error msg and exit from inside this 
    function. If function returns, we are good to go, at least to the next processing step.
    """
    # Read and process any command line parameters. If no parameters, use default values.
    working_year = datetime.date.today().year  # default four-digit journal year is current year

    # See if Config command, specified path is where to find cat file, config file is always in cwd.
    if (len(sys.argv) == 3) and (sys.argv[1] == "-c"):
        if not isfile(sys.argv[2]): # can we find the cat file the user specified?
            sys.exit("Error, can't find category file " + sys.argv[2])
        if isfile(DEFAULT_CONFIG_FILE):  # user's cat file path is good, config file in use?
            # Config file already exists, verify overwrite with user.
            config_file = open(DEFAULT_CONFIG_FILE, "rt")
            old_cat_file_path = config_file.readline().rstrip(" \n")
            config_file.close()
            response = input("Config file already exists\n" + 
                             "Was " + old_cat_file_path + "\n" +
                             "Change to " + sys.argv[2] + "? y/n: ")
            if (response != "y") and (response != "Y"):
                print("Old config file not changed")
                sys.exit(0)
        config_file = open(DEFAULT_CONFIG_FILE, "wt")  # save cat file path in config file
        config_file.write(sys.argv[2])
        config_file.close()
        print("Done")
        sys.exit(0)
            
    # See if Show command, display cat file path either from config file or default location.
    elif (len(sys.argv) == 2) and (sys.argv[1] == "-s"):
    
        if isfile(DEFAULT_CONFIG_FILE):
            config_file = open(DEFAULT_CONFIG_FILE, "rt")
            cat_file_path = config_file.readline().rstrip(" \n")  # get user-specified path
            config_file.close()
            note = " (from config file)"
        else:
            cat_file_path = DEFAULT_CAT_DIR + DEFAULT_CAT_FILE
            note = " (from default location)"
        print("Category file path: " + cat_file_path + note)
        sys.exit(0)
    
    # See if Help command, print module documentation string at top of this file.
    elif (len(sys.argv) == 2) and (sys.argv[1] == "-h"):
        print(__doc__)
        sys.exit(0)
        
    # See if user specified a transaction journal year, perhaps different from current year.
    if len(sys.argv) == 2:
        try:
            user_year = int(sys.argv[1])
        except ValueError:
            sys.exit("Error, invalid command line parameter, for help, enter cashflow -h")
        if (user_year >= 1500) and (user_year <= 3000):
            working_year = user_year
        else:
            sys.exit("Error, invalid transaction journal year: " + sys.argv[1] + ", " +
                     "must be four-digit year between 1500 and 3000")
                     
    # See if spurious command line parameters.
    if len(sys.argv) > 2:
        sys.exit("Error, invalid command line parameters, for help, enter cashflow -h")

    # We're done processing command line parameters, fall through.
    # If sys.argv[1] was None, which is valid, use default year already set at top of function.
    
    # Make sure category and journal files exist in their expected directories.
    cat_file_path = DEFAULT_CAT_DIR + DEFAULT_CAT_FILE
    if isfile(DEFAULT_CONFIG_FILE):
        config_file = open(DEFAULT_CONFIG_FILE, "rt")  # config file exists, get user-specified path
        cat_file_path = config_file.readline().rstrip(" \n")
        config_file.close()
    if not isfile(cat_file_path):
        sys.exit("Error, category file not found: " + cat_file_path)

    journal_file_path = str(working_year) + DEFAULT_JOURNAL_FILE
    if not isfile(journal_file_path):
        sys.exit("Error, journal file not found: " + journal_file_path)
        
    # See if output file already exists; if so, verify overwrite with user.
    # First, create output file name from today's date: yyyymmdd + default name
    oday = datetime.date.today()
    prefix = "%4d%02d%02d" % (oday.year, oday.month, oday.day)
    output_file_path = prefix + DEFAULT_OUTPUT_FILE  # always use cwd
    if isfile(output_file_path):
        response = input("Output file already exists: " + output_file_path + ", overwrite? y/n: ")
        if (response != "y") and (response != "Y"):
            print("Output file not changed")
            sys.exit(0)
        remove(output_file_path)    
    
    # Files all ready to go, return the names (and year) but leave all files closed.
    return (cat_file_path, journal_file_path, output_file_path, working_year)

# Define the states for the parsing of a category file line.
class CS(Enum):
    START       = 1  # very beginning of line, column 1
    LEVEL1      = 2  # got at least a digit 1 to 9
    LEVEL234A   = 3  # building a deeper category level, first digit
    LEVEL234B   = 4  # building a deeper category level, optional second digit
    START_DESCR = 5  # looking for start of mandatory description
    END_DESCR   = 6  # looking for end of description
    END_COMMENT = 7  # in a comment, looking for end

def parse_cat_file_line(cat_file_line):
    """ Parse a line from the category file: if not blank or comment, make sure all fields are valid.
    
    inputs: cat_file_line = text string from cat file, terminated by <newline>
    outputs: error_msg = text string of error message if error (ignore other returned values), or
                         None if no error, other returned values are valid
             cat_code = text string of valid category code (example: "3.6.12"), or
                        None if blank line or comment line (ignore other returned values)
             descr = text string of mandatory description field (example: 
                "rent payment (storage room)")
             comment = text string of optional comment (including the #), None if no comment
             level = integer 1 to 4, cat code level (example: "3.6.12" is level 3)
    """
    # Loop through entire line from cat file, character by character, parsing the fields according
    # to what the current parse state expects.  
    parse_state = CS.START
    
    for idx, char in enumerate(cat_file_line):

        # If column 1 of line, check for comment line, blank line, or start of valid cat code.
        if parse_state == CS.START:
            if char == " ":
                continue  # skip any leading spaces
            if char in "#\n":
                return None,None,None,None,None  # comment or blank line, we're done
            if char in "123456789":
                start_idx = idx  # remember where cat code starts
                level = 1
                parse_state = CS.LEVEL1
                continue
            return "Error, invalid category file format",None,None,None,None

        # If in a level 1 cat code, see if it goes to level 2, else get description.
        elif parse_state == CS.LEVEL1:
            if char == ".":
                level = 2
                parse_state = CS.LEVEL234A  # get more cat code characters
                continue
            if char == " ":
                cat_code = cat_file_line[start_idx:idx]  # cat code done
                parse_state = CS.START_DESCR
                continue
            return "Error, invalid category file format",None,None,None,None

        # If first (or only) char of higher-level cat code, must start with digit 1 to 9
        elif parse_state == CS.LEVEL234A:
            if char in "123456789":
                parse_state = CS.LEVEL234B  # see if there's a second digit
                digit_count = 1
                continue
            return "Error, invalid category file format",None,None,None,None

        # If higher-level cat code, see if there's a second digit 0 to 9
        elif parse_state == CS.LEVEL234B:
            if char.isdigit():
                digit_count += 1
                if digit_count <= 2:
                    continue  # stay in same state for now, accumulate digits
                return "Error, invalid category code, too many digits",None,None,None,None
            if char == ".":
                level += 1
                if level <= 4:
                    parse_state = CS.LEVEL234A  # continue building a higher-level cat code
                    continue
                return "Error, invalid category code, level nested too deeply",None,None,None,None
            if char == " ":
                cat_code = cat_file_line[start_idx:idx]  # cat code done, extract it from line
                parse_state = CS.START_DESCR
                continue
            return "Error, invalid category file format",None,None,None,None

        # If looking for description field, skip over leading spaces.
        elif parse_state == CS.START_DESCR:
            if char == " ":
                continue  # stay in same state, skip spaces
            if char in "#\n":
                return "Error, invalid category file format, missing description",None,None,None,None
            descr_start = idx  # found descr, remember where it started
            parse_state = CS.END_DESCR
            continue
            
        # If looking for end of description field, stop on end of line or comment.
        elif parse_state == CS.END_DESCR:
            if char in "#\n":
                descr = cat_file_line[descr_start:idx]  # end of description, extract it from line
                descr = descr.rstrip()  # strip trailing spaces
                if char == "\n":  # if newline, we're done, return good values
                    return None, cat_code, descr, "", level  # no error or comment
                comment_start = idx  # else, not done yet, get the comment
                parse_state = CS.END_COMMENT
            continue  # get more description characters
            
        # Last state, wait for end of comment, which is a newline.
        if char == "\n":
            comment = cat_file_line[comment_start:idx]  # extract comment from line
            comment = comment.rstrip()  # strip trailing spaces
            return None, cat_code, descr, comment, level  # all done with line, return values
        continue  # get more comment chars
    
    # If we drop out of the for...enumerate loop, the line didn't end well, error.
    if parse_state == CS.START:
       return None,None,None,None,None  # special OK case, last line of file = spaces w/o newline
    return "Error, invalid category file format",None,None,None,None

def read_and_parse_cat_file(cat_file_name):
    """ Open and read cat code file, process each line as req'd. Exit program if any error detected.
    
    Inputs: cat_file_name - verified path/name of file containing category codes
    Inputs/Outputs: global cat_list - list of all category code objects
                    global cat_dict - translates from cat code string to cat list index
    """
    global cat_list, cat_dict
    
    # Read through every line of category file until end of file.
    cat_file = open(cat_file_name, "rt")  # this should always work, we already know file exists
    idx = 0  # cat_list index
    for line_nbr, line in enumerate(cat_file, 1):  # start line number at 1 not 0

        # Run the parser state machine over the line to validate it and extract info.
        error_msg, cat_code, descr, comment, level = parse_cat_file_line(line)
        if error_msg:  # if parser detected an error, bail out
            print (error_msg + "\nLine number " + str(line_nbr) +
                " in category file " + cat_file_name)
            cat_file.close()
            sys.exit(1)
        
        # If this line has a real cat code (instead of just blank or comment), instantiate a cat code
        # object, save important category info, then put this cat code object in the cat list.
        # Only do this if cat code not in dictionary, otherwise this is a duplicate cat code, error.
        if cat_code:  # make sure this line has a cat code instead of blank or comment
            if cat_code in cat_dict:
                print("Error, duplicate category code found\nLine number " + 
                       str(line_nbr) + " in category file " + cat_file_name)
                cat_file.close()
                sys.exit(1)
            cat_dict[cat_code] = idx  # the dict translates from cat code string to cat_list index
            cat_obj = CatCode(cat_code, descr, comment, level, line_nbr)
            cat_list.append(cat_obj)
            idx += 1  # only inc idx for real cat codes
        # Get here if real cat code line, or if blank/comment line.

    # Drop out of loop if cat file completely processed, make sure we got something valid.
    cat_file.close()
    if len(cat_list) == 0:
        print("Error, empty category file " + cat_file_name)
        sys.exit(1)
    return
    
def prc_cat_file_hierarchy():
    """ After populating cat_list, scan through list to figure out parent/children for each cat code.

    Each category object in cat_list remembers the list index of its parent category. For example,
    category "3.2.12" remembers parent "3.2". Also, each parent in cat_list remembers all the list
    indices of its child categories. For example, "3.2" might remember "3.2.1", 3.2.2", "3.2.3", etc.
    But note that "3.2.3.6" is not a child of "3.2" but a child of "3.2.3". Note that the category
    file can't be in random order. A parent cat code must appear in the file before any children cat
    codes for that parent appear in the file. For example, category 3.4 must occur in the file before
    any 3.4.xx categories occur (where xx is 1 to 99).

    Inputs/Outputs: global cat_list - list of all category code objects
                    global cat_dict - translates from cat code string to cat list index
    """
    global cat_list, cat_dict

    for idx in range(len(cat_list)):
        if cat_list[idx].level > 1:  # level 1 cat codes don't have parent, skip them
            # This is for cat code levels 2, 3, 4. To figure out the parent, temporarily strip the 
            # last ".xx" off the cat code (where xx is 1 to 99). Save this parent cat code in the
            # current item. Then find the parent in the cat_list and update the parent's "children" 
            # attribute to include the current item. "Children" is a list, so a parent can have 
            # multiple children.
            full_code = cat_list[idx].cat_str  # get full cat code string
            pos = full_code.rfind(".")  # find last "."
            parent_code = full_code[0:pos]  # parent cat string = strip .xx from full cat code
            if parent_code not in cat_dict:  # oops, we have a child but there is no parent, error
                print ("Error, parent category " + parent_code + 
                       " missing or appears after child category " + full_code)
                sys.exit(1)
            parent_idx = cat_dict[parent_code]  # else, parent exists, get cat_list index
            cat_list[parent_idx].children.append(idx)  # append current item as another child
            cat_list[idx].parent = parent_idx  # save parent index in current item
    
    # Drop out of loop after processing entire category list and saving all parent/children indices.
    return
    
# Define the states for the parsing of a transaction journal file line.
class TJ(Enum):
    START       = 1  # very beginning of line, column 1
    MONTH       = 2  # accumulating month digits
    DATE        = 3  # accumulating date digits
    START_DESCR = 4  # looking for start of description field
    END_DESCR   = 5  # looking for end of description field
    START_AMT   = 6  # looking for start of amount field
    DOLLARS     = 7  # accumulating dollars digits
    CENTS       = 8  # accumulating cents digits
    START_TYPE  = 9  # looking for start of type field
    END_TYPE    = 10 # looking for end of type field
    START_CAT   = 11 # looking for start of cat code field
    END_CAT     = 12 # looking for end of cat code field

# Table giving maximum date for each month, month is 1 to 12, assumes 29 days for February.
# We use this below to check for valid date, we also check for leap year below if date is Feb. 29.
MAX_DATE = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def parse_journal_file_line(journal_file_line, journal_year):
    """ Parse a line from the journal file: if not blank or comment, make sure fields are valid.
    
    inputs: journal_file_line = text string from journal file, terminated by <newline>
            journal_year = integer value for year of this journal file, for example 2015
    outputs: jerror = text string error message if error (ignore other returned values), or
                      None if no error, other returned values are valid
         jdate = text string of expanded date, for example: "04/23/2015", or
                 None if blank line or comment line, ignore other returned values
         jdescr = text string of description field, for example: "GEICO car insurance (CapOne chk)"
                  The field is delimited by a comma, so descr can not contain embedded commas.
         jamt = dollar amount, floating point number, can be negative, for example: -12.38
                In the file, the dollar portion must have at least one digit, for example: "0.98"
         jtype = text string of transaction type, for example "chk" or "cash"
         jcat_code = text string of category code, for example "2.5.3", or
                     None if line is blank or comment. Caller must verify cat code is valid.
    """
    # Loop through entire line from journal file, character by character, parsing the fields 
    # according to what the current parse state expects.  
    parse_state = TJ.START
    
    for idx, char in enumerate(journal_file_line):

        # If column 1 of line, check for comment line, blank line, or start of month field.
        if parse_state == TJ.START:
            if char == " ":
                continue  # skip any leading spaces
            if char in "#\n":
                return None,None,None,None,None,None  # comment or blank line, we're done
            if char.isdigit():
                month_value = int(char)  # starting digit of a month, get integer value
                digit_ctr = 1
                parse_state = TJ.MONTH
                continue
            return "Error, invalid journal file format",None,None,None,None,None

        # If month in progress, accumulate valid digits.
        elif parse_state == TJ.MONTH:
            if char.isdigit():
                month_value = (month_value*10) + int(char)  # accumulate a month digit
                digit_ctr += 1
                if digit_ctr <= 2:
                    continue
                return "Error, invalid month in journal file",None,None,None,None,None
            if char == "/":
                if 1 <= month_value <= 12:  # got a month, is it valid?
                    digit_ctr = 0         # if so, prepare to get date digits
                    date_value = 0
                    parse_state = TJ.DATE
                    continue
            return "Error, invalid month in journal file",None,None,None,None,None
                
        # If date in progress, accumulate valid digits.
        elif parse_state == TJ.DATE:
            if char.isdigit():
                date_value = (date_value*10) + int(char)  # accumulate date digit
                digit_ctr += 1
                if digit_ctr <= 2:
                    continue
                return "Error, invalid date in journal file",None,None,None,None,None
            if char == ",":  # comma terminates month/date field
                if 1 <= date_value <= MAX_DATE[month_value]:  # is date valid for month?
                    if (month_value == 2) and (date_value == 29):  # yes, but check for leap year
                        if not isleap(journal_year):  # if not a leap year, error
                            return "Error, invalid leap year date in journal file", \
                                None,None,None,None,None
                    # Come here if month/date valid. Expand to a full MM/DD/YYYY quoted string.
                    jdate = "{0:02d}/{1:02d}/{2:04d}".format(month_value, date_value, journal_year)
                    parse_state = TJ.START_DESCR
                    continue
            return "Error, invalid date in journal file",None,None,None,None,None
                    
        # If waiting for description field, skip leading spaces.
        elif parse_state == TJ.START_DESCR:
            if char == " ":
                continue  # skip any leading spaces
            if char not in ",\n":
                descr_start = idx  # remember where descr field starts
                parse_state = TJ.END_DESCR  # get remainder of descr field
                continue
            return "Error, invalid description in journal file",None,None,None,None,None
        
        # If waiting for end of description field, look for comma delimiter.
        elif parse_state == TJ.END_DESCR:
            if char == ",":
                jdescr = journal_file_line[descr_start:idx]  # end of descr, extract it from line
                jdescr = jdescr.rstrip()  # strip trailing spaces
                sign_flag = False
                parse_state = TJ.START_AMT  # look for start of amount field
            continue

        # If waiting for amount field, skip leading spaces.
        elif parse_state == TJ.START_AMT:
            if char == " ":
                continue  # skip any leading spaces
            if char == "-":  # if negative sign, remember we got one
                sign_flag = True
                digit_ctr = 0
                dollars = 0.0
                parse_state = TJ.DOLLARS
                continue
            if char.isdigit():  # dollar field must have at least one digit
                digit_ctr = 1
                dollars = float(char)
                parse_state = TJ.DOLLARS
                continue
            return "Error, invalid amount in journal file",None,None,None,None,None
                
        # If processing dollar portion of amount, accumulate digits.
        elif parse_state == TJ.DOLLARS:
            if char.isdigit():
                digit_ctr += 1
                dollars = (dollars*10.0) + float(char)
                continue
            if char == ".":  # if end of dollars
                if digit_ctr != 0:  # must have been at least one dollar digit, even if just "0.xx"
                    digit_ctr = 0  # now look for exactly two cents digits
                    cents = 0.0
                    parse_state = TJ.CENTS
                    continue
            return "Error, invalid amount in journal file",None,None,None,None,None
        
        # If processing cents portion of amount, accumulate exactly two digits.
        elif parse_state == TJ.CENTS:
            if char.isdigit():
                digit_ctr += 1
                cents = (cents*10.0) + float(char)
                continue
            if char == ",":  # end of cents, make sure we got exactly two digits
                if digit_ctr == 2:
                    jamt = dollars + (cents/100.0)
                    if sign_flag: jamt = -jamt
                    parse_state = TJ.START_TYPE  # now look for start of type field
                    continue
            return "Error, invalid amount in journal file",None,None,None,None,None
                    
        # If waiting for transaction type field, skip leading spaces.
        elif parse_state == TJ.START_TYPE:
            if char == " ":
                continue  # skip any leading spaces
            if char not in ",\n":
                type_start = idx  # remember where type field starts
                parse_state = TJ.END_TYPE  # get remainder of type field
                continue
            return "Error, invalid transaction type in journal file",None,None,None,None,None
        
        # If waiting for end of type field, look for comma delimiter
        elif parse_state == TJ.END_TYPE:
            if char == ",":
                jtype = journal_file_line[type_start:idx]  # end of type, extract it from line
                jtype = jtype.rstrip()  # strip trailing spaces
                parse_state = TJ.START_CAT  # look for start of cat code field
            continue

        # If waiting for category code field, skip leading spaces.
        elif parse_state == TJ.START_CAT:
            if char == " ":
                continue
            if char.isdigit():  # cat code must start with digit
                cat_start = idx  # remember where cat code starts
                parse_state = TJ.END_CAT  # get remainder of cat code
                continue
            return "Error, invalid category code in journal file",None,None,None,None,None

        # Last state, waiting for end of cat code. In this function, we are very liberal as to what
        # constitutes a cat code: any combination of digits and periods. The caller is responsible 
        # for validating the cat code, by making sure the string version is in cat_dict.
        if char.isdigit() or (char == "."):  # accumulate valid chars of cat code
            continue
        if char in " \n":  # if end of cat code
            jcat_code = journal_file_line[cat_start:idx]  # end of cat code, extract it from line

            # We have parsed a full valid journal transaction line, return fields to caller.
            return (None, jdate, jdescr, jamt, jtype, jcat_code)
            
        return "Error, invalid category code in journal file",None,None,None,None,None
    
    # If we drop out of the for...enumerate loop, the line didn't end well, error.
    if parse_state == TJ.START:
        return None,None,None,None,None,None  # it's OK if last line of file = spaces w/o newline
    return "Error, invalid journal file format",None,None,None,None,None

def read_and_parse_journal_file(journal_file_name, journal_year):
    """ Open and read journal file, process each line as req'd. Exit program if any error detected.
    
    Inputs: journal_file_name - verified path/name of journal file containing transactions
            journal_year - integer value of current journal year (example 2015)
    Inputs/Outputs: global cat_list - list of all category code objects
                    global cat_dict - translates from cat code string to cat list index
                    global journal_list - list of all transaction journal objects
    """
    global cat_list, cat_dict, journal_list
    
    # Read through every line of transaction journal file until end of file.
    journal_file = open(journal_file_name, "rt")  # should always work, we already know file exists
    idx = 0  # journal_list index
    for line_nbr, line in enumerate(journal_file, 1):  # start line number at 1 not 0

        # Run the parser state machine over the line to validate it and extract info.
        error_msg, date, descr, amt, type, cat_code = parse_journal_file_line(line, journal_year)
        if error_msg:  # if parser detected an error, bail out
            print (error_msg + "\nLine number " + str(line_nbr) + " in journal file " 
                + journal_file_name)
            journal_file.close()
            sys.exit(1)
        
        # If this line has a real journal transaction (instead of just blank or comment), instantiate
        # a journal object, save important info about journal transaction, then put this journal 
        # object in the journal list. Only do this if cat code is in dictionary, otherwise this is an
        # undefined cat code, error.
        if cat_code:  # make sure this line has a cat code instead of blank or comment
            if cat_code not in cat_dict:
                print("Error, undefined category code found\nLine number " + 
                       str(line_nbr) + " in journal file " + journal_file_name)
                journal_file.close()
                sys.exit(1)
            cat_idx = cat_dict[cat_code]
            journal_obj = Journal(date, descr, amt, type, cat_code, cat_idx, line_nbr)
            journal_list.append(journal_obj)
            
            # This journal transaction belongs to a particular cat code in cat_list, so append it to
            # the proper cat code object in the list. A cat code object can own many transactions.
            cat_list[cat_idx].journal.append(idx)  # save the index into journal_list
            cat_list[cat_idx].total += amt  # also update dollar value for that cat code

            # Keep track of monthly subtotals for later detailed printout.
            mon_idx = int(journal_obj.date[:2]) - 1  # convert from month 01 - 12 to index 0 - 11
            cat_list[cat_idx].monthly[mon_idx] += amt  # update monthly dollar value

            # Later when we generate the report file, it will make formatting easier if we remember
            # the longest transaction description for every cat code.
            if len(descr) > cat_list[cat_idx].longest:
                cat_list[cat_idx].longest = len(descr)

            idx += 1  # only inc idx for real transactions
            
        # Get here if real transaction line, or if blank/comment line.

    # Drop out of loop if journal file completely processed, make sure we got something valid.
    journal_file.close()
    if len(journal_list) == 0:
        print("Error, empty journal file " + journal_file_name)
        sys.exit(1)
    return

def generate_cashflow_report (cat_file_name, journal_file_name, output_file_name):
    """ Generate cashflow report to output file, first the details then the various summaries.
    
    Inputs: cat_file_name - verified path/name of file containing category codes
            journal_file_name - verified path/name of journal file containing transactions
            output_file_name - verified path/name of file to contain the report
    Inputs/Outputs: global cat_list - list of all category code objects
                    global cat_dict - translates from cat code string to cat list index
                    global journal_list - list of all journal objects
    """
    global cat_list, cat_dict, journal_list
    
    outfile = open(output_file_name, "wt")  # should always work, path/name already verified
    
    now = datetime.datetime.now()  # get current date and time, then format it specially
    now_str = "{0:02d}/{1:02d}/{2:4d}, {3:02d}:{4:02d},".format(now.month, now.day, now.year, 
                                                               now.hour, now.minute)
    print ("Cashflow program detailed output - Journal transactions for each category code",
           file=outfile)
    print ("\nReport generated on", now_str, "using files:", file=outfile)
    print ("   Category:", abspath(cat_file_name), file=outfile)
    print ("   Journal: ", abspath(journal_file_name), file=outfile)
    print ("   Report:  ", abspath(output_file_name), file=outfile)
    
    # For all cat codes that have transactions, we already know the category subtotals. But before 
    # we print anything out, we have to scan through the children of each category (those categories
    # that have children), and add the child totals to the parent totals. We need to do this "inside
    # out", from the deepest level cat codes working our way to the highest level cat codes, to make
    # sure that the child totals get added into to the parent totals hierarchically. For example, we
    # can't add the "2.1" subtotals to the "2" grand total until we add the "2.1.1" subtotals to the
    # "2.1" subtotals, but we can't even do that until we add the "2.1.1.1" subtotals to the "2.1.1"
    # subtotals. So for all level 4 categories, add their subtotals to their parent category (which 
    # will be a level 3 category). Then for all level 3 categories, add their subtotals to their
    # parent category (which will be level 2). Then for all level 2, add to level 1 parent. Level 1 
    # cats don't have a parent, so we don't need to check level 1 cat codes.
    for lvl in range(4,1,-1):  # do for level = 4,3,2, reverse order to be "inside out"
        for cidx in range(len(cat_list)):  # scan through entire cat_list for items of desired level
            if cat_list[cidx].level == lvl:
                pidx = cat_list[cidx].parent
                cat_list[pidx].nested_total += (cat_list[cidx].total + cat_list[cidx].nested_total)
                
                # After updating main dollar value (which is year-to-date), update the separate
                # monthly dollar values, all 12 of them, for this parent/child pair.
                for mon_idx in range(12):
                    cat_list[pidx].nested_monthly[mon_idx] +=  \
                        cat_list[cidx].monthly[mon_idx] + cat_list[cidx].nested_monthly[mon_idx]
    
    # Generate the detailed portion of the report: all transactions for all categories.
    for cidx in range(len(cat_list)):
        print("\nCategory", cat_list[cidx].cat_str, cat_list[cidx].descr, 
            "   Transactions:", "${0:.2f},".format(cat_list[cidx].total),
            " Nested:", "${0:.2f},".format(cat_list[cidx].nested_total),
            " Total:", "${0:.2f}".format(cat_list[cidx].total + cat_list[cidx].nested_total), 
            file=outfile)
        if len(cat_list[cidx].journal) > 0:  # any transactions for this cat code?
            print(file=outfile)  # print extra blank line if so
            
        # Before we print all the transactions for this category, sort them in place based on date.
        cat_list[cidx].journal.sort(key = lambda obj: journal_list[obj].date)
        # Get the max width of any transaction description, used for nicer formatting.
        max_width = cat_list[cidx].longest
        # cjidx = each journal[] item in turn, jidx = this one
        for cjidx in range(len(cat_list[cidx].journal)):
            jidx = cat_list[cidx].journal[cjidx]
            jobj = journal_list[jidx]  # cat_list only has jrnl index, get the journal object itself
            print("   ", jobj.date, "{0:.<{1}s}".format(jobj.descr, max_width),
                "${0:>8.2f}".format(jobj.amt), jobj.type, file=outfile)
    # All transactions for all categories printed.
    # Now print the year-to-date summary version, categories only, omit those that are all zero.
    print("\n#################################################"
          "###########################################", file=outfile)
    print("\nCashflow program year-to-date summary output - "  \
          "Categories only (omit all-zero categories)\n",
          "                                                          "
          "Transactions   Nested     Total", file=outfile)
    for cidx in range(len(cat_list)):  # scan through cat_list
        if (cat_list[cidx].total + cat_list[cidx].nested_total) != 0:  # if from trans or nested
            print("Category", "{0:.<10s}".format(cat_list[cidx].cat_str),
                "{0:.<40s}".format(cat_list[cidx].descr),
                "{0:>9.2f} ".format(cat_list[cidx].total),
                "{0:>9.2f} ".format(cat_list[cidx].nested_total),
                "{0:>9.2f}".format(cat_list[cidx].total + cat_list[cidx].nested_total), file=outfile)
                
    # After year-to-date summary, print monthly summaries. First, figure out which months we have to
    # print, omit months with no transactions (like those in the future).
    todo = [False] * 12  # which months we have to print
    for cidx in range(len(cat_list)):  # scan all categories
        for month in range(12):  # for all 12 months in each category
            if cat_list[cidx].monthly[month] + cat_list[cidx].nested_monthly[month] != 0:
                todo[month] = True  # if activity in that month, we have to print that month

    # Now print a monthly summary for all months with activity, omitting all-zero categories.
    for month in range(12):
        if todo[month]:
            print("\n#################################################"
                  "###########################################", file=outfile)
            print("\nCashflow program summary output for", month_name[month+1], "\n",
                  "                                                          "
                  "Transactions   Nested     Total", file=outfile)
            for cidx in range(len(cat_list)):  # scan through cat_list
                if (cat_list[cidx].monthly[month] + cat_list[cidx].nested_monthly[month]) != 0:
                    print("Category", "{0:.<10s}".format(cat_list[cidx].cat_str),
                        "{0:.<40s}".format(cat_list[cidx].descr),
                        "{0:>9.2f} ".format(cat_list[cidx].monthly[month]),
                        "{0:>9.2f} ".format(cat_list[cidx].nested_monthly[month]),
                    "{0:>9.2f}".format(cat_list[cidx].monthly[month] + \
                        cat_list[cidx].nested_monthly[month]), file=outfile)
            # end for each cat_list item
        # end if month has activity
    # end for each month

    # Finally, print a monthly average dollar amount for all non-zero categories. The divisor is
    # however many months of activity we have accrued, may be less than 12 if year isn't over.
    months = sum(todo)  # how many months of activity
    print("\n#################################################"
          "###########################################", file=outfile)
    print("\nCashflow program summary output, monthly average for", months, "months\n",
          "                                                          "
          "     Total    Average", file=outfile)
    for cidx in range(len(cat_list)):  # scan through cat_list
        if (cat_list[cidx].total + cat_list[cidx].nested_total) != 0:  # if from trans or nested
            print("Category", "{0:.<10s}".format(cat_list[cidx].cat_str),
                "{0:.<40s}".format(cat_list[cidx].descr),
                "{0:>9.2f}".format(cat_list[cidx].total + cat_list[cidx].nested_total),
                "{0:>9.2f}".format((cat_list[cidx].total + cat_list[cidx].nested_total) / months),
                    file=outfile)
         
    outfile.close()
    return
    
def main():
    """ Main processing for cashflow program, this is where all the work is initiated. """
    
    # Process command line parameters (if any), make sure all necessary files exist,
    # obtain valid file names if so.
    cat_file_name, journal_file_name, output_file_name, journal_year = do_startup_activity()

    # Read, parse, and process category file. All errors are fatal, the called routine
    # prints a message and exits.
    read_and_parse_cat_file(cat_file_name)
    prc_cat_file_hierarchy()

    # Read and parse transaction journal file. All errors are fatal, the called routine
    # prints a message and exits.
    read_and_parse_journal_file(journal_file_name, journal_year)
    
    # Generate cashflow report to output file.
    generate_cashflow_report(cat_file_name, journal_file_name, output_file_name)
    
    return # from main

# This program is not a library so you would not normally import it into another module. You usually
# run the program by itself on the python command line, for example: "python cashflow.py". Therefore,
# the module name will normally be __main__ so the lines below are what actually run the program.
if __name__ == '__main__':
    main()
# Once main() returns, drop out of the bottom and the program is done. 
