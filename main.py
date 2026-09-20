import sqlite3
import csv
from datetime import date
from pathlib import Path

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window


APP_DIR = Path(App.get_running_app().user_data_dir) if App.get_running_app() else Path(".")
DB_FILE = APP_DIR / "attendance.db"


def get_connection():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS learners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            class_name TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id INTEGER NOT NULL,
            att_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (learner_id) REFERENCES learners(id),
            UNIQUE (learner_id, att_date)
        )
    """)

    cur.execute("SELECT COUNT(*) FROM learners")
    if cur.fetchone()[0] == 0:
        sample = [
            ("A101", "Tadiwa Moyo", "4A"),
            ("A102", "Rufaro Ncube", "4A"),
            ("A103", "Blessing Chikafu", "4A"),
            ("A104", "Nyasha Dube", "4A"),
        ]
        cur.executemany(
            "INSERT INTO learners(admission_no, name, class_name) VALUES (?, ?, ?)",
            sample
        )

    conn.commit()
    conn.close()


def popup(title, message):
    box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
    box.add_widget(Label(text=message))
    close = Button(text="OK", size_hint_y=None, height=dp(45))
    box.add_widget(close)

    p = Popup(title=title, content=box, size_hint=(0.85, 0.35))
    close.bind(on_release=p.dismiss)
    p.open()


class LoginScreen(Screen):
    def on_enter(self):
        self.clear_widgets()

        root = BoxLayout(
            orientation="vertical",
            padding=dp(25),
            spacing=dp(12)
        )

        root.add_widget(Label(
            text="STUDENT ATTENDANCE SYSTEM",
            font_size="22sp",
            bold=True,
            size_hint_y=None,
            height=dp(60)
        ))

        root.add_widget(Label(
            text="Teacher Login",
            font_size="18sp",
            size_hint_y=None,
            height=dp(40)
        ))

        self.username = TextInput(
            hint_text="Username",
            multiline=False,
            size_hint_y=None,
            height=dp(50)
        )
        root.add_widget(self.username)

        self.password = TextInput(
            hint_text="Password",
            password=True,
            multiline=False,
            size_hint_y=None,
            height=dp(50)
        )
        root.add_widget(self.password)

        login = Button(
            text="LOGIN",
            size_hint_y=None,
            height=dp(55)
        )
        login.bind(on_release=self.login)
        root.add_widget(login)

        root.add_widget(Label(
            text="Default: teacher / 1234",
            font_size="12sp"
        ))

        self.add_widget(root)

    def login(self, *_):
        if self.username.text.strip() == "teacher" and self.password.text == "1234":
            self.manager.current = "home"
        else:
            popup("Login Failed", "Incorrect username or password.")


class HomeScreen(Screen):
    def on_enter(self):
        self.clear_widgets()

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12)
        )

        root.add_widget(Label(
            text="Attendance Dashboard",
            font_size="24sp",
            bold=True,
            size_hint_y=None,
            height=dp(60)
        ))

        buttons = [
            ("Mark Attendance", "attendance"),
            ("Reports / Search", "reports"),
            ("Manage Learners", "learners"),
        ]

        for text, screen_name in buttons:
            btn = Button(
                text=text,
                size_hint_y=None,
                height=dp(60)
            )
            btn.bind(
                on_release=lambda _, s=screen_name:
                setattr(self.manager, "current", s)
            )
            root.add_widget(btn)

        logout = Button(
            text="Logout",
            size_hint_y=None,
            height=dp(50)
        )
        logout.bind(
            on_release=lambda *_:
            setattr(self.manager, "current", "login")
        )
        root.add_widget(logout)

        self.add_widget(root)


class AttendanceScreen(Screen):
    def on_enter(self):
        self.build()

    def build(self):
        self.clear_widgets()

        root = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        today = date.today().isoformat()

        root.add_widget(Label(
            text=f"Attendance - {today}",
            font_size="20sp",
            bold=True,
            size_hint_y=None,
            height=dp(45)
        ))

        scroll = ScrollView()
        container = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None
        )
        container.bind(minimum_height=container.setter("height"))

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, admission_no, name, class_name
            FROM learners
            ORDER BY class_name, name
        """)
        learners = cur.fetchall()

        cur.execute("""
            SELECT learner_id, status
            FROM attendance
            WHERE att_date = ?
        """, (today,))
        existing = dict(cur.fetchall())
        conn.close()

        self.spinners = {}

        for learner_id, adm, name, class_name in learners:
            row = BoxLayout(
                size_hint_y=None,
                height=dp(65),
                spacing=dp(5)
            )

            label = Label(
                text=f"{adm}\n{name}\nClass: {class_name}",
                halign="left",
                valign="middle"
            )
            label.bind(size=lambda obj, _: setattr(
                obj, "text_size", obj.size
            ))

            spinner = Spinner(
                text=existing.get(learner_id, "Present"),
                values=("Present", "Absent", "Late"),
                size_hint_x=0.38
            )

            self.spinners[learner_id] = spinner
            row.add_widget(label)
            row.add_widget(spinner)
            container.add_widget(row)

        scroll.add_widget(container)
        root.add_widget(scroll)

        save = Button(
            text="SAVE ATTENDANCE",
            size_hint_y=None,
            height=dp(55)
        )
        save.bind(on_release=self.save)
        root.add_widget(save)

        back = Button(
            text="Back",
            size_hint_y=None,
            height=dp(45)
        )
        back.bind(on_release=lambda *_: setattr(
            self.manager, "current", "home"
        ))
        root.add_widget(back)

        self.add_widget(root)

    def save(self, *_):
        today = date.today().isoformat()

        conn = get_connection()
        cur = conn.cursor()

        for learner_id, spinner in self.spinners.items():
            cur.execute("""
                INSERT INTO attendance
                (learner_id, att_date, status)
                VALUES (?, ?, ?)
                ON CONFLICT(learner_id, att_date)
                DO UPDATE SET status = excluded.status
            """, (learner_id, today, spinner.text))

        conn.commit()
        conn.close()

        popup("Saved", f"Attendance for {today} was saved.")


