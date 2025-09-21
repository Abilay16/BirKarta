# main.py
import json  # ВАЖНО! Этого не было в твоем коде
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock

# Android NFC импорты
from kivy.utils import platform
if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission
    from android import activity

# Настройка окна
Window.clearcolor = (1, 1, 1, 1)

# Демо данные (для тестирования без NFC)
DEMO_DATA = {
    "fio": "АРМАН АХМЕТОВ",
    "certs": [
        {
            "name": "Удостоверение по проверке знаний, правил, норм и инструкций по безопасности и охране труда",
            "date": "24.02.2025",
            "details": {
                "Выдано": "24.02.2025",
                "Должность": "Оператор",
                "Место работы": "ТОО Болашак-Узень",
                "Комментарий": "В том что сдал экзамены на знание Безопасность и охрана труда",
                "Основание": "Приказ №8 от 24.02.2025",
                "Номер протокола": "82",
                "Председатель": "Аяпбергенов А.А.",
                "Члены комиссии": "Джайгулова Ұ., Каржаубаев А."
            }
        },
        {
            "name": "ОРТ ҚАУІПСІЗІГІ",
            "date": "28.02.2025",
            "details": {
                "Выдано": "28.02.2025",
                "Должность": "Оператор",
                "Место работы": "ТОО Болашак-Узень",
                "Комментарий": "В том что сдал экзамены на знание Безопасность и охрана труда",
                "Основание": "Приказ №7 от 20.02.2025",
                "Номер протокола": "81",
                "Председатель": "Кенжебаев Д.Д.",
                "Члены комиссии": "Салимов К., Абдуллин Е."
            }
        }
    ]
}

class CardButton(ButtonBehavior, BoxLayout):
    """
    Кнопка-карточка для отображения сертификата
    Объяснение для новичка:
    - ButtonBehavior делает виджет кликабельным
    - BoxLayout позволяет размещать элементы вертикально
    """
    def __init__(self, cert, idx, open_callback, **kwargs):
        super().__init__(
            orientation='vertical', 
            size_hint_y=None, 
            spacing=4, 
            padding=[18, 10, 10, 8], 
            **kwargs
        )
        
        # Рисуем фон карточки (округлый прямоугольник)
        with self.canvas.before:
            Color(0.96, 0.98, 1, 1)  # Светло-голубой цвет
            self.bg = RoundedRectangle(radius=[22], pos=self.pos, size=self.size)
        
        # Привязываем обновление фона к изменению позиции/размера
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Заголовок сертификата
        title_text = cert.get('name', 'Без названия')
        title = Label(
            text=title_text,
            font_size=15,
            bold=True,
            color=[0, 0, 0, 1],
            halign='left',
            valign='top',
            size_hint_y=None,
            text_size=(Window.width - 110, None)  # Ограничиваем ширину для переноса строк
        )
        # Автоматически подгоняем высоту под текст
        title.bind(texture_size=lambda inst, val: setattr(title, 'height', val[1]))
        self.add_widget(title)

        # Дата выдачи
        date_issued = cert.get('details', {}).get('Выдано', 'Не указано')
        self.add_widget(Label(
            text=f"Выдано: {date_issued}",
            font_size=14,
            color=[0.2, 0.2, 0.2, 1],
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=22
        ))
        
        # Дата окончания
        valid_until = cert.get('date', 'Не указано')
        self.add_widget(Label(
            text=f"Действует до: {valid_until}",
            font_size=14,
            color=[0.2, 0.2, 0.2, 1],
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=22
        ))
        
        # Автоматически подгоняем высоту карточки под содержимое
        self.bind(minimum_height=self.setter('height'))
        
        # Сохраняем callback и индекс для обработки нажатия
        self._open_callback = open_callback
        self._cert_index = idx

    def _update_bg(self, *args):
        """Обновляет позицию и размер фона при изменении карточки"""
        self.bg.pos = self.pos
        self.bg.size = self.size

    def on_press(self):
        """Вызывается при нажатии на карточку"""
        self._open_callback(self._cert_index)

