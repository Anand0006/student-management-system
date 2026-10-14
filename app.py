import pandas as pd
import streamlit as st

DATA_FILE = "student_dataset.csv"  # the CSV is the database
COLUMNS = ["Roll_No", "Name", "Gender", "Marks", "City", "Department", "Course"]
GENDERS = ["Male", "Female", "Other"]


def centered(df):
    """Return a styled DataFrame with centered headers and cells."""
    return (df.style
            .set_properties(**{"text-align": "center"})
            .set_table_styles([{"selector": "th",
                                "props": [("text-align", "center")]}]))


class Student:
    """One student record."""

    def __init__(self, roll_no, name, gender, marks, city, department, course):
        self.roll_no = str(roll_no).strip()
        self.name = str(name).strip()
        self.gender = gender
        self.marks = int(marks)
        self.city = str(city).strip()
        self.department = str(department).strip()
        self.course = str(course).strip()

    def validate(self):
        if not self.roll_no or not self.name:
            raise ValueError("Roll number and name are required.")
        if not 0 <= self.marks <= 100:
            raise ValueError("Marks must be between 0 and 100.")

    def to_dict(self):
        return {
            "Roll_No": self.roll_no, "Name": self.name, "Gender": self.gender,
            "Marks": self.marks, "City": self.city,
            "Department": self.department, "Course": self.course,
        }

    @classmethod
    def from_row(cls, row):
        return cls(row["Roll_No"], row["Name"], row["Gender"], row["Marks"],
                   row["City"], row["Department"], row["Course"])


class StudentRepository:
    """CSV-backed storage. Every change is written back to the CSV file."""

    def __init__(self, path=DATA_FILE):
        self.path = path
        try:
            self.df = pd.read_csv(path, dtype={"Roll_No": str})
        except FileNotFoundError:
            self.df = pd.DataFrame(columns=COLUMNS)

    def _commit(self):
        self.df.to_csv(self.path, index=False)

    def exists(self, roll_no):
        return (self.df["Roll_No"] == roll_no).any()

    def get(self, roll_no):
        match = self.df[self.df["Roll_No"] == roll_no]
        return Student.from_row(match.iloc[0]) if not match.empty else None

    def add(self, student):
        student.validate()
        if self.exists(student.roll_no):
            raise ValueError(f"Roll number {student.roll_no} already exists.")
        new_row = pd.DataFrame([student.to_dict()])
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self._commit()

    def update(self, roll_no, student):
        student.validate()
        if not self.exists(roll_no):
            raise ValueError("Student not found.")
        idx = self.df.index[self.df["Roll_No"] == roll_no][0]
        for col, val in student.to_dict().items():
            self.df.loc[idx, col] = val
        self._commit()

    def delete(self, roll_no):
        if not self.exists(roll_no):
            raise ValueError("Student not found.")
        self.df = self.df[self.df["Roll_No"] != roll_no].reset_index(drop=True)
        self._commit()

    def search(self, keyword):
        keyword = keyword.strip().lower()
        if not keyword:
            return self.df
        cols = ["Roll_No", "Name", "City", "Department", "Course"]
        mask = self.df[cols].astype(str).apply(
            lambda c: c.str.lower().str.contains(keyword, regex=False)).any(axis=1)
        return self.df[mask]

    def department_summary(self):
        return (self.df.groupby("Department")["Marks"]
                .agg(students="count", average="mean", highest="max", lowest="min")
                .round(2))


# ---------- Pages ----------
def page_dashboard(repo):
    df = repo.df
    c1, c2, c3 = st.columns(3)
    c1.metric("Total students", len(df))
    c2.metric("Average marks", f"{df['Marks'].mean():.2f}" if len(df) else "—")
    c3.metric("Highest marks", int(df["Marks"].max()) if len(df) else "—")

    summary = repo.department_summary()
    st.subheader("Department-wise performance")
    st.table(centered(summary))  # st.table fills the full width
    st.bar_chart(summary["average"])


def page_view(repo):
    st.subheader("View and search students")
    keyword = st.text_input("Search by roll no, name, city, department or course")
    results = repo.search(keyword)
    st.caption(f"{len(results)} record(s) found")
    st.dataframe(centered(results), hide_index=True, use_container_width=True)


def page_add(repo):
    st.subheader("Add student")
    with st.form("add_form", clear_on_submit=True):
        left, right = st.columns(2)
        with left:
            roll = st.text_input("Roll No")
            name = st.text_input("Name")
            gender = st.selectbox("Gender", GENDERS)
            marks = st.number_input("Marks", min_value=0, max_value=100, value=0)
        with right:
            city = st.text_input("City")
            department = st.text_input("Department")
            course = st.text_input("Course")
        submitted = st.form_submit_button("Add student", use_container_width=True)

    if submitted:
        try:
            repo.add(Student(roll, name, gender, marks, city, department, course))
            st.success("Student added and saved to the CSV.")
        except ValueError as e:
            st.error(str(e))


def page_update(repo):
    st.subheader("Update student")
    if repo.df.empty:
        st.info("No students to update.")
        return

    names = dict(zip(repo.df["Roll_No"], repo.df["Name"]))
    roll = st.selectbox("Select roll number", list(names),
                        format_func=lambda r: f"{r} — {names[r]}")
    s = repo.get(roll)

    with st.form(f"update_form_{roll}"):
        left, right = st.columns(2)
        with left:
            st.text_input("Roll No (cannot be changed)", value=s.roll_no, disabled=True)
            name = st.text_input("Name", value=s.name)
            gender = st.selectbox("Gender", GENDERS,
                                  index=GENDERS.index(s.gender) if s.gender in GENDERS else 0)
            marks = st.number_input("Marks", min_value=0, max_value=100, value=s.marks)
        with right:
            city = st.text_input("City", value=s.city)
            department = st.text_input("Department", value=s.department)
            course = st.text_input("Course", value=s.course)
        submitted = st.form_submit_button("Save changes", use_container_width=True)

    if submitted:
        try:
            repo.update(roll, Student(roll, name, gender, marks, city, department, course))
            st.success("Record updated and saved to the CSV.")
        except ValueError as e:
            st.error(str(e))


def page_delete(repo):
    st.subheader("Delete student")
    if repo.df.empty:
        st.info("No students to delete.")
        return

    names = dict(zip(repo.df["Roll_No"], repo.df["Name"]))
    roll = st.selectbox("Select roll number", list(names),
                        format_func=lambda r: f"{r} — {names[r]}")
    st.table(centered(repo.df[repo.df["Roll_No"] == roll]))

    confirm = st.checkbox("I confirm I want to delete this record")
    if st.button("Delete student", type="primary", disabled=not confirm):
        try:
            repo.delete(roll)
            st.success(f"Student {roll} deleted.")
        except ValueError as e:
            st.error(str(e))


def main():
    st.set_page_config(page_title="Student Management System", layout="wide")
    st.title("🎓 Student Management System")

    repo = StudentRepository(DATA_FILE)  # reloads the CSV on every interaction
    pages = {
        "Dashboard": page_dashboard,
        "View & Search": page_view,
        "Add Student": page_add,
        "Update Student": page_update,
        "Delete Student": page_delete,
    }
    choice = st.sidebar.radio("Menu", list(pages))
    st.sidebar.caption(f"Database: {DATA_FILE} ({len(repo.df)} records)")
    pages[choice](repo)


if __name__ == "__main__":
    main()