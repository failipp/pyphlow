import os

from kivy import Config
from kivy.app import App
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager

from pyphlow.app.viewer import ViewScreen


class PhlowManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._keyboard = Window.request_keyboard(self._on_keyboard_close, self)
        self._keyboard.bind(on_key_down=self._on_key_down)

    def _on_keyboard_close(self):
        self._keyboard.unbind(on_key_down=self._on_key_down)
        self._keyboard = None

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        print(keyboard, keycode, text, modifiers)

        self.current_screen._on_key_down(keyboard, keycode, text, modifiers)


class PhlowApp(App):
    _path = StringProperty("")

    def __init__(self, **kwargs):
        self._path = kwargs.pop('path', None)
        super().__init__(**kwargs)

    def build(self):
        sm = PhlowManager()
        sm.add_widget(ViewScreen())
        return sm


def main(path):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        print(f"Path {path} does not exist!")
        return

    # disable escape key
    Config.set('kivy', 'exit_on_escape', 0)
    PhlowApp(path=path).run()


if __name__ == '__main__':
    main("/wrong_path")