class MainScreen(Screen):
    """
    Главный экран приложения
    Показывает список всех сертификатов работника
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = None  # Здесь будут храниться данные работника
        
        # Основной контейнер
        layout = BoxLayout(
            orientation='vertical', 
            spacing=18, 
            padding=[30, 20, 30, 20]
        )
        
        # Заголовок приложения
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        header.add_widget(Label(
            text='БірКарта', 
            font_size=28, 
            bold=True, 
            color=[0, 0, 0, 1]
        ))
        header.add_widget(Widget(size_hint_x=None, width=40))  # Пустое место справа
        layout.add_widget(header)

        # Имя работника (или инструкция)
        self.name_label = Label(
            text='Поднесите карту к телефону',
            font_size=20,
            bold=True,
            color=[0, 0, 0, 1],
            size_hint_y=None,
            height=36
        )
        layout.add_widget(self.name_label)

        # Прокручиваемый список сертификатов
        self.scroll = ScrollView()
        self.rows = BoxLayout(
            orientation='vertical', 
            spacing=18, 
            size_hint_y=None, 
            padding=[0, 10, 0, 10]
        )
        self.rows.bind(minimum_height=self.rows.setter('height'))
        self.scroll.add_widget(self.rows)
        layout.add_widget(self.scroll)

        self.add_widget(layout)

    def set_data(self, data):
        """
        Устанавливает данные работника и обновляет интерфейс
        data - словарь с информацией о работнике и его сертификатах
        """
        self.data = data
        self.refresh_ui()

    def refresh_ui(self):
        """Обновляет интерфейс после получения новых данных"""
        # Очищаем старый список
        self.rows.clear_widgets()
        
        if not self.data:
            self.name_label.text = 'Поднесите карту к телефону'
            return
        
        # Показываем имя работника
        worker_name = self.data.get('fio', 'Сотрудник')
        self.name_label.text = worker_name
        
        # Добавляем карточки сертификатов
        certificates = self.data.get('certs', [])
        for idx, cert in enumerate(certificates):
            card = CardButton(cert, idx, self.open_detail)
            self.rows.add_widget(card)

    def open_detail(self, cert_index):
        """Открывает детальную информацию о сертификате"""
        if not self.data:
            return
            
        certificates = self.data.get('certs', [])
        if 0 <= cert_index < len(certificates):
            # Получаем ссылку на приложение и показываем детали
            app = App.get_running_app()
            app.show_detail(certificates[cert_index])

class DetailScreen(Screen):
    """
    Экран с детальной информацией о сертификате
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Основной контейнер
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=24)
        
        # Название сертификата
        self.title_label = Label(
            text='',
            font_size=20,
            bold=True,
            color=[0, 0.3, 1, 1],
            halign='center',
            valign='middle',
            text_size=(Window.width - 80, None),
            size_hint_y=None
        )
        self.title_label.bind(texture_size=lambda inst, val: setattr(self.title_label, 'height', val[1]))
        self.layout.add_widget(self.title_label)
        
        # Дата действия
        self.date_label = Label(
            text='',
            font_size=16,
            bold=True,
            color=[0, 0, 0, 1],
            size_hint_y=None,
            height=28
        )
        self.layout.add_widget(self.date_label)
        
        # Прокручиваемая область с деталями
        scroll = ScrollView()
        self.details_box = BoxLayout(
            orientation='vertical', 
            spacing=6, 
            size_hint_y=None
        )
        self.details_box.bind(minimum_height=self.details_box.setter('height'))
        scroll.add_widget(self.details_box)
        self.layout.add_widget(scroll)
        
        # Кнопка "Назад"
        back_btn = Button(
            text="Назад",
            size_hint_y=None,
            height=45,
            background_color=[0, 0.3, 1, 1],
            color=[1, 1, 1, 1]
        )
        back_btn.bind(on_press=self.go_back)
        self.layout.add_widget(back_btn)
        
        self.add_widget(self.layout)

    def set_certificate(self, cert):
        """Устанавливает информацию о сертификате для отображения"""
        # Название
        cert_name = cert.get('name', 'Без названия')
        self.title_label.text = cert_name
        
        # Дата действия
        valid_date = cert.get('date', 'Не указано')
        self.date_label.text = f"Действует до: {valid_date}"
        
        # Очищаем старые детали
        self.details_box.clear_widgets()
        
        # Добавляем детальную информацию
        details = cert.get('details', {})
        for key, value in details.items():
            detail_label = Label(
                text=f"{key}: {value}",
                font_size=15,
                color=[0, 0, 0, 1],
                halign='left',
                valign='top',
                size_hint_y=None,
                text_size=(Window.width - 80, None)
            )
            detail_label.bind(texture_size=lambda inst, val: setattr(detail_label, 'height', val[1]))
            self.details_box.add_widget(detail_label)

    def go_back(self, *args):
        """Возвращается на главный экран"""
        self.manager.current = 'main'

