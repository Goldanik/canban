import sys
import random
import uuid
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
    QLineEdit,
    QFrame, QInputDialog,
)
from PyQt5.QtCore import Qt, QMimeData, QRect, QPoint
from PyQt5.QtGui import QDrag, QPixmap
from PyQt5.QtCore import QTimer


class DraggableLineEdit(QLineEdit):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("background-color: lightblue; border: 1px solid black; border-radius: 5px; padding: 5px;")
        self.setFixedWidth(150)
        self.parent_area = parent
        self.previous_parent_area = None
        self.id = uuid.uuid4()  # Генерируем уникальный ID
        self.setReadOnly(True)  # Отключаем прямое редактирование
        self.drag_timer = QTimer(self)  # Таймер для перетаскивания
        self.drag_timer.setInterval(1000)  # 1 секунда
        self.drag_timer.timeout.connect(self.start_drag)  # Обработчик таймера
        self.is_dragging = False  # Флаг для отслеживания перетаскивания
        self.click_count = 0  # Счетчик кликов для обработки двойного клика

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_timer.start()  # Запускаем таймер при зажатии кнопки мыши
            self.start_pos = event.pos()  # Сохраняем начальную позицию клика

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_timer.stop()  # Останавливаем таймер при отпускании кнопки
            if not self.is_dragging:  # Если перетаскивание не началось
                if (event.pos() - self.start_pos).manhattanLength() < 5:  # Проверяем, был ли это клик (не движение)
                    self.click_count += 1  # Увеличиваем счетчик кликов
                    if self.click_count == 1:
                        # Запускаем таймер для проверки двойного клика
                        QTimer.singleShot(200, self.check_double_click)

    def check_double_click(self):
        if self.click_count == 1:
            # Это был одиночный клик, ничего не делаем
            self.click_count = 0  # Сбрасываем счетчик
        elif self.click_count >= 2:
            # Это был двойной клик
            self.mouseDoubleClickEvent(None)
            self.click_count = 0  # Сбрасываем счетчик

    def mouseDoubleClickEvent(self, event):
        # Открываем QInputDialog для редактирования текста
        new_text, ok = QInputDialog.getText(self, "Редактирование заметки", "Введите новый текст:", text=self.text())
        if ok and new_text:
            self.setText(new_text)

    def start_drag(self):
        self.drag_timer.stop()  # Останавливаем таймер
        self.is_dragging = True  # Начинаем перетаскивание
        pixmap = self.grab()
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"{self.id};{self.text()}")  # Сохраняем ID и текст
        drag.setMimeData(mime_data)
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.start_pos)
        self.previous_parent_area = self.parent_area
        self.hide()
        drag_result = drag.exec_(Qt.MoveAction)
        if drag_result == Qt.MoveAction:
            self.parent_area = None
        else:
            self.show()
            self.parent_area = self.previous_parent_area
        self.is_dragging = False  # Завершаем перетаскивание

    def setParentArea(self, new_parent):
        self.parent_area = new_parent

class KanbanColumn(QFrame):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background-color: #e0e0e0; border: 1px solid #cccccc;")
        self.setMinimumWidth(200)
        self.setAcceptDrops(True)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        title = QLineEdit(name)
        title.setReadOnly(True)
        title.setStyleSheet("font-weight: bold; background-color: #d0d0d0;")
        self.layout().addWidget(title)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            # Получаем ID и текст из mimeData
            id_text = event.mimeData().text().split(";")
            if len(id_text) == 2:
              id = uuid.UUID(id_text[0])
              text = id_text[1]
            else:
              return

            # Находим виджет по ID
            for child in self.parent().findChildren(DraggableLineEdit):
                if child.id == id:
                    # Удаляем виджет из предыдущего родителя
                    if child.previous_parent_area:
                        if isinstance(child.previous_parent_area, KanbanColumn):
                            layout = child.previous_parent_area.layout()
                            for i in reversed(range(layout.count())):
                                item = layout.itemAt(i)
                                if item.widget() == child:
                                    layout.removeWidget(child)
                                    break
                        elif isinstance(child.previous_parent_area, IdeaContainer):
                            child.setParent(None)
                    # Добавляем виджет в текущий столбец
                    child.setParent(self)
                    child.setParentArea(self)
                    self.layout().addWidget(child)
                    child.show()
                    event.accept()
                    return
            # Если виджет не найден, создаем новый
            idea = DraggableLineEdit(text, self)
            idea.id = id
            idea.setParentArea(self)
            self.layout().addWidget(idea)
            event.accept()
        else:
            event.ignore()


