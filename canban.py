import sys
import random
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
    QLineEdit,
    QFrame,
)
from PyQt5.QtCore import Qt, QMimeData, QRect, QPoint
from PyQt5.QtGui import QDrag, QPixmap


class DraggableLineEdit(QLineEdit):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("background-color: lightblue; border: 1px solid black; border-radius: 5px; padding: 5px;")
        self.setFixedWidth(150)
        self.parent_area = parent  # Сохраняем ссылку на текущего родителя (канбан-столбец или поле идей)
        self.previous_parent_area = None  # Добавляем ссылку на предыдущего родителя

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Создаем изображение (pixmap) текущего виджета
            pixmap = self.grab()

            # Настраиваем объект для перетаскивания
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.text())
            drag.setMimeData(mime_data)

            # Устанавливаем изображение для перетаскивания
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())

            # Сохраняем ссылку на текущего родителя перед началом перетаскивания
            self.previous_parent_area = self.parent_area

            # Удаляем виджет из текущего родителя при начале перетаскивания
            self.hide()  # Скрываем виджет во время перетаскивания
            drag_result = drag.exec_(Qt.MoveAction)
            if drag_result == Qt.MoveAction:
                self.parent_area = None  # Удаляем ссылку на родителя после успешного перемещения
            else:
                self.show()  # Если перетаскивание отменено, показываем обратно
                self.parent_area = self.previous_parent_area  # Возвращаем ссылку на предыдущего родителя

    def setParentArea(self, new_parent):
        self.parent_area = new_parent


class KanbanColumn(QFrame):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background-color: #e0e0e0; border: 1px solid #cccccc;")
        self.setMinimumWidth(200)
        self.setAcceptDrops(True)  # Включаем возможность сброса
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        # Добавляем заголовок столбца
        title = QLineEdit(name)
        title.setReadOnly(True)
        title.setStyleSheet("font-weight: bold; background-color: #d0d0d0;")
        self.layout().addWidget(title)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()  # Разрешаем перетаскивание
        else:
            event.ignore()  # Игнорируем неподходящие данные

    def dropEvent(self, event):
        if event.mimeData().hasText():
            # Получаем текст перетаскиваемой идеи
            text = event.mimeData().text()

            # Проверяем, есть ли уже виджет с этим текстом
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if isinstance(widget, QLineEdit) and widget.text() == text:
                    event.ignore()  # Игнорируем сброс, если идея уже здесь
                    return

            # Находим виджет по тексту и перемещаем его в текущий столбец
            for child in self.parent().findChildren(DraggableLineEdit):
                if child.text() == text:
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
                    child.setParentArea(self)  # Обновляем ссылку на родителя
                    self.layout().addWidget(child)
                    child.show()
                    event.accept()  # Завершаем операцию
                    return

            # Если виджет не найден, создаем новый
            idea = DraggableLineEdit(text, self)
            idea.setParentArea(self)  # Указываем, что столбец - новый родитель
            self.layout().addWidget(idea)
            event.accept()  # Завершаем операцию
        else:
            event.ignore()


class IdeaContainer(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc;")
        self.setAcceptDrops(True)  # Включаем возможность сброса
        self.setLayout(QVBoxLayout())
        self.resize(800, 400)  # Размер зоны идей

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()  # Разрешаем перетаскивание
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            # Получаем текст перетаскиваемой идеи
            text = event.mimeData().text()

            # Проверяем, есть ли уже виджет с этим текстом
            for child in self.children():
                if isinstance(child, DraggableLineEdit) and child.text() == text:
                    event.ignore()  # Игнорируем сброс, если идея уже здесь
                    return

            # Находим виджет по тексту и перемещаем его в контейнер идей
            for child in self.parent().findChildren(DraggableLineEdit):
                if child.text() == text:
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

                    # Добавляем виджет в контейнер идей
                    child.setParent(self)
                    child.setParentArea(self)  # Обновляем ссылку на родителя
                    self.place_idea_randomly(child)
                    event.accept()  # Завершаем операцию
                    return

            # Если виджет не найден, создаем новый
            idea = DraggableLineEdit(text, self)
            idea.setParentArea(self)  # Указываем, что идея принадлежит полю идей
            self.place_idea_randomly(idea)
            event.accept()  # Завершаем операцию
        else:
            event.ignore()

    def place_idea_randomly(self, idea):
        max_attempts = 100  # Максимальное количество попыток разместить идею
        for _ in range(max_attempts):
            x = random.randint(0, self.width() - idea.width())
            y = random.randint(0, self.height() - idea.height())

            # Проверяем пересечение с другими виджетами
            rect = QRect(x, y, idea.width(), idea.height())
            if not any(isinstance(child, QWidget) and rect.intersects(child.geometry()) for child in self.children()):
                idea.setGeometry(rect)
                idea.show()
                return

        # Если не удалось найти место, ставим в верхнем левом углу
        idea.setGeometry(0, 0, idea.width(), idea.height())
        idea.show()


class KanbanApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kanban Board")
        self.setGeometry(100, 100, 1200, 800)

        # Главный виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Верхняя часть (столбцы канбан)
        self.kanban_frame = QFrame()
        self.kanban_frame.setFrameShape(QFrame.StyledPanel)
        self.kanban_frame.setFixedHeight(self.height() // 3)
        self.kanban_layout = QHBoxLayout()
        self.kanban_frame.setLayout(self.kanban_layout)
        main_layout.addWidget(self.kanban_frame)

        # Нижняя часть (идеи)
        self.idea_frame = QFrame()
        self.idea_frame.setFrameShape(QFrame.StyledPanel)
        self.idea_frame.setStyleSheet("background-color: #f0f0f0;")
        self.idea_frame.setMinimumHeight(self.height() * 2 // 3)
        self.idea_frame_layout = QVBoxLayout()
        self.idea_frame.setLayout(self.idea_frame_layout)
        main_layout.addWidget(self.idea_frame)

        # Столбцы канбан
        self.columns = []
        for column_name in ["To Do", "In Progress", "Done"]:
            self.add_kanban_column(column_name)

        # Кнопка добавления идей
        add_idea_button = QPushButton("Добавить идею")
        add_idea_button.clicked.connect(self.add_idea)
        self.idea_frame_layout.addWidget(add_idea_button)

        # Контейнер для текстовых блоков (идей)
        self.idea_container = IdeaContainer(self.idea_frame)
        self.idea_frame_layout.addWidget(self.idea_container)

    def add_kanban_column(self, name):
        # Создаем новый столбец
        column = KanbanColumn(name, self.kanban_frame)
        self.kanban_layout.addWidget(column)
        self.columns.append(column)

    def add_idea(self):
        # Создаем новый текстовый блок
        idea = DraggableLineEdit(f"Идея {len(self.idea_container.children()) + 1}", self.idea_container)
        idea.parent_area = self.idea_container
        self.idea_container.place_idea_randomly(idea)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KanbanApp()
    window.show()
    sys.exit(app.exec_())