class BirKartaApp(App):
    """
    Главный класс приложения
    """
    def build(self):
        # Создаем менеджер экранов
        self.sm = ScreenManager()
        
        # Создаем экраны
        self.main_screen = MainScreen(name='main')
        self.detail_screen = DetailScreen(name='detail')
        
        # Добавляем экраны в менеджер
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.detail_screen)
        
        # Запрашиваем разрешения для Android
        if platform == 'android':
            try:
                request_permissions([Permission.NFC])
                activity.bind(on_new_intent=self.on_new_intent)
                print("NFC настроен успешно")
            except Exception as e:
                print(f"Ошибка настройки NFC: {e}")
        
        # Загружаем демо данные для тестирования
        # В реальном приложении эта строка не нужна
        Clock.schedule_once(lambda dt: self.main_screen.set_data(DEMO_DATA), 1)
        
        return self.sm

    def show_detail(self, certificate):
        """Показывает детальную информацию о сертификате"""
        self.detail_screen.set_certificate(certificate)
        self.sm.current = 'detail'

    def on_new_intent(self, intent):
        """
        Обработчик NFC событий
        Вызывается когда телефон считывает NFC карту
        """
        if platform != 'android':
            return
        
        try:
            # Импортируем Android классы
            Intent = autoclass('android.content.Intent')
            NfcAdapter = autoclass('android.nfc.NfcAdapter')
            
            # Проверяем тип действия
            action = intent.getAction()
            valid_actions = [
                NfcAdapter.ACTION_NDEF_DISCOVERED,
                NfcAdapter.ACTION_TAG_DISCOVERED,
                NfcAdapter.ACTION_TECH_DISCOVERED
            ]
            
            if action not in valid_actions:
                print(f"Неподдерживаемое NFC действие: {action}")
                return

            # Получаем NDEF сообщения
            raw_msgs = intent.getParcelableArrayExtra(NfcAdapter.EXTRA_NDEF_MESSAGES)
            if raw_msgs is None:
                print("Нет NDEF сообщений")
                return

            # Конвертируем в NdefMessage объекты
            messages = [cast('android.nfc.NdefMessage', msg) for msg in raw_msgs]
            if not messages:
                print("Пустые сообщения")
                return

            # Берем первую запись первого сообщения
            records = messages[0].getRecords()
            if not records or records.length == 0:
                print("Нет записей в сообщении")
                return

            first_record = records[0]
            payload = first_record.getPayload()
            if payload is None:
                print("Пустой payload")
                return

            # Декодируем NDEF Text Record
            # Формат: [status][язык][текст]
            status_byte = payload[0] & 0xFF
            language_length = status_byte & 0x3F
            is_utf16 = (status_byte & 0x80) != 0
            
            # Извлекаем текст (пропускаем статус и язык)
            text_bytes = payload[1 + language_length:]
            
            # Декодируем текст
            encoding = 'utf-16' if is_utf16 else 'utf-8'
            try:
                text_data = bytes(text_bytes).decode(encoding)
            except UnicodeDecodeError:
                # Пробуем UTF-8 как запасной вариант
                text_data = bytes(text_bytes).decode('utf-8', errors='ignore')

            print(f"Считан текст с NFC: {text_data[:100]}...")  # Показываем первые 100 символов

            # Парсим JSON
            try:
                worker_data = json.loads(text_data)
                print("JSON успешно распарсен")
                
                # Обновляем данные в приложении
                self.main_screen.set_data(worker_data)
                self.sm.current = 'main'
                
                print(f"Загружены данные для: {worker_data.get('fio', 'Неизвестно')}")
                
            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга JSON: {e}")
                print(f"Полученный текст: {text_data}")

        except Exception as e:
            print(f"Ошибка обработки NFC: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    BirKartaApp().run()