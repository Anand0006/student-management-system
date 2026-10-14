****************************************************************
STUDENT MANAGEMENT SYSTEM  README
****************************************************************

OVERVIEW
~~~~~~~~
This is a Streamlit web application for managing student records.
It supports adding, viewing, searching, updating and deleting
students, and shows a dashboard with department wise performance.

All data is stored in a single CSV file (student_dataset.csv), which
acts as the database. Every change is written back to this file
immediately.

Technologies used:
  * Python
  * pandas (data handling and CSV reading and writing)
  * Streamlit (web user interface)

How to run:
  1. Install dependencies:  pip install pandas streamlit
  2. Run the app:           streamlit run your_file_name.py
  3. Keep student_dataset.csv in the same folder as the script.
     If the file does not exist, an empty table is used and the CSV
     is created when you add the first record.


GLOBAL CONSTANTS
~~~~~~~~~~~~~~~~
DATA_FILE : "student_dataset.csv"
    Name of the CSV file used as the database.

COLUMNS : Roll_No, Name, Gender, Marks, City, Department, Course
    The column structure of the CSV. Used to create an empty table
    if the CSV file is missing.

GENDERS : Male, Female, Other
    The allowed options shown in the Gender dropdown.


HELPER FUNCTION
~~~~~~~~~~~~~~~
centered(df)
    Purpose : Makes tables look neat.
    Input   : a pandas DataFrame.
    Output  : a styled DataFrame in which all headers and cell
              values are center aligned.
    Used by : Dashboard, View and Search, and Delete pages.


****************************************************************
CLASS 1: Student
****************************************************************

PURPOSE
~~~~~~~
Represents ONE student record as a Python object. It holds the data
for a single student, cleans it, validates it, and converts it to
and from the dictionary and row format used by pandas.

Think of it as the "model": it describes what a student is.

DATA (ATTRIBUTES)
~~~~~~~~~~~~~~~~~
  roll_no     Student's unique roll number (stored as text, trimmed)
  name        Student's full name (text, trimmed)
  gender      Male, Female or Other
  marks       Marks obtained (converted to an integer)
  city        City the student belongs to (text, trimmed)
  department  Department name (text, trimmed)
  course      Course name (text, trimmed)

METHODS
~~~~~~~
__init__(roll_no, name, gender, marks, city, department, course)
    Constructor. Creates a student object. It converts values to
    the right type (text or integer) and strips extra spaces so the
    data is stored cleanly.

validate()
    Checks the student's data before it is saved.
    Rules:
      * Roll number and name must not be empty.
      * Marks must be between 0 and 100.
    Raises a ValueError with a clear message if a rule is broken.

to_dict()
    Converts the student object into a dictionary whose keys match
    the CSV column names. Used when adding a row to the DataFrame
    or updating an existing row.

from_row(row)   [class method]
    Does the reverse of to_dict(). Takes one row of the DataFrame
    and builds a Student object from it. Used when a record is
    loaded for editing on the Update page.


****************************************************************
CLASS 2: StudentRepository
****************************************************************

PURPOSE
~~~~~~~
Handles ALL storage work. It reads the CSV file, keeps the data in
memory as a pandas DataFrame, performs add, update, delete and
search operations, and saves the changes back to the CSV.

The rest of the app never touches the CSV directly. It only talks
to this class. This keeps data logic separate from the user
interface (the "repository" pattern).

DATA (ATTRIBUTES)
~~~~~~~~~~~~~~~~~
  path   Path of the CSV file (default: student_dataset.csv)
  df     pandas DataFrame holding all student records in memory.
         Loaded from the CSV when the object is created. If the
         file is not found, an empty DataFrame with the standard
         columns is created instead. Roll_No is read as text so
         values like "001" keep their leading zeros.

METHODS
~~~~~~~
__init__(path)
    Loads the CSV into self.df, or creates an empty table if the
    file does not exist.

_commit()
    Private helper. Writes the current DataFrame back to the CSV
    file. Called after every add, update and delete so the file is
    always up to date.

exists(roll_no)
    Returns True if a student with this roll number is already in
    the data, otherwise False. Used to prevent duplicates and to
    check that a record exists before updating or deleting.

get(roll_no)
    Finds a student by roll number and returns a Student object.
    Returns None if not found.

add(student)
    Adds a new student.
      1. Validates the student data.
      2. Rejects it if the roll number already exists.
      3. Appends the new row to the DataFrame.
      4. Saves to the CSV.

update(roll_no, student)
    Updates an existing student.
      1. Validates the new data.
      2. Raises an error if the roll number is not found.
      3. Overwrites that row's values.
      4. Saves to the CSV.

delete(roll_no)
    Removes a student.
      1. Raises an error if the roll number is not found.
      2. Drops that row and resets the index.
      3. Saves to the CSV.

search(keyword)
    Case insensitive search across Roll_No, Name, City, Department
    and Course. Returns all matching rows. If the keyword is empty,
    returns all records.

department_summary()
    Groups students by department and calculates, for each one:
    number of students, average marks, highest marks and lowest
    marks (rounded to 2 decimals). Used by the Dashboard.


****************************************************************
PAGE FUNCTIONS (USER INTERFACE)
****************************************************************
These are plain functions, not classes. Each one draws one screen
of the app and receives the repository object (repo).

page_dashboard(repo)
    Shows summary metrics (total students, average marks, highest
    marks), a department wise performance table and a bar chart of
    average marks per department.

page_view(repo)
    Shows all students in a table with a search box. Displays how
    many records were found.

page_add(repo)
    Form to enter a new student's details. On submit, it creates a
    Student object and calls repo.add(). Shows a success or error
    message. The form clears itself after submission.

page_update(repo)
    Lets the user pick a student from a dropdown (roll number and
    name), fills a form with the current details and saves changes
    through repo.update(). The roll number cannot be changed.

page_delete(repo)
    Lets the user pick a student, shows the record, and requires a
    confirmation checkbox before the Delete button is enabled. Then
    calls repo.delete().

main()
    Entry point of the app. Sets the page title and layout, creates
    the StudentRepository (the CSV is reloaded on every
    interaction), builds the sidebar menu, shows the record count,
    and calls the page function chosen by the user.


****************************************************************
HOW THE PARTS WORK TOGETHER
****************************************************************

   User (browser)
        |
        v
   Page functions (Streamlit UI: forms, tables, buttons)
        |
        v
   Student  <~~~~~~>  StudentRepository
   (one record:        (all records:
    clean, validate,    load, add, update,
    convert)            delete, search, summary)
                             |
                             v
                    student_dataset.csv (the database)

Example flow, adding a student:
  1. User fills the form on the Add Student page.
  2. page_add() creates a Student object from the inputs.
  3. repo.add() calls student.validate().
  4. If valid and the roll number is new, the row is added to the
     DataFrame and saved to the CSV.
  5. A success (or error) message is shown to the user.


****************************************************************
CSV FILE FORMAT
****************************************************************
Header row (required):
  Roll_No,Name,Gender,Marks,City,Department,Course

Example row:
  101,Aarav Sharma,Male,85,Noida,Computer Science,B.Tech

****************************************************************
