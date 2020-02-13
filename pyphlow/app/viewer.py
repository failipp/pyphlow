import os
import subprocess
import sys

from kivy.properties import (AliasProperty, BoundedNumericProperty,
                             NumericProperty, ObjectProperty, OptionProperty,
                             StringProperty)
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from pyphlow.data.picturehandling import (Mode, Picture, PictureManager,
                                          get_picture_angle)

RED = [.8, .5, .5]
YELLOW = [.8, .8, .5]
GREY = [.3, .3, .3]


def jpg_path(root, name):
    for ext in ["jpg", "JPG", "jpeg", "JPEG"]:
        path = os.path.join(root, f"{name}.{ext}")
        if os.path.exists(path):
            return path

    return None


class ViewScreen(Screen):
    viewer = ObjectProperty(None)

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        self.viewer._on_key_down(keyboard, keycode, text, modifiers)


class PhlowViewer(Widget):
    def _get_source(self):
        if (self._current_picture.name == "No picture available"
                or self._current_picture.preview == ""):
            return (f"{os.path.dirname(os.path.abspath(__file__))}"
                    f"/../res/empty.png")

        return self._current_picture.preview

    source: str = AliasProperty(_get_source,
                                None,
                                bind=("_current_picture", ),
                                cache=False)

    picture_info = StringProperty()
    img = ObjectProperty(None)

    def _get_mode_str(self):
        mode = getattr(self._picture_manager, 'mode', None)
        if mode is None:
            return "Wait"
        elif mode == Mode.VIEW_PUBLIC:
            mode_str = "View public"
        elif mode == Mode.VIEW_ALL:
            mode_str = "View all"
        elif mode == Mode.EDITING:
            mode_str = "Edit"
        elif mode == Mode.CATEGORIZING:
            mode_str = "Categorizing"

        return mode_str

    mode_str = AliasProperty(_get_mode_str,
                             None,
                             bind=("mode", "_picture_manager"),
                             cache=False)

    mode = OptionProperty(Mode.VIEW_PUBLIC,
                          options=[
                              Mode.CATEGORIZING, Mode.EDITING, Mode.VIEW_ALL,
                              Mode.VIEW_PUBLIC
                          ])

    _picture_manager = ObjectProperty(None)
    _current_picture = ObjectProperty(Picture("No picture available", "",
                                              mode))

    _path = StringProperty(sys.argv[1])

    def _get_current_picture_action(self):
        if self._current_picture.action == "reject":
            return "Reject"
        elif self._current_picture.action == "private":
            return "Make private"
        else:
            return ""

    def _set_current_picture_action(self, value):
        try:
            getattr(self._current_picture, value)()
        except AttributeError:
            return False
        return True

    action = AliasProperty(_get_current_picture_action,
                           _set_current_picture_action,
                           bind=("source", ),
                           cache=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not os.path.exists(self._path):
            raise FileNotFoundError(f"Path {self._path} does not exist!!!")

        self._picture_manager = PictureManager(self._path, self.mode)

        self._current_picture: Picture = self._picture_manager.current_picture

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]

        if 'meta' in modifiers:
            pass
        elif 'shift' in modifiers:
            if key == 'h':
                # offset left
                self.img.offsetfactor_x += .1
            elif key == 'l':
                # offset right
                self.img.offsetfactor_x -= .1
            elif key == 'j':
                # offset down
                self.img.offsetfactor_y += .1
            elif key == 'k':
                # offset up
                self.img.offsetfactor_y -= .1
        else:
            if key == "l":
                self._current_picture = self._picture_manager.next
            elif key == "h":
                self._current_picture = self._picture_manager.previous
            elif key == "1":
                self._picture_manager.mode = Mode.CATEGORIZING
                self.mode = Mode.CATEGORIZING
                self._current_picture = self._picture_manager.current_picture
            elif key == "2":
                self._picture_manager.mode = Mode.EDITING
                self.mode = Mode.EDITING
                self._current_picture = self._picture_manager.current_picture
            elif key == "3":
                self._picture_manager.mode = Mode.VIEW_ALL
                self.mode = Mode.VIEW_ALL
                self._current_picture = self._picture_manager.current_picture
            elif key == "4":
                self._picture_manager.mode = Mode.VIEW_PUBLIC
                self.mode = Mode.VIEW_PUBLIC
                self._current_picture = self._picture_manager.current_picture
            elif key == "x":
                self.action = "reject"
            elif key == "c":
                self.action = "make_private"
            elif key == "v":
                self.action = "keep"
            elif key == 'k':
                self.img.zoomfactor *= 1.25
            elif key == 'j':
                self.img.zoomfactor /= 1.25
            elif key == 'u':
                self.img.zoomfactor = 1
                self.img.offsetfactor_x = 0
                self.img.offsetfactor_y = 0
            elif key == 'e':
                if self.mode == Mode.EDITING:
                    # open in darktable
                    path = os.path.join(self._path, 'src', 'arw',
                                        f'{self._current_picture.name}.ARW')
                    subprocess.Popen(['darktable', path])

    def on_source(self, obj, value):
        print(self.source.split("/")[-1], self._current_picture.name)

        self.picture_info = self._current_picture.name

        print(getattr(self.img, 'angle', 0), "winkel")


