import sqlite3
import random
from faker import Faker

fake = Faker()

DB_FILE = "system.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Generate 20 colleges
college_codes = [f"C{str(i).zfill(2)}" for i in range(1, 21)]
for code in college_codes:
    cursor.execute("INSERT OR IGNORE INTO colleges (code, name) VALUES (?, ?)", (code, f"College of {code}"))

# Generate 30 programs and assign them to colleges randomly
program_codes = [f"P{str(i).zfill(2)}" for i in range(1, 31)]
for code in program_codes:
    college_code = random.choice(college_codes)
    cursor.execute("INSERT OR IGNORE INTO programs (code, name, college_code) VALUES (?, ?, ?)", 
                   (code, f"Program {code}", college_code))

# Generate 2000 students with realistic names
for i in range(2000):
    year = random.randint(2020, 2025)
    num = str(i).zfill(4)
    student_id = f"{year}-{num}"
    fname = fake.first_name()
    lname = fake.last_name()
    year_level = random.choice(['1st', '2nd', '3rd', '4th'])
    gender = random.choice(['M', 'F', 'Other'])
    program_code = random.choice(program_codes)

    cursor.execute("""
        INSERT OR IGNORE INTO students (id, first_name, last_name, year_level, gender, program_code)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student_id, fname, lname, year_level, gender, program_code))

conn.commit()
conn.close()
print("Database seeded successfully with real names.")
