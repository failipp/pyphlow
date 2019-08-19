import os

from kivy import Config
from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.properties import (StringProperty, ObjectProperty, NumericProperty,
                             ListProperty, AliasProperty,
                             BooleanProperty)
from kivy.resources import resource_find
from kivy.uix.image import Image
from kivy.uix.widget import Widget

from pyphlow.data.handler import PictureHandler, TEST_PATH, Picture

RED = [.8, .5, .5]
YELLOW = [.8, .8, .5]
GREY = [.5, .5, .5]


class PhlowWidget(Widget):
    source: str = StringProperty(None)
    extensions = StringProperty('')
    img = ObjectProperty(None)
    background_color = ListProperty(GREY)

    def __init__(self, path, **kwargs):
        super(PhlowWidget, self).__init__(**kwargs)

        self._keyboard = Window.request_keyboard(self._on_keyboard_close, self)
        self._keyboard.bind(on_key_down=self._on_key_down)

        self._picture_handler = PictureHandler(path)
        self._current_picture: Picture = self._picture_handler.next
        self.source = self._current_picture.preview_path

    def _on_keyboard_close(self):
        self._keyboard.unbind(on_key_down=self._on_key_down)
        self._keyboard = None

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        print(keyboard, keycode, text, modifiers)

        key = keycode[1]

        if key == "right":
            self._current_picture = self._picture_handler.next
            self.source = self._current_picture.preview_path
        elif key == "left":
            self._current_picture = self._picture_handler.previous
            self.source = self._current_picture.preview_path
        elif key == "x":
            self._current_picture.reject_all()
            self.background_color = RED
        elif key == "c":
            self._current_picture.reject_raw()
            self.background_color = YELLOW
        elif key == "v":
            self._current_picture.keep()
            self.background_color = GREY
        elif key == "o":
            self._current_picture = self._picture_handler.apply()
            self.source = self._current_picture.preview_path
        elif key == "e":
            show_export = not self._current_picture.show_export
            self._current_picture.show_export = show_export
            self.source = self._current_picture.preview_path

    def on_source(self, obj, value):
        print(self.source.split("/")[-1], self._current_picture.name)
        # TODO: rename self.extensions
        self.extensions = self._current_picture.info
        self.img.angle = self._current_picture.angle
        print(self._current_picture.angle, "winkel")
        # self.rejected = any((self._current_picture._reject_raw,
        #                      self._current_picture._reject_jpg))
        if self._current_picture._reject_raw:
            if self._current_picture._reject_jpg:
                self.background_color = RED
            else:
                self.background_color = YELLOW
        else:
            self.background_color = GREY


class RotatableImage(Image):
    angle = NumericProperty(0)

    def get_is_rotated(self):
        return self.angle == 90 or self.angle == 270

    is_rotated = AliasProperty(get_is_rotated, bind=('texture', 'angle'),
                               cache=True)

    def get_scale(self):
        scale = 1.
        if self.is_rotated:
            iw, ih = self.norm_image_size
            w, h = self.size
            if ih == h:
                scale = ih / iw
            elif iw == w:
                scale = h / w
            else:
                raise ValueError(f"You didn't think of {w} {iw} {h} {ih}")
            if w < ih * scale:
                scale = w / ih
        return scale

    scale_factor = AliasProperty(get_scale,
                                 bind=('texture', 'is_rotated', 'size'),
                                 cache=True)


class PhlowImage(Widget):
    source = StringProperty(None)
    texture = ObjectProperty(None, allownone=True)
    texture_size = ListProperty([0, 0])

    def get_image_ratio(self):
        if self.texture:
            return self.texture.width / self.texture.height
        return 1.

    image_ratio = AliasProperty(get_image_ratio, bind=('texture',), cache=True)

    allow_stretch = BooleanProperty(False)
    keep_ratio = BooleanProperty(True)
    keep_data = BooleanProperty(False)

    nocache = BooleanProperty(False)

    def get_norm_image_size(self):
        if not self.texture:
            return self.size
        ratio = self.image_ratio
        width, height = self.size
        tex_width, tex_height = self.texture.size

        if self.allow_stretch:
            if not self.keep_ratio:
                return width, height
            i_width = width
        else:
            i_width = min(width, tex_width)

        i_height = i_width / ratio
        if i_height > height:
            if self.allow_stretch:
                i_height = height
            else:
                i_height = min(height, tex_height)
            i_width = i_height * ratio
        return i_width, i_height

    norm_image_size = AliasProperty(get_norm_image_size,
                                    bind=('texture', 'size', 'allow_stretch',
                                          'image_ratio', 'keep_ratio'),
                                    cache=True)

    def __init__(self, **kwargs):
        self._coreimage = None
        super(PhlowImage, self).__init__(**kwargs)
        fbind = self.fbind
        update = self.texture_update
        fbind('source', update)
        if self.source:
            update()

    def texture_update(self, *largs):
        if not self.source:
            self.texture = None
        else:
            filename = resource_find(self.source)
            if filename is None:
                return Logger.error('Image: Error reading file {filename}'.
                                    format(filename=self.source))

            if self._coreimage is not None:
                self._coreimage.unbind(on_texture=self._on_tex_change)
            try:
                self._coreimage = ci = CoreImage(filename,
                                                 keep_data=self.keep_data,
                                                 mipmap=False,
                                                 nocache=self.nocache)
            except Exception as e:
                print(e)
                Logger.error('Image: Error loading texture {filename}'.
                             format(filename=self.source))
                self._coreimage = ci = None

            if ci:
                ci.bind(on_texture=self._on_tex_change)
                self.texture = ci.texture

    def on_texture(self, instance, value):
        if value is not None:
            self.texture_size = list(value.size)

    def _on_tex_change(self, *largs):
        self.texture = self._coreimage.texture
        ci = self._coreimage

    def reload(self):
        try:
            self._coreimage.remove_from_cache()
        except AttributeError:
            pass

        oldsource = self.source
        self.source = ''
        self.source = oldsource

    def on_nocache(self, *args):
        if self.nocache and self._coreimage:
            self._coreimage.remove_from_cache()
            self._coreimage._nocache = True


class PhlowApp(App):
    def __init__(self, **kwargs):
        self._path = kwargs.pop('path', TEST_PATH)
        super().__init__(**kwargs)

    def build(self):
        return PhlowWidget(self._path)


def main(path):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        print(f"Path {path} does not exist!")
        return

    # disable escape key
    Config.set('kivy', 'exit_on_escape', 0)
    PhlowApp(path=path).run()


if __name__ == '__main__':
    main(TEST_PATH)
