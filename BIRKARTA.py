from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.behaviors import ButtonBehavior  # <-- ПРАВИЛЬНЫЙ импорт

from kivy.utils import platform
if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission
    from android import activity

Window.clearcolor = (1, 1, 1, 1)

user_data = {
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
            "name": "ОРТ КАУІПСІЗІГІ",
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
    def __init__(self, cert, idx, open_callback, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, spacing=4, padding=[18, 10, 10, 8], **kwargs)
        with self.canvas.before:
            Color(0.96, 0.98, 1, 1)
            self.bg = RoundedRectangle(radius=[22], pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

        title = Label(
            text=cert['name'], font_size=15, bold=True, color=[0, 0, 0, 1],
            halign='left', valign='top', size_hint_y=None, text_size=(Window.width-110, None)
        )
        title.bind(texture_size=lambda inst, val: setattr(title, 'height', val[1]))
        self.add_widget(title)

        date_issued = cert['details'].get('Выдано', '')
        self.add_widget(Label(
            text=f"Выдано: {date_issued}", font_size=14,
            color=[0.2, 0.2, 0.2, 1], halign='left', valign='middle',
            size_hint_y=None, height=22
        ))
        self.add_widget(Label(
            text=f"Действует до: {cert['date']}", font_size=14,
            color=[0.2, 0.2, 0.2, 1], halign='left', valign='middle',
            size_hint_y=None, height=22
        ))
        self.bind(minimum_height=self.setter('height'))
        self._open = open_callback
        self._idx = idx

    def _upd(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def on_press(self):
        self._open(self._idx)

class MainScreen(Screen):
    def __init__(self, get_data_cb, open_detail_callback, **kwargs):
        super().__init__(**kwargs)
        self.get_data_cb = get_data_cb

        layout = BoxLayout(orientation='vertical', spacing=18, padding=[30, 20, 30, 20])
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        header.add_widget(Label(text='БірКарта', font_size=28, bold=True, color=[0, 0, 0, 1]))
        header.add_widget(Widget(size_hint_x=None, width=40))
        layout.add_widget(header)

        self.name_label = Label(text='Поднесите карту к телефону', font_size=20, bold=True, color=[0, 0, 0, 1],
                                size_hint_y=None, height=36)
        layout.add_widget(self.name_label)

        self.scroll = ScrollView()
        self.rows = BoxLayout(orientation='vertical', spacing=18, size_hint_y=None, padding=[0, 10, 0, 10])
        self.rows.bind(minimum_height=self.rows.setter('height'))
        self.scroll.add_widget(self.rows)

        layout.add_widget(self.scroll)
        self.add_widget(layout)

        self.refresh_ui()

    def refresh_ui(self):
        data = self.get_data_cb()
        self.rows.clear_widgets()
        if not data:
            return
        self.name_label.text = data.get('fio', 'Сотрудник')
        for idx, cert in enumerate(data.get('certs', [])):
            self.rows.add_widget(CardButton(cert, idx, self.open_detail))

    def open_detail(self, idx):
        self.manager.parent_app.show_detail(idx)

class DetailScreen(Screen):
    def __init__(self, cert, back_callback, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=24)
        layout.add_widget(Label(
            text=cert['name'], font_size=20, bold=True, color=[0, 0.3, 1, 1],
            halign='center', valign='middle', text_size=(Window.width-80, None)
        ))
        layout.add_widget(Label(
            text=f"Действует до: {cert['date']}",
            font_size=16, bold=True, color=[0, 0, 0, 1], size_hint_y=None, height=28
        ))
        for k, v in cert['details'].items():
            lbl = Label(
                text=f"{k}: {v}", font_size=15, color=[0, 0, 0, 1],
                halign='left', valign='top', size_hint_y=None, text_size=(Window.width-80, None)
            )
            lbl.bind(texture_size=lambda inst, val: setattr(lbl, 'height', val[1]))
            layout.add_widget(lbl)
        layout.add_widget(Widget(size_hint_y=None, height=10))
        back_btn = Button(text="Назад", size_hint_y=None, height=45, background_color=[0, 0.3, 1, 1], color=[1, 1, 1, 1])
        back_btn.bind(on_press=lambda inst: back_callback())
        layout.add_widget(back_btn)
        self.add_widget(layout)

class BirKartaApp(App):
    def build(self):
        self.data = user_data.copy()  # <-- ДЕФОЛТ, чтобы экран не был пустым
        self.sm = ScreenManager()
        self.show_main()
        if platform == 'android':
            request_permissions([Permission.NFC])
            activity.bind(on_new_intent=self.on_new_intent)
        return self.sm

    def show_main(self):
    # Если экран уже добавлен — просто переключаемся и обновляем
        if self.sm.has_screen('main'):
           self.sm.current = 'main'
           scr = self.sm.get_screen('main')
           if hasattr(scr, 'refresh_ui'):
              scr.refresh_ui()
           return

    # Иначе создаём и добавляем
        screen = MainScreen(lambda: self.data, None, name="main")
        self.sm.add_widget(screen)           # <-- Больше не назначаем screen.manager вручную
        self.sm.parent_app = self
        self.sm.current = "main"


    def show_detail(self, idx):
        def go_back():
            self.show_main()
        certs = self.data.get("certs", [])
        if 0 <= idx < len(certs):
            cert = certs[idx]

        if self.sm.has_screen('detail'):
           self.sm.remove_widget(self.sm.get_screen('detail'))

        self.sm.add_widget(DetailScreen(cert, go_back, name="detail"))
        self.sm.current = "detail"

    def on_new_intent(self, intent):
        if platform != 'android':
            return
        Intent = autoclass('android.content.Intent')
        NfcAdapter = autoclass('android.nfc.NfcAdapter')
        action = intent.getAction()
        if action not in (NfcAdapter.ACTION_NDEF_DISCOVERED,  # <-- ПОПРАВИЛ БУКВУ 'S'
                          NfcAdapter.ACTION_TAG_DISCOVERED,
                          NfcAdapter.ACTION_TECH_DISCOVERED):
            return

        raw_msgs = intent.getParcelableArrayExtra(NfcAdapter.EXTRA_NDEF_MESSAGES)
        if raw_msgs is None:
            return

        messages = [cast('android.nfc.NdefMessage', m) for m in raw_msgs]
        if not messages:
            return

        records = messages[0].getRecords()
        if not records or records.length == 0:
            return

        rec0 = records[0]
        payload = rec0.getPayload()
        if payload is None:
            return

        status = payload[0] & 0xFF
        lang_len = status & 0x3F
        utf16 = (status & 0x80) != 0
        text_bytes = payload[1 + lang_len:]

        try:
            text = bytes(text_bytes).decode('utf-16' if utf16 else 'utf-8')
        except Exception:
            return

        try:
            data = json.loads(text)
        except Exception:
            return

        self.data = data
        self.show_main()
        if hasattr(self.sm.current_screen, 'refresh_ui'):
            self.sm.current_screen.refresh_ui()

if __name__ == '__main__':
    BirKartaApp().run()