class IdeaContainer(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc;")
        self.setAcceptDrops(True)
        self.setLayout(QVBoxLayout())
        self.resize(800, 400)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            id_text = event.mimeData().text().split(";")
            if len(id_text) == 2:
                id = uuid.UUID(id_text[0])
                text = id_text[1]
            else:
                return
            for child in self.parent().findChildren(DraggableLineEdit):
                if child.id == id:
                    # Обновляем текст виджета
                    child.setText(text)

                    if child.previous_parent_area:
                        if isinstance(child.previous_parent_area, KanbanColumn):
                            layout = child.previous_parent_area.layout()
                            for i in reversed(range(layout.count())):
                                item = layout.itemAt(i)
                                if item.widget() == child:
                                    layout.removeWidget(child)
                                    break
                        elif isinstance(child.previous_parent_area, IdeaContainer):
                            child.setParent(None)
                    child.setParent(self)
                    child.setParentArea(self)
                    self.place_idea_randomly(child)
                    event.accept()
                    return

            idea = DraggableLineEdit(text, self)
            idea.id = id
            idea.setParentArea(self)
            self.place_idea_randomly(idea)
            event.accept()
        else:
            event.ignore()

    def place_idea_randomly(self, idea):
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(0, self.width() - idea.width())
            y = random.randint(0, self.height() - idea.height())
            rect = QRect(x, y, idea.width(), idea.height())
            if not any(isinstance(child, QWidget) and rect.intersects(child.geometry()) for child in self.children()):
                idea.setGeometry(rect)
                idea.show()
                return
        idea.setGeometry(0, 0, idea.width(), idea.height())
        idea.show()


class KanbanApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kanban Board")
        self.setGeometry(100, 100, 1200, 800)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        self.kanban_frame = QFrame()
        self.kanban_frame.setFrameShape(QFrame.StyledPanel)
        self.kanban_frame.setFixedHeight(self.height() // 3)
        self.kanban_layout = QHBoxLayout()
        self.kanban_frame.setLayout(self.kanban_layout)
        main_layout.addWidget(self.kanban_frame)

        self.idea_frame = QFrame()
        self.idea_frame.setFrameShape(QFrame.StyledPanel)
        self.idea_frame.setStyleSheet("background-color: #f0f0f0;")
        self.idea_frame.setMinimumHeight(self.height() * 2 // 3)
        self.idea_frame_layout = QVBoxLayout()
        self.idea_frame.setLayout(self.idea_frame_layout)
        main_layout.addWidget(self.idea_frame)

        self.columns = []
        for column_name in ["To Do", "In Progress", "Done"]:
            self.add_kanban_column(column_name)

        add_idea_button = QPushButton("Добавить идею")
        add_idea_button.clicked.connect(self.add_idea)
        self.idea_frame_layout.addWidget(add_idea_button)

        self.idea_container = IdeaContainer(self.idea_frame)
        self.idea_frame_layout.addWidget(self.idea_container)

    def add_kanban_column(self, name):
        column = KanbanColumn(name, self.kanban_frame)
        self.kanban_layout.addWidget(column)
        self.columns.append(column)

    def add_idea(self):
      # Запрашиваем текст новой идеи
      text, ok = QInputDialog.getText(self, "Новая идея", "Введите текст идеи:")
      if ok and text:
        idea = DraggableLineEdit(text, self.idea_container)
        idea.parent_area = self.idea_container
        self.idea_container.place_idea_randomly(idea)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KanbanApp()
    window.show()
    sys.exit(app.exec_())