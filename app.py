from flask import Flask, render_template, request, jsonify
import sqlite3
from database import get_db_connection, init_db

app = Flask(__name__)

# Initialize database schema and seed data
init_db()

MAX_CREDITS_PER_STUDENT = 18

def dict_from_row(row):
    return dict(row) if row else None

@app.route('/')
def index():
    return render_template('index.html')

# ==============================================================================
# COURSES API ENDPOINTS
# ==============================================================================

@app.route('/api/courses', methods=['GET'])
def get_courses():
    q = request.args.get('q', '').strip()
    department = request.args.get('department', '').strip()
    level = request.args.get('level', '').strip()
    status = request.args.get('status', 'all').strip()

    query = 'SELECT * FROM courses WHERE 1=1'
    params = []

    if department and department != 'All':
        query += ' AND department = ?'
        params.append(department)

    if level and level != 'All':
        query += ' AND level = ?'
        params.append(level)

    if status == 'open':
        query += ' AND enrolled_count < capacity'
    elif status == 'full':
        query += ' AND enrolled_count >= capacity'

    if q:
        query += ' AND (code LIKE ? OR title LIKE ? OR instructor LIKE ? OR description LIKE ?)'
        pattern = f'%{q}%'
        params.extend([pattern, pattern, pattern, pattern])

    query += ' ORDER BY code ASC'

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    courses = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify(courses)

