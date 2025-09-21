import json
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

# Android NFC импорты
from kivy.utils import platform
if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission
    from android import activity

# Настройка окна
Window.clearcolor = (1, 1, 1, 1)

class CardButton(ButtonBehavior, BoxLayout):
    """
    Кнопка-карточка для отображения сертификата
    """
    def __init__(self, cert, idx, open_callback, **kwargs):
        super().__init__(
            orientation='vertical', 
            size_hint_y=None, 
            spacing=4, 
            padding=[18, 10, 10, 8], 
            **kwargs
        )
        
        # Рисуем фон карточки
        with self.canvas.before:
            Color(0.96, 0.98, 1, 1)  # Светло-голубой
            self.bg = RoundedRectangle(radius=[22], pos=self.pos, size=self.size)
        
        # Привязываем обновление фона
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
            text_size=(Window.width - 110, None)
        )
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
        
        # Дата окончания с проверкой срока
        valid_until = cert.get('date', 'Не указано')
        date_color = self._get_date_color(valid_until)
        self.add_widget(Label(
            text=f"Действует до: {valid_until}",
            font_size=14,
            color=date_color,
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=22
        ))
        
        self.bind(minimum_height=self.setter('height'))
        self._open_callback = open_callback
        self._cert_index = idx

    def _get_date_color(self, date_str):
        """Определяет цвет даты в зависимости от срока действия"""
        try:
            from datetime import datetime
            # Пробуем распарсить дату в формате дд.мм.гггг
            cert_date = datetime.strptime(date_str, "%d.%m.%Y")
            today = datetime.now()
            days_left = (cert_date - today).days
            
            if days_left < 0:
                return [1, 0, 0, 1]  # Красный - просрочен
            elif days_left < 30:
                return [1, 0.5, 0, 1]  # Оранжевый - скоро истекает
            else:
                return [0.2, 0.2, 0.2, 1]  # Серый - все ок
        except:
            return [0.2, 0.2, 0.2, 1]  # Серый по умолчанию

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def on_press(self):
        self._open_callback(self._cert_index)

class EmptyStateWidget(BoxLayout):
    """Виджет для показа когда нет данных"""
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=20, **kwargs)
        
        # Иконка (используем текст как иконку)
        icon = Label(
            text="📱",
            font_size=80,
            size_hint_y=None,
            height=120
        )
        self.add_widget(icon)
        
        # Основной текст
        main_text = Label(
            text="Поднесите карту к телефону",
            font_size=24,
            bold=True,
            color=[0.3, 0.3, 0.3, 1],
            size_hint_y=None,
            height=40
        )
        self.add_widget(main_text)
        
        # Инструкция
        instruction = Label(
            text="Для считывания данных сотрудника\nподнесите NFC карту к задней\nпанели телефона",
            font_size=16,
            color=[0.5, 0.5, 0.5, 1],
            halign='center',
            size_hint_y=None,
            height=80
        )
        self.add_widget(instruction)