class ReportsScreen(Screen):
    def on_enter(self):
        self.build()

    def build(self):
        self.clear_widgets()

        root = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        top = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(5)
        )

        self.search = TextInput(
            hint_text="Date, name, admission no. or class",
            multiline=False
        )
        top.add_widget(self.search)

        search_btn = Button(
            text="Search",
            size_hint_x=0.25
        )
        search_btn.bind(on_release=lambda *_: self.load())
        top.add_widget(search_btn)

        root.add_widget(top)

        self.summary = Label(
            text="",
            size_hint_y=None,
            height=dp(40)
        )
        root.add_widget(self.summary)

        self.scroll = ScrollView()
        self.results = GridLayout(
            cols=1,
            spacing=dp(4),
            size_hint_y=None
        )
        self.results.bind(minimum_height=self.results.setter("height"))
        self.scroll.add_widget(self.results)
        root.add_widget(self.scroll)

        export = Button(
            text="Export CSV",
            size_hint_y=None,
            height=dp(50)
        )
        export.bind(on_release=self.export_csv)
        root.add_widget(export)

        back = Button(
            text="Back",
            size_hint_y=None,
            height=dp(45)
        )
        back.bind(on_release=lambda *_: setattr(
            self.manager, "current", "home"
        ))
        root.add_widget(back)

        self.add_widget(root)
        self.load()

    def load(self):
        term = self.search.text.strip() if hasattr(self, "search") else ""

        conn = get_connection()
        cur = conn.cursor()

        query = """
            SELECT a.att_date, l.admission_no, l.name,
                   l.class_name, a.status
            FROM attendance a
            JOIN learners l ON a.learner_id = l.id
        """

        params = ()

        if term:
            query += """
                WHERE a.att_date = ?
                OR l.name LIKE ?
                OR l.admission_no LIKE ?
                OR l.class_name LIKE ?
            """
            params = (
                term,
                f"%{term}%",
                f"%{term}%",
                f"%{term}%"
            )

        query += " ORDER BY a.att_date DESC, l.name ASC"

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        self.results.clear_widgets()

        present = absent = late = 0

        for row in rows:
            if row[4] == "Present":
                present += 1
            elif row[4] == "Absent":
                absent += 1
            elif row[4] == "Late":
                late += 1

            self.results.add_widget(Label(
                text=f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}",
                size_hint_y=None,
                height=dp(45),
                halign="left",
                valign="middle"
            ))

        self.summary.text = (
            f"Records: {len(rows)}   "
            f"Present: {present}   "
            f"Absent: {absent}   "
            f"Late: {late}"
        )

        self.current_rows = rows

    def export_csv(self, *_):
        if not getattr(self, "current_rows", []):
            popup("No Data", "There are no attendance records to export.")
            return

        path = APP_DIR / f"attendance_report_{date.today().isoformat()}.csv"

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Date", "Admission No", "Name", "Class", "Status"
            ])
            writer.writerows(self.current_rows)

        popup(
            "CSV Exported",
            f"Report saved inside the app folder:\n{path}"
        )


