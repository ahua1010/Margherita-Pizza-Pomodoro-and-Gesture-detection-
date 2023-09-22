import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, \
    QPushButton, QListWidget, QCalendarWidget, QTimeEdit, QDateTimeEdit, QMessageBox
from PyQt5.QtCore import QDate, QTime, QDateTime

class TodoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Todo List App')
        self.layout = QVBoxLayout()

        # Todo input widgets
        self.task_label = QLabel('Task:')
        self.task_input = QLineEdit()
        self.date_time_edit = QDateTimeEdit()
        self.date_time_edit.setDateTime(QDateTime.currentDateTime())

        self.add_button = QPushButton('Add')
        self.add_button.clicked.connect(self.add_task)

        self.edit_button = QPushButton('Edit')
        self.edit_button.clicked.connect(self.edit_task)

        self.delete_button = QPushButton('Delete')
        self.delete_button.clicked.connect(self.delete_task)

        self.task_layout = QHBoxLayout()
        self.task_layout.addWidget(self.task_label)
        self.task_layout.addWidget(self.task_input)

        self.datetime_layout = QHBoxLayout()
        self.datetime_layout.addWidget(self.date_time_edit)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addWidget(self.add_button)
        self.buttons_layout.addWidget(self.edit_button)
        self.buttons_layout.addWidget(self.delete_button)

        # Todo list widget
        self.todo_list = QListWidget()
        self.todo_list.itemClicked.connect(self.load_task)

        # Add the widgets to the main layout
        self.layout.addLayout(self.task_layout)
        self.layout.addLayout(self.datetime_layout)
        self.layout.addLayout(self.buttons_layout)
        self.layout.addWidget(self.todo_list)

        self.setLayout(self.layout)

    def add_task(self):
        task_text = self.task_input.text()
        date_time = self.date_time_edit.dateTime()
        task_datetime_str = date_time.toString('yyyy-MM-dd hh:mm:ss')
        task_text_with_datetime = f'{task_text} (Due: {task_datetime_str})'

        if task_text:
            self.todo_list.addItem(task_text_with_datetime)
            self.task_input.clear()

    def edit_task(self):
        selected_item = self.todo_list.currentItem()
        if selected_item:
            new_task_text = self.task_input.text()
            date_time = self.date_time_edit.dateTime()
            task_datetime_str = date_time.toString('yyyy-MM-dd hh:mm:ss')
            new_task_text_with_datetime = f'{new_task_text} (Due: {task_datetime_str})'

            if new_task_text:
                selected_item.setText(new_task_text_with_datetime)
                self.task_input.clear()

    def delete_task(self):
        selected_item = self.todo_list.currentItem()
        if selected_item:
            confirm_delete = QMessageBox.question(self, 'Delete Task', 'Are you sure you want to delete this task?',
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if confirm_delete == QMessageBox.Yes:
                self.todo_list.takeItem(self.todo_list.row(selected_item))

    def load_task(self, item):
        task_text = item.text().split(' (Due: ')[0]
        self.task_input.setText(task_text)
        date_time_str = item.text().split(' (Due: ')[1][:-1]
        date_time = QDateTime.fromString(date_time_str, 'yyyy-MM-dd hh:mm:ss')
        self.date_time_edit.setDateTime(date_time)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    todo_app = TodoApp()
    todo_app.show()
    sys.exit(app.exec_())