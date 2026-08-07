CREATE TABLE teachers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  last_name VARCHAR(40) NOT NULL,
  first_name VARCHAR(40) NOT NULL,
  city VARCHAR(60),
  active TINYINT DEFAULT 1
);
CREATE TABLE students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  last_name VARCHAR(40) NOT NULL,
  first_name VARCHAR(40) NOT NULL,
  city VARCHAR(60),
  birthdate CHAR(8),
  gpa DOUBLE,
  active TINYINT DEFAULT 1
);
CREATE TABLE courses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(16) UNIQUE NOT NULL,
  title VARCHAR(100) NOT NULL,
  credits INT DEFAULT 3,
  teacher_id INT,
  FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);
CREATE TABLE enrollments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  course_id INT NOT NULL,
  grade CHAR(2),
  UNIQUE KEY uq_student_course (student_id, course_id),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (course_id) REFERENCES courses(id)
);
