import os
import re
import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem
from SSISFINAL import Ui_MainWindow

DB_FILE = 'system.db'

class StudentSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Information System")
        
        self.conn = sqlite3.connect(DB_FILE)
        self.create_tables()
        
       

        self.Program_Code = set()
        self.College_Code = set()
        self.ProgramCollegeMap = {}

        # Connect buttons
        self.ui.AddSt.clicked.connect(self.AddStudent)
        self.ui.AddCo.clicked.connect(self.AddCollege)
        self.ui.AddProg.clicked.connect(self.AddProgram)
        self.ui.EditSt.clicked.connect(self.EditStudent)
        self.ui.EditSt_2.clicked.connect(self.EditCollege)
        self.ui.EditSt_3.clicked.connect(self.EditProgram)
        self.ui.SEARCHbutton.clicked.connect(self.SearchStudent)
        self.ui.Searchbutton.clicked.connect(self.SearchCollege)
        self.ui.Searchbutton_2.clicked.connect(self.SearchProgram)
        self.ui.DeleteSt.clicked.connect(self.DeleteStudent)
        self.ui.DeleteSt_2.clicked.connect(self.DeleteCollege)
        self.ui.DeleteSt_3.clicked.connect(self.DeleteProgram)
        self.ui.SREFRESH.clicked.connect(self.StudentRefresh)
        self.ui.CREFRESH.clicked.connect(self.CollegeRefresh)
        self.ui.REFRESH.clicked.connect(self.ProgramRefresh)


        self.ui.Sortbybox.currentIndexChanged.connect(self.FilterStudents)
        self.ui.Searchbybox.textChanged.connect(self.FilterStudents)
        self.ui.Sortbox.currentIndexChanged.connect(self.FilterColleges)
        self.ui.Searchbox.textChanged.connect(self.FilterColleges)
        self.ui.Sortbybox_2.currentIndexChanged.connect(self.FilterPrograms)
        self.ui.Searchbybox_2.textChanged.connect(self.FilterPrograms)

        self.combo_boxes()
        #Pagination Variables
        self.current_student_page = 0
        self.students_per_page = 30  

        self.current_college_page = 0
        self.colleges_per_page = 30

        self.current_program_page = 0
        self.programs_per_page = 30
        
        self.LoadStudent()
        self.LoadCollege()
        self.LoadProgram()
        self.setup_pagination_buttons()

        self.ui.tabWidget.setCurrentIndex(0)


    def create_tables(self):
        cursor = self.conn.cursor()

        # Enable foreign key support
        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS colleges (
                code TEXT PRIMARY KEY,
                name TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS programs (
                code TEXT PRIMARY KEY,
                name TEXT,
                college_code TEXT,
                FOREIGN KEY (college_code) REFERENCES colleges(code) 
                ON DELETE SET NULL ON UPDATE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                year_level TEXT,
                gender TEXT,
                program_code TEXT,
                FOREIGN KEY (program_code) REFERENCES programs(code)
                ON DELETE SET NULL ON UPDATE CASCADE
            )
        """)
        self.conn.commit()


    def combo_boxes(self):
        self.ui.Yrlvlbox.clear()
        self.ui.genderbox.clear()
        self.ui.Yrlvlbox.addItems(["Please Select", "1st", "2nd", "3rd", "4th"])
        self.ui.genderbox.addItems(["Please Select", "M", "F", "Other"])
        self.ui.Yrlvlbox.setCurrentIndex(0)
        self.ui.genderbox.setCurrentIndex(0)

        self.ui.prcComboBox.clear()
        self.ui.prcComboBox.addItem("Please Select")
        self.ui.prcComboBox.addItems(sorted(self.Program_Code))
        self.ui.prcComboBox.setCurrentIndex(0)

        self.ui.ccComboBox.clear()
        self.ui.ccComboBox.addItem("Please Select")
        self.ui.ccComboBox.addItems(sorted(self.College_Code))
        self.ui.ccComboBox.setCurrentIndex(0)
    
 
    
    #Pagination Buttons
    def setup_pagination_buttons(self):
        self.ui.NextStudentButton.clicked.connect(self.NextStudentPage)
        self.ui.PrevStudentButton.clicked.connect(self.PrevStudentPage)

        self.ui.NextCollegeButton.clicked.connect(self.NextCollegePage)
        self.ui.PrevCollegeButton.clicked.connect(self.PrevCollegePage)

        self.ui.NextProgramButton.clicked.connect(self.NextProgramPage)
        self.ui.PrevProgramButton.clicked.connect(self.PrevProgramPage)
    
    

        self.conn.commit()



    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# STUDENT METHODS

    def AddStudent(self):
        id = self.ui.IDnoBox.text().strip()
        fname = self.ui.FristNbox.text().strip()
        lname = self.ui.LastNbox.text().strip()
        yearlevel = self.ui.Yrlvlbox.currentText().strip()
        gender = self.ui.genderbox.currentText().strip()
        code = self.ui.prcComboBox.currentText().strip()

        if not id or not fname or not lname or not code or yearlevel == "Please Select" or gender == "Please Select":
            QMessageBox.warning(self, "Input Error", "All fields must be filled.")
            return

        if not self.studentidformat(id):
            QMessageBox.warning(self, "Input Error", "Invalid Student ID format. Must be YYYY-NNNN.")
            return

        if not self.studentnameformat(fname) or not self.studentnameformat(lname):
            QMessageBox.warning(self, "Input Error", "Names must contain only letters and spaces.")
            return

        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO students (id, first_name, last_name, year_level, gender, program_code) VALUES (?, ?, ?, ?, ?, ?)",
                           (id, fname, lname, yearlevel, gender, code))
            self.conn.commit()
            QMessageBox.information(self, "Success", "Student added successfully.")
            self.LoadStudent()
            self.ClearStudentInputs()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate Error", "Student ID already exists.")

    def LoadStudent(self):
        self.ui.StudentTable.setSortingEnabled(False)
        self.ui.StudentTable.setRowCount(0)
        cursor = self.conn.cursor()
        
        # Get all students first
        cursor.execute("SELECT * FROM students")
        all_students = cursor.fetchall()
        
        # Calculate total students count
        total_students = len(all_students)
        
        # Valid Pagination
        max_page = (total_students - 1) // self.students_per_page if total_students > 0 else 0
        if self.current_student_page > max_page:
            self.current_student_page = max_page
        if self.current_student_page < 0:
            self.current_student_page = 0
        
        # Calculate start and end indices for current page
        start = self.current_student_page * self.students_per_page
        end = start + self.students_per_page
        
        # Get only the students for the current page
        current_page_students = all_students[start:end]
        
        # Populate the table with current page students
        for row_index, row_data in enumerate(current_page_students):
            self.ui.StudentTable.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.StudentTable.setItem(row_index, col_index, QTableWidgetItem(str(data)))
        
        self.ui.StudentTable.setSortingEnabled(True)
        self.ui.StudentTable.horizontalHeader().setSortIndicator(-1, 0)
    
    def NextStudentPage(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]

        if (self.current_student_page + 1) * self.students_per_page < total_students:
            self.current_student_page += 1
            self.LoadStudent()
    
    def PrevStudentPage(self):
        if self.current_student_page > 0:
            self.current_student_page -= 1
            self.LoadStudent()
    
    def EditStudent(self):
        selectedrow = self.ui.StudentTable.currentRow()
        if selectedrow < 0:
            QMessageBox.warning(self, "Error", "Please select a student to edit.")
            return
        
        reply = QMessageBox.information(self, "Edit Student", 
                                        "You can edit the student details and click 'Update Student' to save changes.",
                                        QMessageBox.Ok | QMessageBox.No) 
        if reply == QMessageBox.No:
            return
                
        

        student_id = self.ui.StudentTable.item(selectedrow, 0).text()

        # Load values into input boxes
        self.ui.IDnoBox.setText(student_id)
        self.ui.FristNbox.setText(self.ui.StudentTable.item(selectedrow, 1).text())
        self.ui.LastNbox.setText(self.ui.StudentTable.item(selectedrow, 2).text())
        self.ui.Yrlvlbox.setCurrentText(self.ui.StudentTable.item(selectedrow, 3).text())
        self.ui.genderbox.setCurrentText(self.ui.StudentTable.item(selectedrow, 4).text())
        self.ui.prcComboBox.setCurrentText(self.ui.StudentTable.item(selectedrow, 5).text())
        
        # Set a flag or store the original ID for proper update
        self.editing_student_id = student_id
        
        # Change the Add button text to indicate edit mode
        self.ui.AddSt.setText("Update")
        
        # Temporarily disconnect and reconnect with different function
        self.ui.AddSt.clicked.disconnect()
        self.ui.AddSt.clicked.connect(self.UpdateStudent)

    def UpdateStudent(self):
        # This function handles the update operation after Edit button was pressed
        id = self.ui.IDnoBox.text().strip()
        fname = self.ui.FristNbox.text().strip()
        lname = self.ui.LastNbox.text().strip()
        yearlevel = self.ui.Yrlvlbox.currentText().strip()
        gender = self.ui.genderbox.currentText().strip()
        code = self.ui.prcComboBox.currentText().strip()

        if not id or not fname or not lname or code == "Please Select" or yearlevel == "Please Select" or gender == "Please Select":
            QMessageBox.warning(self, "Input Error", "All fields must be filled.")
            return

        if not self.studentidformat(id):
            QMessageBox.warning(self, "Input Error", "Invalid Student ID format. Must be YYYY-NNNN.")
            return

        if not self.studentnameformat(fname) or not self.studentnameformat(lname):
            QMessageBox.warning(self, "Input Error", "Names must contain only letters and spaces.")
            return

        cursor = self.conn.cursor()
        try:
            # If the ID hasn't changed, just update the record
            if id == self.editing_student_id:
                cursor.execute("""
                    UPDATE students 
                    SET first_name=?, last_name=?, year_level=?, gender=?, program_code=?
                    WHERE id=?
                """, (fname, lname, yearlevel, gender, code, id))
            else:
                # If ID has changed, delete old record and insert new one
                cursor.execute("DELETE FROM students WHERE id=?", (self.editing_student_id,))
                cursor.execute("""
                    INSERT INTO students (id, first_name, last_name, year_level, gender, program_code)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id, fname, lname, yearlevel, gender, code))
                
            self.conn.commit()
            QMessageBox.information(self, "Success", "Student updated successfully.")
            
            # Reset the edit mode
            self.ui.AddSt.setText("Add Student")
            self.ui.AddSt.clicked.disconnect()
            self.ui.AddSt.clicked.connect(self.AddStudent)
            self.editing_student_id = None
            
            self.LoadStudent()
            self.ClearStudentInputs()
        except sqlite3.IntegrityError as e:
            QMessageBox.warning(self, "Database Error", f"Error updating student: {str(e)}")


    def DeleteStudent(self):
        selectedrow = self.ui.StudentTable.currentRow()
        if selectedrow < 0:
            QMessageBox.warning(self, "Error", "Please select a student to delete.")
            return
        
        student_id = self.ui.StudentTable.item(selectedrow, 0).text()

        reply = QMessageBox.question(self, "Confirm Deletion", 
                                  "Are you sure you want to delete this student?", 
                                  QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return

        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
            self.conn.commit()
            QMessageBox.information(self, "Success", "Student deleted successfully.")
            self.LoadStudent()
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Database Error", f"Error deleting student: {str(e)}")
    def SearchStudent(self):
        search_text = self.ui.Searchbybox.text().strip()
        if not search_text:
            self.LoadStudent()
            return
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id LIKE ? OR first_name LIKE ? OR last_name LIKE ?", 
                       (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"))

        self.ui.StudentTable.setRowCount(0)
        for row_index, row_data in enumerate(cursor.fetchall()):
            self.ui.StudentTable.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.StudentTable.setItem(row_index, col_index, QTableWidgetItem(str(data)))

    def FilterStudents(self):
        search_text = self.ui.Searchbybox.text().strip()
        selected_filter = self.ui.Sortbybox.currentIndex()

        if not search_text:
            self.LoadStudent()
            return

        column_map = {
            1: "id",
            2: "first_name",
            3: "last_name",
            4: "year_level",
            5: "gender",
            6: "program_code"
        }

        if selected_filter not in column_map:
            return

        field = column_map[selected_filter]

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM students WHERE {field} LIKE ?", (f"%{search_text}%",))

        self.ui.StudentTable.setRowCount(0)
        for row_index, row_data in enumerate(cursor.fetchall()):
            self.ui.StudentTable.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.StudentTable.setItem(row_index, col_index, QTableWidgetItem(str(data)))

    def StudentRefresh(self):
        self.ui.Searchbybox.clear()
        self.ui.Sortbybox.setCurrentIndex(0)
        self.LoadStudent()

    def ClearStudentInputs(self):
        self.ui.IDnoBox.clear()
        self.ui.FristNbox.clear()
        self.ui.LastNbox.clear()
        self.ui.Yrlvlbox.setCurrentIndex(0)
        self.ui.genderbox.setCurrentIndex(0)
        self.ui.prcComboBox.setCurrentIndex(0)

        # Reset the Add Button if it was in edit mode
        if hasattr(self, 'editing_student_id') and self.editing_student_id:
            self.ui.AddSt.setText("Add Student")
            self.ui.AddSt.clicked.disconnect()
            self.ui.AddSt.clicked.connect(self.AddStudent)
            self.editing_student_id = None
           

    def studentidformat(self, student_id):
        return bool(re.match(r'^\d{4}-\d{4}$', student_id))

    def studentnameformat(self, name):
        return bool(re.match(r'^[a-zA-Z ]+$', name))


    
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# COLLEGE METHODS

    def AddCollege(self):
        collegecode = self.ui.AddCCodeBox.text().strip().upper()
        collegename = self.ui.CollegeNbox.text().strip()

        if not collegecode or not collegename:
            QMessageBox.warning(self, "Input Error", "All fields must be filled.")
            return
        if not collegecode.isalnum():
            QMessageBox.warning(self, "Input Error", "College Code must be letters and numbers only.")
            return


        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO colleges (code, name) VALUES (?, ?)", (collegecode, collegename))
            self.conn.commit()
            QMessageBox.information(self, "Success", "College added successfully.")
            self.LoadCollege()
            self.ClearCollegeInputs()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate Error", "College Code already exists.")

    def LoadCollege(self):  
        self.ui.COLLEGETABLE.setSortingEnabled(False)
        self.ui.COLLEGETABLE.setRowCount(0)
        self.College_Code.clear()

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM colleges")
        total_colleges = cursor.fetchone()[0]
        
        # Calculate valid pagination
        max_page = (total_colleges - 1) // self.colleges_per_page if total_colleges > 0 else 0
        if self.current_college_page > max_page:
            self.current_college_page = max_page
        if self.current_college_page < 0:
            self.current_college_page = 0
            
        start = self.current_college_page * self.colleges_per_page
        cursor.execute("SELECT * FROM colleges LIMIT ? OFFSET ?", 
                     (self.colleges_per_page, start))

        for row_index, row_data in enumerate(cursor.fetchall()):
            self.ui.COLLEGETABLE.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.COLLEGETABLE.setItem(row_index, col_index, QTableWidgetItem(str(data)))
            self.College_Code.add(row_data[0])

        # Load all college codes for combo boxes
        cursor.execute("SELECT code FROM colleges")
        for code in cursor.fetchall():
            self.College_Code.add(code[0])

        self.combo_boxes()
        self.ui.COLLEGETABLE.setSortingEnabled(True)
        self.ui.COLLEGETABLE.horizontalHeader().setSortIndicator(-1, 0)
    def NextCollegePage(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM colleges")
        total_colleges = cursor.fetchone()[0]

        if (self.current_college_page + 1) * self.colleges_per_page < total_colleges:
            self.current_college_page += 1
            self.LoadCollege()
        
    def PrevCollegePage(self):
        if self.current_college_page > 0:
            self.current_college_page -= 1
            self.LoadCollege()

    def EditCollege(self):
        selected_row = self.ui.COLLEGETABLE.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a College to edit.")
            return
        
        college_code = self.ui.COLLEGETABLE.item(selected_row, 0).text()
        college_name = self.ui.COLLEGETABLE.item(selected_row, 1).text()
        
        reply = QMessageBox.information(self, "Edit College", 
                                        "You can edit the college details and click 'Update College' to save changes.",
                                        QMessageBox.Ok | QMessageBox.No) 
        if reply == QMessageBox.No:
            return

        # Load existing values into input fields
        self.ui.AddCCodeBox.setText(college_code)
        self.ui.CollegeNbox.setText(college_name)
        
        # Set edit mode
        self.editing_college_code = college_code
        self.ui.AddCo.setText("Update")
        
        # Temporarily change button action
        self.ui.AddCo.clicked.disconnect()
        self.ui.AddCo.clicked.connect(self.UpdateCollege)

    def UpdateCollege(self):
        new_code = self.ui.AddCCodeBox.text().strip().upper()
        new_name = self.ui.CollegeNbox.text().strip()

        if not new_code or not new_name:
            QMessageBox.warning(self, "Input Error", "All fields must be filled.")
            return
        
        if not new_code.isalnum():
            QMessageBox.warning(self, "Input Error", "College Code must be letters and numbers only.")
            return

        cursor = self.conn.cursor()
        try:
            # Only check for duplicate if the code was changed
            if new_code != self.editing_college_code:
                cursor.execute("SELECT 1 FROM colleges WHERE code=?", (new_code,))
                if cursor.fetchone():
                    QMessageBox.warning(self, "Duplicate Error", "College Code already exists.")
                    return

            # Update the college record
            cursor.execute("UPDATE colleges SET code=?, name=? WHERE code=?", 
                        (new_code, new_name, self.editing_college_code))
            
            # If code changed, update all programs referencing this college
            if new_code != self.editing_college_code:
                cursor.execute("UPDATE programs SET college_code=? WHERE college_code=?", 
                            (new_code, self.editing_college_code))
            
            self.conn.commit()
            QMessageBox.information(self, "Success", "College updated successfully.")
            
            # Reset edit mode
            self.ui.AddCo.setText("Add College")
            self.ui.AddCo.clicked.disconnect()
            self.ui.AddCo.clicked.connect(self.AddCollege)
            self.editing_college_code = None
            
            # Refresh all tables
            self.LoadCollege()
            self.LoadProgram()
            self.LoadStudent()
            self.ClearCollegeInputs()
            
        except sqlite3.Error as e:
            self.conn.rollback()
            QMessageBox.warning(self, "Database Error", f"Error updating college: {str(e)}")



    def DeleteCollege(self):
        selected_row = self.ui.COLLEGETABLE.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a College to delete.")
            return

        college_code = self.ui.COLLEGETABLE.item(selected_row, 0).text()

        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            "Are you sure you want to delete this College? This will set all programs' college code to NULL.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        cursor = self.conn.cursor()
        try:
            # First set all programs' college_code to NULL
            cursor.execute("UPDATE programs SET college_code=NULL WHERE college_code=?", (college_code,))
            
            # Then delete the college
            cursor.execute("DELETE FROM colleges WHERE code=?", (college_code,))
            
            self.conn.commit()
            
            QMessageBox.information(
                self, 
                "Success", 
                "College deleted successfully. Associated programs now have no college."
            )
            
            self.LoadCollege()
            self.LoadProgram()
            self.LoadStudent()
            
        except sqlite3.Error as e:
            self.conn.rollback()
            QMessageBox.warning(self, "Database Error", f"Error: {str(e)}")

    def SearchCollege(self):
        search_text = self.ui.Searchbox.text().strip()
        if not search_text:
            self.LoadCollege()
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM colleges WHERE code LIKE ? OR name LIKE ?", (f"%{search_text}%", f"%{search_text}%"))

        self.ui.COLLEGETABLE.setRowCount(0)
        for row_index, row_data in enumerate(cursor.fetchall()):
            self.ui.COLLEGETABLE.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.COLLEGETABLE.setItem(row_index, col_index, QTableWidgetItem(str(data)))

    def FilterColleges(self):
        search_text = self.ui.Searchbox.text().strip()
        selected_filter = self.ui.Sortbox.currentIndex()

        if not search_text:
            self.LoadCollege()
            return

        column_map = {
            1: "code",
            2: "name"
        }

        if selected_filter not in column_map:
            return

        field = column_map[selected_filter]

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM colleges WHERE {field} LIKE ?", (f"%{search_text}%",))

        results = cursor.fetchall()
        self.ui.COLLEGETABLE.setRowCount(0)

        for row_index, row_data in enumerate(results):
            self.ui.COLLEGETABLE.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.COLLEGETABLE.setItem(row_index, col_index, QTableWidgetItem(str(data)))

    def CollegeRefresh(self):
        self.ui.Searchbox.clear()
        self.ui.Sortbox.setCurrentIndex(0)
        self.LoadCollege()

    def ClearCollegeInputs(self):
        self.ui.AddCCodeBox.clear()
        self.ui.CollegeNbox.clear()
    
        if hasattr(self, 'editing_college_code') and self.editing_college_code:
            self.ui.AddCo.setText("Add College")
            self.ui.AddCo.clicked.disconnect()
            self.ui.AddCo.clicked.connect(self.AddCollege)
            self.editing_college_code = None
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# PROGRAM METHODS

    def AddProgram(self):
        programcode = self.ui.PrCodeBox.text().strip()
        programname = self.ui.ProgNbox.text().strip()
        collegecode = self.ui.ccComboBox.currentText().strip()

        if not programcode or not programname or collegecode == "Please Select":
            QMessageBox.warning(self, "Input Error", "All fields must be filled.")
            return
        if not programcode.isalnum():
            QMessageBox.warning(self, "Input Error", "Program Code must be letters and numbers only.")
            return

        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO programs (code, name, college_code) VALUES (?, ?, ?)", (programcode, programname, collegecode))
            self.conn.commit()
            QMessageBox.information(self, "Success", "Program added successfully.")
            self.LoadProgram()
            self.ClearProgramInputs()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate Error", "Program Code already exists.")
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Database Error", f"Error adding program: {str(e)}")

    def LoadProgram(self):
        self.ui.COLLEGETABLE_2.setSortingEnabled(False)
        self.ui.COLLEGETABLE_2.setRowCount(0)
        self.Program_Code.clear()
        self.ProgramCollegeMap.clear()

        cursor = self.conn.cursor()

        # Load ALL program codes for dropdown
        cursor.execute("SELECT code, college_code FROM programs")
        for code, college_code in cursor.fetchall():
            self.Program_Code.add(code)
            self.ProgramCollegeMap[code] = college_code

        # Load only paginated data for table display
        cursor.execute("SELECT * FROM programs")
        all_programs = cursor.fetchall()
        start = self.current_program_page * self.programs_per_page 
        end = start + self.programs_per_page
        paginated_programs = all_programs[start:end]

        self.ui.COLLEGETABLE_2.setRowCount(0)
        for row_index, row_data in enumerate(paginated_programs):
            self.ui.COLLEGETABLE_2.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.COLLEGETABLE_2.setItem(row_index, col_index, QTableWidgetItem(str(data)))


        self.combo_boxes()
        self.ui.COLLEGETABLE_2.setSortingEnabled(True)
        self.ui.COLLEGETABLE_2.horizontalHeader().setSortIndicator(-1, 0)
    
    def NextProgramPage(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM programs")
        total_programs = cursor.fetchone()[0]

        if (self.current_program_page + 1) * self.programs_per_page < total_programs:
            self.current_program_page += 1
            self.LoadProgram()
    
    def PrevProgramPage(self):
        if self.current_program_page > 0:
            self.current_program_page -= 1
            self.LoadProgram()

    def EditProgram(self):
        selected_row = self.ui.COLLEGETABLE_2.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a Program to edit.")
            return

        program_code = self.ui.COLLEGETABLE_2.item(selected_row, 0).text()
        program_name = self.ui.COLLEGETABLE_2.item(selected_row, 1).text()
        college_code = self.ui.COLLEGETABLE_2.item(selected_row, 2).text()
        
        reply = QMessageBox.information(self, "Edit Program", 
                                        "You can edit the program details and click 'Update Program' to save changes.",
                                        QMessageBox.Ok | QMessageBox.No) 
        if reply == QMessageBox.No:
            return

        # Load current values into the input fields
        self.ui.PrCodeBox.setText(program_code)
        self.ui.ProgNbox.setText(program_name)
        self.ui.ccComboBox.setCurrentText(college_code if college_code else "Please Select")
        
        # Set edit mode
        self.editing_program_code = program_code
        self.ui.AddProg.setText("Update")
        
        # Temporarily change button action
        self.ui.AddProg.clicked.disconnect()
        self.ui.AddProg.clicked.connect(self.UpdateProgram)

    def UpdateProgram(self):
        new_code = self.ui.PrCodeBox.text().strip()
        name = self.ui.ProgNbox.text().strip()
        college_code = self.ui.ccComboBox.currentText().strip()
        
        if college_code == "Please Select":
            college_code = None

        if not new_code or not name:
            QMessageBox.warning(self, "Input Error", "Program code and name must be filled.")
            return
                
        if not new_code.isalnum():
            QMessageBox.warning(self, "Input Error", "Program Code must be letters and numbers only.")
            return

        cursor = self.conn.cursor()
        try: 
            if new_code != self.editing_program_code:
                # Only check for duplicates if the code is being changed
                cursor.execute("SELECT 1 FROM programs WHERE code=?", (new_code,))
                if cursor.fetchone():
                    raise sqlite3.IntegrityError("Program code already exists")
                
                # Update the program record
                cursor.execute("UPDATE programs SET code=?, name=?, college_code=? WHERE code=?", 
                            (new_code, name, college_code, self.editing_program_code))
                
                # Update the program_code in students table
                cursor.execute("UPDATE students SET program_code=? WHERE program_code=?", 
                            (new_code, self.editing_program_code))
            else:
                # Only update name and college if code didn't change
                cursor.execute("UPDATE programs SET name=?, college_code=? WHERE code=?", 
                            (name, college_code, new_code))
                
            # Commit the transaction
            self.conn.commit()
            
            QMessageBox.information(self, "Success", "Program updated successfully.")
            
            # Reset edit mode
            self.ui.AddProg.setText("Add Program")
            self.ui.AddProg.clicked.disconnect()
            self.ui.AddProg.clicked.connect(self.AddProgram)
            self.editing_program_code = None
            
            # Refresh all tables that might be affected
            self.LoadProgram()
            self.LoadStudent()
            self.ClearProgramInputs()
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            QMessageBox.warning(self, "Duplicate Error", "Program code already exists.")
        except sqlite3.Error as e:
            self.conn.rollback()
            QMessageBox.warning(self, "Database Error", f"Error updating program: {str(e)}")


    def DeleteProgram(self):
        selected_row = self.ui.COLLEGETABLE_2.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Error", "Please select a Program to delete.")
            return

        program_code = self.ui.COLLEGETABLE_2.item(selected_row, 0).text()

        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            "Are you sure you want to delete this Program? All students in this program will have their program set to NULL.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        cursor = self.conn.cursor()
        try:
            # Begin transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            # First update all students' program_code to NULL
            cursor.execute("UPDATE students SET program_code=NULL WHERE program_code=?", (program_code,))
            
            # Then delete the program
            cursor.execute("DELETE FROM programs WHERE code=?", (program_code,))
            
            # Commit the transaction
            self.conn.commit()
            
            QMessageBox.information(
                self, 
                "Success", 
                "Program deleted successfully. Associated students now have no program."
            )
            
            # Refresh all tables
            self.LoadProgram()
            self.LoadStudent()
            
        except sqlite3.Error as e:
            # Rollback if any error occurs
            self.conn.rollback()
            QMessageBox.warning(self, "Database Error", f"Error deleting program: {str(e)}")

    def SearchProgram(self):
        search_text = self.ui.Searchbybox_2.text().strip()
        if not search_text:
            self.LoadProgram()
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM programs WHERE code LIKE ? OR name LIKE ? OR college_code LIKE ?", 
                       (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"))

        self.ui.COLLEGETABLE_2.setRowCount(0)
        for row_index, row_data in enumerate(cursor.fetchall()):
            self.ui.COLLEGETABLE_2.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.COLLEGETABLE_2.setItem(row_index, col_index, QTableWidgetItem(str(data)))

    def FilterPrograms(self):
        search_text = self.ui.Searchbybox_2.text().strip()
        selected_filter = self.ui.Sortbybox_2.currentIndex()

        if not search_text:
            self.LoadProgram()
            return

        column_map = {
            1: "code",
            2: "name",
            3: "college_code"
        }

        if selected_filter not in column_map:
            return

        field = column_map[selected_filter]

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM programs WHERE {field} LIKE ?", (f"%{search_text}%",))

        self.ui.COLLEGETABLE_2.setRowCount(0)
        for row_index, row_data in enumerate(cursor.fetchall()):
            self.ui.COLLEGETABLE_2.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.ui.COLLEGETABLE_2.setItem(row_index, col_index, QTableWidgetItem(str(data)))

    def ProgramRefresh(self):
        self.ui.Searchbybox_2.clear()
        self.ui.Sortbybox_2.setCurrentIndex(0)
        self.LoadProgram()

    def ClearProgramInputs(self):
        self.ui.PrCodeBox.clear()
        self.ui.ProgNbox.clear()
        self.ui.ccComboBox.setCurrentIndex(0)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# Main Function to Run the App
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudentSystem()
    window.show()
    sys.exit(app.exec_())


