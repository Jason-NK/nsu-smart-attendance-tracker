-- NSU Smart Attendance Tracker Seed Data
-- All passwords are stored as bcrypt ($2b$12$) hashes (never plain text).
-- Demo Credentials:
--   Student 1: jkennedy@spartans.nsu.edu / Spartan123 (ID: 1234567)
--   Student 2: ccuffee@spartans.nsu.edu  / Spartan123 (ID: 7654321)
--   Student 3: tcorprew@spartans.nsu.edu / Spartan123 (ID: 1122334)
--   Professor: dnwosu@nsu.edu            / Professor123
--   IT Admin:  itadmin@nsu.edu           / AdminPass123

PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO users (id, username, full_name, email, password_hash, role, student_id, major, employee_id, department) VALUES
(1, 'jkennedy', 'Jason Kennedy', 'jkennedy@spartans.nsu.edu', '$2b$12$CrBsI4XkVkwlsBg0pDRnDeDEe47p0KsoieVmzc.4W/o1jUW/f60Ca', 'student', '1234567', 'Computer Science', NULL, NULL),
(2, 'ccuffee', 'Carissa Cuffee', 'ccuffee@spartans.nsu.edu', '$2b$12$CrBsI4XkVkwlsBg0pDRnDeDEe47p0KsoieVmzc.4W/o1jUW/f60Ca', 'student', '7654321', 'Computer Science', NULL, NULL),
(3, 'tcorprew', 'Tyson Corprew', 'tcorprew@spartans.nsu.edu', '$2b$12$CrBsI4XkVkwlsBg0pDRnDeDEe47p0KsoieVmzc.4W/o1jUW/f60Ca', 'student', '1122334', 'Computer Science', NULL, NULL),
(4, 'dnwosu', 'Dr. Nwosu', 'dnwosu@nsu.edu', '$2b$12$mL0v3ZsoTBK1e9g0bowIT.hsxMyZ78s18MbI/yL0V.AjLg7.Bu9di', 'professor', NULL, NULL, 'EMP-1001', 'Computer Science'),
(5, 'itadmin', 'NSU IT Admin', 'itadmin@nsu.edu', '$2b$12$6XD4YgkaukZQe0dEm4TunuuyDSK.R9qR7ucfDJBjclWaAoR2sjeRC', 'admin', NULL, NULL, 'ADM-9001', 'Information Technology');

INSERT OR IGNORE INTO courses (id, course_code, course_name, professor_id) VALUES
(1, 'CSC-380', 'Software Engineering', 4);

INSERT OR IGNORE INTO enrollments (course_id, student_id, student_name, student_email) VALUES
(1, '1234567', 'Jason Kennedy', 'jkennedy@spartans.nsu.edu'),
(1, '7654321', 'Carissa Cuffee', 'ccuffee@spartans.nsu.edu'),
(1, '1122334', 'Tyson Corprew', 'tcorprew@spartans.nsu.edu');

INSERT OR IGNORE INTO attendance_sessions (id, course_id, session_date, start_time, end_time, totp_secret, is_active) VALUES
(1, 1, '2026-11-15', '10:00', '11:15', 'JBSWY3DPEHPK3PXP', 0);

INSERT OR IGNORE INTO attendance_records (id, session_id, course_id, user_id, student_id, student_name, check_in_time, status) VALUES
(1, 1, 1, 1, '1234567', 'Jason Kennedy', '2026-11-15 10:02:14', 'Present'),
(2, 1, 1, 2, '7654321', 'Carissa Cuffee', '2026-11-15 10:03:05', 'Present');
