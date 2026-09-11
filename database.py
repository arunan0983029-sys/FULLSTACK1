import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'portal.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            instructor TEXT NOT NULL,
            department TEXT NOT NULL,
            credits INTEGER DEFAULT 3,
            capacity INTEGER DEFAULT 30,
            enrolled_count INTEGER DEFAULT 0,
            level TEXT DEFAULT 'Beginner',
            schedule TEXT DEFAULT 'Mon / Wed 10:00 AM - 11:30 AM',
            cover_image TEXT,
            prerequisites TEXT DEFAULT 'None',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            year TEXT DEFAULT 'Sophomore',
            gpa REAL DEFAULT 3.6,
            avatar TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create enrollments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            status TEXT DEFAULT 'enrolled',
            grade TEXT DEFAULT 'N/A',
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()

    # Check if seed data is needed
    cursor.execute('SELECT COUNT(*) FROM courses')
    count = cursor.fetchone()[0]

    if count == 0:
        seed_portal_data(cursor)
        conn.commit()

    conn.close()

def seed_portal_data(cursor):
    sample_courses = [
        {
            "code": "CS-101",
            "title": "Introduction to Computer Science & Algorithms",
            "description": "Comprehensive foundation in problem-solving, data structures, computational thinking, and software engineering principles.",
            "instructor": "Dr. Alan Turing",
            "department": "Computer Science",
            "credits": 4,
            "capacity": 35,
            "enrolled_count": 3,
            "level": "Beginner",
            "schedule": "Mon / Wed 09:00 AM - 10:30 AM",
            "cover_image": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&auto=format&fit=crop&q=80",
            "prerequisites": "None"
        },
        {
            "code": "DS-204",
            "title": "Data Science & Applied Machine Learning",
            "description": "Hands-on exploration of statistical inference, data wrangling with Python, pandas, regression models, and neural networks.",
            "instructor": "Prof. Fei-Fei Li",
            "department": "Data Science",
            "credits": 4,
            "capacity": 25,
            "enrolled_count": 2,
            "level": "Intermediate",
            "schedule": "Tue / Thu 01:00 PM - 02:30 PM",
            "cover_image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop&q=80",
            "prerequisites": "CS-101 or Linear Algebra"
        },
        {
            "code": "UX-150",
            "title": "UI/UX Design Systems & Human Factors",
            "description": "Principles of user-centered design, interactive wireframing, design tokens, visual hierarchy, and usability testing.",
            "instructor": "Sarah Jenkins",
            "department": "Design",
            "credits": 3,
            "capacity": 20,
            "enrolled_count": 2,
            "level": "Beginner",
            "schedule": "Fri 10:00 AM - 01:00 PM",
            "cover_image": "https://images.unsplash.com/photo-1581291518857-4e27b48ff24e?w=800&auto=format&fit=crop&q=80",
            "prerequisites": "None"
        },
        {
            "code": "CY-310",
            "title": "Cyber Security Fundamentals & Ethical Hacking",
            "description": "Network security architecture, cryptography, threat modeling, vulnerability auditing, and defensive security strategies.",
            "instructor": "Marcus Vance",
            "department": "Computer Science",
            "credits": 3,
            "capacity": 30,
            "enrolled_count": 1,
            "level": "Advanced",
            "schedule": "Mon / Wed 02:00 PM - 03:30 PM",
            "cover_image": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&auto=format&fit=crop&q=80",
            "prerequisites": "CS-101, Computer Networks"
        },
        {
            "code": "BUS-210",
            "title": "Technology Entrepreneurship & Product Strategy",
            "description": "Building sustainable tech startups, market research, business model canvas, go-to-market strategies, and agile execution.",
            "instructor": "Elena Rostova",
            "department": "Business",
            "credits": 3,
            "capacity": 40,
            "enrolled_count": 2,
            "level": "Intermediate",
            "schedule": "Tue / Thu 10:00 AM - 11:30 AM",
            "cover_image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&auto=format&fit=crop&q=80",
            "prerequisites": "None"
        },
        {
            "code": "AI-400",
            "title": "Deep Learning & Natural Language Processing",
            "description": "Advanced Transformer architectures, attention mechanisms, LLM fine-tuning, PyTorch frameworks, and generative AI systems.",
            "instructor": "Dr. Geoffrey Hinton",
            "department": "Artificial Intelligence",
            "credits": 4,
            "capacity": 15,
            "enrolled_count": 1,
            "level": "Advanced",
            "schedule": "Wed / Fri 03:30 PM - 05:00 PM",
            "cover_image": "https://images.unsplash.com/photo-1677442136019-21780efad99a?w=800&auto=format&fit=crop&q=80",
            "prerequisites": "DS-204, Multivariable Calculus"
        }
    ]

    for c in sample_courses:
        cursor.execute('''
            INSERT INTO courses (code, title, description, instructor, department, credits, capacity, enrolled_count, level, schedule, cover_image, prerequisites)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            c["code"], c["title"], c["description"], c["instructor"], c["department"],
            c["credits"], c["capacity"], c["enrolled_count"], c["level"], c["schedule"],
            c["cover_image"], c["prerequisites"]
        ))

    sample_students = [
        {
            "student_code": "STU-2026-01",
            "name": "Alex Morgan",
            "email": "alex.morgan@university.edu",
            "department": "Computer Science",
            "year": "Junior",
            "gpa": 3.85,
            "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
        },
        {
            "student_code": "STU-2026-02",
            "name": "Samantha Reed",
            "email": "samantha.r@university.edu",
            "department": "Data Science",
            "year": "Senior",
            "gpa": 3.92,
            "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80"
        },
        {
            "student_code": "STU-2026-03",
            "name": "Devin Chen",
            "email": "devin.c@university.edu",
            "department": "Design",
            "year": "Sophomore",
            "gpa": 3.65,
            "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80"
        },
        {
            "student_code": "STU-2026-04",
            "name": "Liam O'Connor",
            "email": "liam.oc@university.edu",
            "department": "Business",
            "year": "Freshman",
            "gpa": 3.50,
            "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80"
        }
    ]

    for s in sample_students:
        cursor.execute('''
            INSERT INTO students (student_code, name, email, department, year, gpa, avatar)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            s["student_code"], s["name"], s["email"], s["department"],
            s["year"], s["gpa"], s["avatar"]
        ))

    sample_enrollments = [
        {"student_id": 1, "course_id": 1, "status": "enrolled", "grade": "A"},
        {"student_id": 1, "course_id": 2, "status": "enrolled", "grade": "A-"},
        {"student_id": 1, "course_id": 4, "status": "enrolled", "grade": "B+"},
        {"student_id": 2, "course_id": 1, "status": "completed", "grade": "A"},
        {"student_id": 2, "course_id": 2, "status": "enrolled", "grade": "A"},
        {"student_id": 2, "course_id": 6, "status": "enrolled", "grade": "A"},
        {"student_id": 3, "course_id": 3, "status": "enrolled", "grade": "B+"},
        {"student_id": 3, "course_id": 5, "status": "enrolled", "grade": "A-"},
        {"student_id": 4, "course_id": 1, "status": "enrolled", "grade": "B"},
        {"student_id": 4, "course_id": 3, "status": "enrolled", "grade": "A"},
        {"student_id": 4, "course_id": 5, "status": "enrolled", "grade": "B+"}
    ]

    for e in sample_enrollments:
        cursor.execute('''
            INSERT INTO enrollments (student_id, course_id, status, grade)
            VALUES (?, ?, ?, ?)
        ''', (e["student_id"], e["course_id"], e["status"], e["grade"]))
