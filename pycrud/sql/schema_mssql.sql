CREATE TABLE teachers (
  id INT IDENTITY(1,1) PRIMARY KEY,
  last_name NVARCHAR(40) NOT NULL,
  first_name NVARCHAR(40) NOT NULL,
  city NVARCHAR(60) NULL,
  active BIT DEFAULT 1
);
CREATE TABLE students (
  id INT IDENTITY(1,1) PRIMARY KEY,
  last_name NVARCHAR(40) NOT NULL,
  first_name NVARCHAR(40) NOT NULL,
  city NVARCHAR(60) NULL,
  birthdate CHAR(8) NULL,
  gpa FLOAT NULL,
  active BIT DEFAULT 1
);
CREATE TABLE courses (
  id INT IDENTITY(1,1) PRIMARY KEY,
  code NVARCHAR(16) UNIQUE NOT NULL,
  title NVARCHAR(100) NOT NULL,
  credits INT DEFAULT 3,
  teacher_id INT NULL,
  FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);
CREATE TABLE enrollments (
  id INT IDENTITY(1,1) PRIMARY KEY,
  student_id INT NOT NULL,
  course_id INT NOT NULL,
  grade CHAR(2) NULL,
  CONSTRAINT uq_student_course UNIQUE (student_id, course_id),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (course_id) REFERENCES courses(id)
);