class RotatableImage(Image):
    def _get_angle(self):
        return get_picture_angle(self.source)

    angle = AliasProperty(_get_angle, None, bind=("source", ), cache=True)

    def get_is_rotated(self):
        return self.angle == 90 or self.angle == 270

    is_rotated = AliasProperty(get_is_rotated, bind=('angle', ), cache=True)

    zoomfactor = NumericProperty(1)
    offsetfactor_x = BoundedNumericProperty(0,
                                            min=-1,
                                            max=1,
                                            errorhandler=(lambda x: 1
                                                          if x > 1 else -1))
    offsetfactor_y = BoundedNumericProperty(0,
                                            min=-1,
                                            max=1,
                                            errorhandler=(lambda x: 1
                                                          if x > 1 else -1))

    def _get_offset_x(self):
        print("getoffset x")
        if self.is_rotated:
            window_w, window_h = self.parent.size
            self_h, self_w = self.norm_image_size
        else:
            window_w, window_h = self.parent.size
            self_w, self_h = self.norm_image_size
        self_w *= self.scale_factor
        print(f"offset x: {(self_w - window_w) / 2}")
        if (self_w - window_w) / 2 > 0:
            return ((self_w - window_w) / 2) * self.offsetfactor_x
        else:
            return 0

    def _get_offset_y(self):
        print("getoffset y")
        if self.is_rotated:
            window_w, window_h = self.parent.size
            self_h, self_w = self.norm_image_size
        else:
            window_w, window_h = self.parent.size
            self_w, self_h = self.norm_image_size
        self_h *= self.scale_factor
        print(f"offset y: {(self_h - window_h) / 2}")
        if (self_h - window_h) / 2 > 0:
            return ((self_h - window_h) / 2) * self.offsetfactor_y
        else:
            return 0

    offset_x = AliasProperty(_get_offset_x,
                             None,
                             bind=('offsetfactor_x', 'scale_factor'),
                             cache=True)
    offset_y = AliasProperty(_get_offset_y,
                             None,
                             bind=('offsetfactor_y', 'scale_factor'),
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
                # TODO make right for pictures smaller than the window
                # raise ValueError(f"You didn't think of {w} {iw} {h} {ih}")
                pass
            # print(f"Here it's {w} {iw} {h} {ih}")
            if w < ih * scale:
                scale = w / ih
        return scale * self.zoomfactor

    scale_factor = AliasProperty(get_scale,
                                 bind=('texture', 'size', 'zoomfactor'),
                                 cache=True)