class MainScreen(Screen):
    """Главный экран приложения"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = None
        
        # Основной контейнер
        self.main_layout = BoxLayout(
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
            color=[0, 0, 0, 1],
            halign='left'
        ))
        
        # Статус NFC
        self.nfc_status = Label(
            text='NFC готов',
            font_size=14,
            color=[0, 0.7, 0, 1],
            halign='right',
            size_hint_x=None,
            width=100
        )
        header.add_widget(self.nfc_status)
        self.main_layout.add_widget(header)

        # Контейнер для контента (будет меняться)
        self.content_container = BoxLayout(orientation='vertical')
        self.main_layout.add_widget(self.content_container)
        
        self.add_widget(self.main_layout)
        
        # Показываем пустое состояние по умолчанию
        self.show_empty_state()

    def show_empty_state(self):
        """Показывает экран ожидания карты"""
        self.content_container.clear_widgets()
        empty_widget = EmptyStateWidget()
        self.content_container.add_widget(empty_widget)

    def show_employee_data(self):
        """Показывает данные сотрудника"""
        if not self.data:
            self.show_empty_state()
            return
            
        self.content_container.clear_widgets()
        
        # Имя сотрудника
        name_label = Label(
            text=self.data.get('fio', 'Сотрудник'),
            font_size=20,
            bold=True,
            color=[0, 0, 0, 1],
            size_hint_y=None,
            height=40
        )
        self.content_container.add_widget(name_label)
        
        # Количество сертификатов
        cert_count = len(self.data.get('certs', []))
        count_label = Label(
            text=f"Сертификатов: {cert_count}",
            font_size=16,
            color=[0.5, 0.5, 0.5, 1],
            size_hint_y=None,
            height=30
        )
        self.content_container.add_widget(count_label)
        
        # Прокручиваемый список сертификатов
        scroll = ScrollView()
        rows = BoxLayout(
            orientation='vertical', 
            spacing=18, 
            size_hint_y=None, 
            padding=[0, 10, 0, 10]
        )
        rows.bind(minimum_height=rows.setter('height'))
        
        # Добавляем карточки сертификатов
        certificates = self.data.get('certs', [])
        for idx, cert in enumerate(certificates):
            card = CardButton(cert, idx, self.open_detail)
            rows.add_widget(card)
        
        scroll.add_widget(rows)
        self.content_container.add_widget(scroll)
        
        # Кнопка для очистки (для тестирования)
        clear_button = Button(
            text="Очистить данные",
            size_hint_y=None,
            height=40,
            background_color=[0.8, 0.8, 0.8, 1]
        )
        clear_button.bind(on_press=self.clear_data)
        self.content_container.add_widget(clear_button)

    def set_data(self, data):
        """Устанавливает данные сотрудника"""
        self.data = data
        if data:
            self.show_employee_data()
            self.nfc_status.text = 'Данные загружены'
            self.nfc_status.color = [0, 0.7, 0, 1]
        else:
            self.show_empty_state()
            self.nfc_status.text = 'NFC готов'
            self.nfc_status.color = [0, 0.7, 0, 1]

    def clear_data(self, *args):
        """Очищает данные (для тестирования)"""
        self.set_data(None)

    def open_detail(self, cert_index):
        """Открывает детальную информацию о сертификате"""
        if not self.data:
            return
            
        certificates = self.data.get('certs', [])
        if 0 <= cert_index < len(certificates):
            app = App.get_running_app()
            app.show_detail(certificates[cert_index])

class DetailScreen(Screen):
    """Экран с детальной информацией о сертификате"""
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
        
        # Дата действия с проверкой срока
        valid_date = cert.get('date', 'Не указано')
        date_status = self._get_date_status(valid_date)
        self.date_label.text = f"Действует до: {valid_date} {date_status}"
        
        # Цвет даты в зависимости от статуса
        if "ПРОСРОЧЕН" in date_status:
            self.date_label.color = [1, 0, 0, 1]  # Красный
        elif "скоро истекает" in date_status:
            self.date_label.color = [1, 0.5, 0, 1]  # Оранжевый
        else:
            self.date_label.color = [0, 0.7, 0, 1]  # Зеленый
        
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

    def _get_date_status(self, date_str):
        """Определяет статус сертификата по дате"""
        try:
            from datetime import datetime
            cert_date = datetime.strptime(date_str, "%d.%m.%Y")
            today = datetime.now()
            days_left = (cert_date - today).days
            
            if days_left < 0:
                return "- ПРОСРОЧЕН!"
            elif days_left < 30:
                return f"- скоро истекает ({days_left} дн.)"
            else:
                return "- действителен"
        except:
            return ""

    def go_back(self, *args):
        """Возвращается на главный экран"""
        self.manager.current = 'main'

class BirKartaApp(App):
    """Главный класс приложения"""
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
                
                # Обновляем статус NFC
                self.main_screen.nfc_status.text = 'NFC активен'
                self.main_screen.nfc_status.color = [0, 0.7, 0, 1]
                
            except Exception as e:
                print(f"Ошибка настройки NFC: {e}")
                self.main_screen.nfc_status.text = 'NFC ошибка'
                self.main_screen.nfc_status.color = [1, 0, 0, 1]
        else:
            # На компьютере показываем что NFC недоступен
            self.main_screen.nfc_status.text = 'Только Android'
            self.main_screen.nfc_status.color = [0.5, 0.5, 0.5, 1]
        
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
            print("NFC событие обнаружено!")
            
            # Обновляем статус
            self.main_screen.nfc_status.text = 'Считывание...'
            self.main_screen.nfc_status.color = [1, 0.5, 0, 1]  # Оранжевый
            
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
                self.main_screen.nfc_status.text = 'Неверная карта'
                self.main_screen.nfc_status.color = [1, 0, 0, 1]
                return

            # Получаем NDEF сообщения
            raw_msgs = intent.getParcelableArrayExtra(NfcAdapter.EXTRA_NDEF_MESSAGES)
            if raw_msgs is None:
                print("Нет NDEF сообщений")
                self.main_screen.nfc_status.text = 'Пустая карта'
                self.main_screen.nfc_status.color = [1, 0, 0, 1]
                return

            # Конвертируем в NdefMessage объекты
            messages = [cast('android.nfc.NdefMessage', msg) for msg in raw_msgs]
            if not messages:
                print("Пустые сообщения")
                self.main_screen.nfc_status.text = 'Нет данных'
                self.main_screen.nfc_status.color = [1, 0, 0, 1]
                return

            # Берем первую запись первого сообщения
            records = messages[0].getRecords()
            if not records or records.length == 0:
                print("Нет записей в сообщении")
                self.main_screen.nfc_status.text = 'Нет записей'
                self.main_screen.nfc_status.color = [1, 0, 0, 1]
                return

            first_record = records[0]
            payload = first_record.getPayload()
            if payload is None:
                print("Пустой payload")
                self.main_screen.nfc_status.text = 'Пустые данные'
                self.main_screen.nfc_status.color = [1, 0, 0, 1]
                return

            # Декодируем NDEF Text Record
            status_byte = payload[0] & 0xFF
            language_length = status_byte & 0x3F
            is_utf16 = (status_byte & 0x80) != 0
            
            # Извлекаем текст
            text_bytes = payload[1 + language_length:]
            
            # Декодируем текст
            encoding = 'utf-16' if is_utf16 else 'utf-8'
            try:
                text_data = bytes(text_bytes).decode(encoding)
            except UnicodeDecodeError:
                text_data = bytes(text_bytes).decode('utf-8', errors='ignore')

            print(f"Считан текст с NFC: {text_data[:100]}...")

            # Парсим JSON
            try:
                worker_data = json.loads(text_data)
                print("JSON успешно распарсен")
                
                # Проверяем структуру данных
                if not isinstance(worker_data, dict):
                    raise ValueError("Неверная структура данных")
                
                if 'fio' not in worker_data:
                    raise ValueError("Отсутствует ФИО")
                
                if 'certs' not in worker_data:
                    raise ValueError("Отсутствуют сертификаты")
                
                # Обновляем данные в приложении
                self.main_screen.set_data(worker_data)
                self.sm.current = 'main'
                
                # Обновляем статус
                self.main_screen.nfc_status.text = 'Данные загружены'
                self.main_screen.nfc_status.color = [0, 0.7, 0, 1]
                
                print(f"Загружены данные для: {worker_data.get('fio', 'Неизвестно')}")
                
            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга JSON: {e}")
                print(f"Полученный текст: {text_data}")
                self.main_screen.nfc_status.text = 'Неверный формат'
                self.main_screen.nfc_status.color = [1, 0, 0, 1]
                
            except ValueError as e:
                print(f"Ошибка данных: {e}")
                self.main_screen.nfc_status.text = str(e)
                self.main_screen.nfc_status.color = [1, 0, 0, 1]

        except Exception as e:
            print(f"Ошибка обработки NFC: {e}")
            import traceback
            traceback.print_exc()
            self.main_screen.nfc_status.text = 'Ошибка NFC'
            self.main_screen.nfc_status.color = [1, 0, 0, 1]

if __name__ == '__main__':
    BirKartaApp().run()