@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course_detail(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Course not found'}), 404

    course = dict_from_row(row)

    # Fetch enrolled students
    cursor.execute('''
        SELECT e.id as enrollment_id, e.status, e.grade, e.enrolled_at,
               s.id as student_id, s.student_code, s.name as student_name, s.email as student_email, s.avatar, s.year, s.department as student_department
        FROM enrollments e
        JOIN students s ON e.student_id = s.id
        WHERE e.course_id = ?
        ORDER BY s.name ASC
    ''', (course_id,))
    
    course['enrolled_students'] = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify(course)

@app.route('/api/courses', methods=['POST'])
def create_course():
    data = request.get_json() or {}
    
    code = data.get('code', '').strip().upper()
    title = data.get('title', '').strip()
    instructor = data.get('instructor', '').strip()
    department = data.get('department', 'Computer Science').strip()
    description = data.get('description', '').strip()
    credits = int(data.get('credits', 3))
    capacity = int(data.get('capacity', 30))
    level = data.get('level', 'Beginner').strip()
    schedule = data.get('schedule', 'Mon / Wed 10:00 AM - 11:30 AM').strip()
    cover_image = data.get('cover_image', '').strip()
    prerequisites = data.get('prerequisites', 'None').strip()

    if not code:
        return jsonify({'error': 'Course code is required (e.g., CS-101)'}), 400
    if not title:
        return jsonify({'error': 'Course title is required'}), 400
    if not instructor:
        return jsonify({'error': 'Instructor name is required'}), 400

    if not cover_image:
        cover_image = 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&auto=format&fit=crop&q=80'

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check unique code
    cursor.execute('SELECT id FROM courses WHERE code = ?', (code,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Course code {code} already exists'}), 400

    cursor.execute('''
        INSERT INTO courses (code, title, description, instructor, department, credits, capacity, level, schedule, cover_image, prerequisites)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (code, title, description, instructor, department, credits, capacity, level, schedule, cover_image, prerequisites))

    course_id = cursor.lastrowid
    conn.commit()

    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    new_course = dict_from_row(cursor.fetchone())
    conn.close()

    return jsonify(new_course), 201

@app.route('/api/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    data = request.get_json() or {}

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'Course not found'}), 404

    code = data.get('code', existing['code']).strip().upper()
    title = data.get('title', existing['title']).strip()
    instructor = data.get('instructor', existing['instructor']).strip()
    department = data.get('department', existing['department']).strip()
    description = data.get('description', existing['description']).strip()
    credits = int(data.get('credits', existing['credits']))
    capacity = int(data.get('capacity', existing['capacity']))
    level = data.get('level', existing['level']).strip()
    schedule = data.get('schedule', existing['schedule']).strip()
    cover_image = data.get('cover_image', existing['cover_image']).strip()
    prerequisites = data.get('prerequisites', existing['prerequisites']).strip()

    cursor.execute('''
        UPDATE courses
        SET code = ?, title = ?, description = ?, instructor = ?, department = ?, credits = ?, capacity = ?, level = ?, schedule = ?, cover_image = ?, prerequisites = ?
        WHERE id = ?
    ''', (code, title, description, instructor, department, credits, capacity, level, schedule, cover_image, prerequisites, course_id))

    conn.commit()
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    updated = dict_from_row(cursor.fetchone())
    conn.close()

    return jsonify(updated)

@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM courses WHERE id = ?', (course_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Course not found'}), 404

    cursor.execute('DELETE FROM enrollments WHERE course_id = ?', (course_id,))
    cursor.execute('DELETE FROM courses WHERE id = ?', (course_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': f'Course {course_id} deleted successfully'})

# ==============================================================================
# STUDENTS API ENDPOINTS
# ==============================================================================

@app.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.*, 
               COUNT(e.id) as total_enrollments,
               COALESCE(SUM(CASE WHEN e.status = 'enrolled' THEN c.credits ELSE 0 END), 0) as total_credits
        FROM students s
        LEFT JOIN enrollments e ON s.id = e.student_id
        LEFT JOIN courses c ON e.course_id = c.id
        GROUP BY s.id
        ORDER BY s.name ASC
    ''')
    students = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify(students)

@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student_profile(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Student not found'}), 404

    student = dict_from_row(row)

    # Fetch student's course schedule & transcript
    cursor.execute('''
        SELECT e.id as enrollment_id, e.status, e.grade, e.enrolled_at,
               c.id as course_id, c.code, c.title, c.instructor, c.department, c.credits, c.schedule, c.cover_image
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = ?
        ORDER BY e.enrolled_at DESC
    ''', (student_id,))
    
    student['enrolled_courses'] = [dict_from_row(r) for r in cursor.fetchall()]
    student['total_credits'] = sum(c['credits'] for c in student['enrolled_courses'] if c['status'] == 'enrolled')
    conn.close()

    return jsonify(student)

@app.route('/api/students', methods=['POST'])
def create_student():
    data = request.get_json() or {}
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    department = data.get('department', 'Computer Science').strip()
    year = data.get('year', 'Freshman').strip()
    gpa = float(data.get('gpa', 3.5))
    avatar = data.get('avatar', '').strip()

    if not name:
        return jsonify({'error': 'Student name is required'}), 400
    if not email:
        return jsonify({'error': 'Student email is required'}), 400

    if not avatar:
        avatar = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80'

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check unique email
    cursor.execute('SELECT id FROM students WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': f'Email {email} is already registered'}), 400

    # Auto generate student code STU-2026-XX
    cursor.execute('SELECT COUNT(*) FROM students')
    count = cursor.fetchone()[0] + 1
    student_code = f"STU-2026-{count:02d}"

    cursor.execute('''
        INSERT INTO students (student_code, name, email, department, year, gpa, avatar)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (student_code, name, email, department, year, gpa, avatar))

    student_id = cursor.lastrowid
    conn.commit()

    cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    new_student = dict_from_row(cursor.fetchone())
    conn.close()

    return jsonify(new_student), 201

# ==============================================================================
# ENROLLMENTS API ENDPOINTS
# ==============================================================================

@app.route('/api/enrollments', methods=['GET'])
def get_enrollments():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT e.id as enrollment_id, e.status, e.grade, e.enrolled_at,
               s.id as student_id, s.student_code, s.name as student_name, s.email as student_email, s.avatar as student_avatar,
               c.id as course_id, c.code as course_code, c.title as course_title, c.credits, c.schedule, c.department as course_department
        FROM enrollments e
        JOIN students s ON e.student_id = s.id
        JOIN courses c ON e.course_id = c.id
        ORDER BY e.enrolled_at DESC
    ''')
    enrollments = [dict_from_row(r) for r in cursor.fetchall()]
    conn.close()

    return jsonify(enrollments)

@app.route('/api/enrollments', methods=['POST'])
def create_enrollment():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    course_id = data.get('course_id')

    if not student_id or not course_id:
        return jsonify({'error': 'Both student_id and course_id are required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check student existence
    cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({'error': 'Student not found'}), 404

    # Check course existence
    cursor.execute('SELECT * FROM courses WHERE id = ?', (course_id,))
    course = cursor.fetchone()
    if not course:
        conn.close()
        return jsonify({'error': 'Course not found'}), 404

    # Rule 1: Check existing enrollment
    cursor.execute('SELECT * FROM enrollments WHERE student_id = ? AND course_id = ?', (student_id, course_id))
    existing_enrollment = cursor.fetchone()
    if existing_enrollment:
        conn.close()
        status_text = existing_enrollment['status']
        return jsonify({'error': f"Student is already registered in {course['code']} (Status: {status_text})"}), 400

    # Rule 2: Check student credit limit
    cursor.execute('''
        SELECT COALESCE(SUM(c.credits), 0) as current_credits
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = ? AND e.status = 'enrolled'
    ''', (student_id,))
    current_credits = cursor.fetchone()['current_credits']

    if current_credits + course['credits'] > MAX_CREDITS_PER_STUDENT:
        conn.close()
        return jsonify({
            'error': f"Cannot enroll in {course['code']} ({course['credits']} credits). Total active credits would be {current_credits + course['credits']}, exceeding the max limit of {MAX_CREDITS_PER_STUDENT} credits."
        }), 400

    # Rule 3: Check course capacity
    status = 'enrolled'
    if course['enrolled_count'] >= course['capacity']:
        status = 'waitlist'

    cursor.execute('''
        INSERT INTO enrollments (student_id, course_id, status)
        VALUES (?, ?, ?)
    ''', (student_id, course_id, status))
    
    enrollment_id = cursor.lastrowid

    if status == 'enrolled':
        cursor.execute('UPDATE courses SET enrolled_count = enrolled_count + 1 WHERE id = ?', (course_id,))

    conn.commit()

    cursor.execute('''
        SELECT e.id as enrollment_id, e.status, e.grade, e.enrolled_at,
               s.name as student_name, c.code as course_code, c.title as course_title
        FROM enrollments e
        JOIN students s ON e.student_id = s.id
        JOIN courses c ON e.course_id = c.id
        WHERE e.id = ?
    ''', (enrollment_id,))
    new_enrollment = dict_from_row(cursor.fetchone())
    conn.close()

    message = f"Successfully enrolled {student['name']} in {course['code']}"
    if status == 'waitlist':
        message = f"Course capacity full. {student['name']} added to Waitlist for {course['code']}"

    return jsonify({'message': message, 'enrollment': new_enrollment}), 201

@app.route('/api/enrollments/<int:enrollment_id>', methods=['PUT'])
def update_enrollment(enrollment_id):
    data = request.get_json() or {}
    new_status = data.get('status', '').strip().lower()
    new_grade = data.get('grade', '').strip().upper()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM enrollments WHERE id = ?', (enrollment_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'Enrollment record not found'}), 404

    old_status = existing['status']
    course_id = existing['course_id']

    # Update logic
    grade_val = new_grade if new_grade else existing['grade']
    status_val = new_status if new_status else old_status

    cursor.execute('UPDATE enrollments SET status = ?, grade = ? WHERE id = ?', (status_val, grade_val, enrollment_id))

    # Adjust course enrolled_count if status changed to/from 'enrolled'
    if old_status == 'enrolled' and status_val in ['dropped']:
        cursor.execute('UPDATE courses SET enrolled_count = MAX(0, enrolled_count - 1) WHERE id = ?', (course_id,))
    elif old_status in ['dropped', 'waitlist'] and status_val == 'enrolled':
        cursor.execute('UPDATE courses SET enrolled_count = enrolled_count + 1 WHERE id = ?', (course_id,))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Enrollment record updated successfully'})

@app.route('/api/enrollments/<int:enrollment_id>', methods=['DELETE'])
def drop_enrollment(enrollment_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM enrollments WHERE id = ?', (enrollment_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'Enrollment record not found'}), 404

    course_id = existing['course_id']
    old_status = existing['status']

    cursor.execute('DELETE FROM enrollments WHERE id = ?', (enrollment_id,))
    if old_status == 'enrolled':
        cursor.execute('UPDATE courses SET enrolled_count = MAX(0, enrolled_count - 1) WHERE id = ?', (course_id,))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Enrollment dropped successfully'})

# ==============================================================================
# ANALYTICS API ENDPOINTS
# ==============================================================================

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM courses')
    total_courses = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM students')
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM enrollments WHERE status = 'enrolled'")
    total_active_enrollments = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COALESCE(SUM(c.credits), 0)
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.status = 'enrolled'
    ''')
    total_credits_handled = cursor.fetchone()[0]

    cursor.execute('SELECT department, COUNT(*) as count FROM courses GROUP BY department')
    dept_distribution = [dict_from_row(r) for r in cursor.fetchall()]

    cursor.execute('''
        SELECT code, title, enrolled_count, capacity 
        FROM courses 
        ORDER BY enrolled_count DESC 
        LIMIT 5
    ''')
    top_courses = [dict_from_row(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        'total_courses': total_courses,
        'total_students': total_students,
        'active_enrollments': total_active_enrollments,
        'total_credits_handled': total_credits_handled,
        'department_distribution': dept_distribution,
        'top_courses': top_courses
    })

@app.route('/api/seed', methods=['POST'])
def reset_seed():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS enrollments')
    cursor.execute('DROP TABLE IF EXISTS students')
    cursor.execute('DROP TABLE IF EXISTS courses')
    conn.commit()
    conn.close()

    init_db()
    return jsonify({'message': 'Student Portal database reset successfully'})

if __name__ == '__main__':
    print("Starting Student Course Management Portal on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