class LearnersScreen(Screen):
    def on_enter(self):
        self.build()

    def build(self):
        self.clear_widgets()

        root = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        root.add_widget(Label(
            text="Manage Learners",
            font_size="21sp",
            bold=True,
            size_hint_y=None,
            height=dp(50)
        ))

        form = GridLayout(
            cols=2,
            size_hint_y=None,
            height=dp(170),
            spacing=dp(6)
        )

        self.admission = TextInput(
            hint_text="Admission number",
            multiline=False
        )
        self.name = TextInput(
            hint_text="Learner name",
            multiline=False
        )
        self.class_name = TextInput(
            hint_text="Class",
            multiline=False
        )

        form.add_widget(Label(text="Admission No."))
        form.add_widget(self.admission)
        form.add_widget(Label(text="Name"))
        form.add_widget(self.name)
        form.add_widget(Label(text="Class"))
        form.add_widget(self.class_name)

        add = Button(text="Add Learner")
        add.bind(on_release=self.add_learner)

        form.add_widget(Label(text=""))
        form.add_widget(add)

        root.add_widget(form)

        self.scroll = ScrollView()
        self.list_box = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )
        self.list_box.bind(
            minimum_height=self.list_box.setter("height")
        )
        self.scroll.add_widget(self.list_box)

        root.add_widget(self.scroll)

        back = Button(
            text="Back",
            size_hint_y=None,
            height=dp(45)
        )
        back.bind(on_release=lambda *_: setattr(
            self.manager, "current", "home"
        ))
        root.add_widget(back)

        self.add_widget(root)
        self.refresh()

    def refresh(self):
        if not hasattr(self, "list_box"):
            return

        self.list_box.clear_widgets()

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, admission_no, name, class_name
            FROM learners
            ORDER BY class_name, name
        """)

        learners = cur.fetchall()
        conn.close()

        for learner_id, adm, name, class_name in learners:
            row = BoxLayout(
                size_hint_y=None,
                height=dp(55),
                spacing=dp(5)
            )

            row.add_widget(Label(
                text=f"{adm} | {name} | {class_name}"
            ))

            delete = Button(
                text="Delete",
                size_hint_x=0.25
            )
            delete.bind(
                on_release=lambda _, lid=learner_id:
                self.delete_learner(lid)
            )

            row.add_widget(delete)
            self.list_box.add_widget(row)

    def add_learner(self, *_):
        adm = self.admission.text.strip()
        name = self.name.text.strip()
        cls = self.class_name.text.strip()

        if not adm or not name or not cls:
            popup("Missing Information", "Complete all fields.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO learners
                (admission_no, name, class_name)
                VALUES (?, ?, ?)
            """, (adm, name, cls))

            conn.commit()
            conn.close()

            self.admission.text = ""
            self.name.text = ""
            self.class_name.text = ""

            self.refresh()
            popup("Learner Added", f"{name} was added successfully.")

        except sqlite3.IntegrityError:
            popup(
                "Duplicate Admission Number",
                "That admission number already exists."
            )

    def delete_learner(self, learner_id):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT name FROM learners WHERE id = ?",
            (learner_id,)
        )
        result = cur.fetchone()

        if not result:
            conn.close()
            return

        name = result[0]

        cur.execute(
            "DELETE FROM attendance WHERE learner_id = ?",
            (learner_id,)
        )
        cur.execute(
            "DELETE FROM learners WHERE id = ?",
            (learner_id,)
        )

        conn.commit()
        conn.close()

        self.refresh()
        popup("Deleted", f"{name} was deleted.")


class AttendanceApp(App):
    def build(self):
        self.title = "Student Attendance System"

        init_db()

        manager = ScreenManager()

        manager.add_widget(LoginScreen(name="login"))
        manager.add_widget(HomeScreen(name="home"))
        manager.add_widget(AttendanceScreen(name="attendance"))
        manager.add_widget(ReportsScreen(name="reports"))
        manager.add_widget(LearnersScreen(name="learners"))

        manager.current = "login"

        return manager


if __name__ == "__main__":
    AttendanceApp().run()
