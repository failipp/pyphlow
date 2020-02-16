import os
from collections import deque
from enum import Enum
from functools import lru_cache
from typing import Container

from PIL import ExifTags
from PIL import Image as PILImage

Mode = Enum("Mode", "CATEGORIZING EDITING VIEW_ALL VIEW_PUBLIC")


class FalseDirContentError(Exception):
    pass


class Picture:
    def __init__(self, name: str, preview: str, mode: Mode, **kwargs):
        self._name = name
        self._preview = preview
        self._mode = mode

        self._action = None

        self._is_public = kwargs.get('is_public', False)

    @property
    def name(self):
        return self._name

    @property
    def preview(self):
        return self._preview

    @property
    def action(self):
        return self._action

    @property
    def is_public(self):
        """
        bool: indicates if the picture has been exported publicly
        """
        return self._is_public

    def _reject(self):
        self._action = "reject"

    def _make_private(self):
        self._action = "private"

    def keep(self):
        self._action = None

    def __getattr__(self, name):
        if self._mode == Mode.CATEGORIZING:
            if name == "reject":
                return self._reject
            elif name == "make_private":
                return self._make_private

        raise AttributeError(f"{type(self)} does not have attribute {name}")


class PictureManager:
    def __init__(self, root: str, mode: Mode):
        self.root = os.path.abspath(root)

        if not os.path.exists(self.root):
            raise ValueError("Path does not exist!")

        if not isinstance(mode, Mode):
            raise ValueError(f"mode attribute must be set to a mode")

        self._mode = mode
        self._pictures = load_pictures(self.root, self.mode)

    @property
    def next(self) -> Picture:
        # rotate one picture to te left
        self._pictures.append(self._pictures.popleft())

        return self.current_picture

    @property
    def previous(self) -> Picture:
        # rotate one picture to the right
        self._pictures.appendleft(self._pictures.pop())

        return self.current_picture

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, new_mode):
        if not isinstance(new_mode, Mode):
            raise ValueError(f"mode attribute must be set to a mode")
        # TODO: apply changes
        if self._mode != new_mode:
            self._mode = new_mode
            self.apply()

    def apply(self):
        apply_actions(self.root, self._pictures)
        self._pictures = load_pictures(self.root, self.mode)

    @property
    def current_picture(self):
        return self._pictures[0]


def find_jpg(root, name):
    for ext in ("jpg", "JPG", "jpeg", "JPEG"):
        path = os.path.join(root, f"{name}.{ext}")
        if os.path.exists(path):
            return path

    raise FileNotFoundError(f"Picture {name} not in {root}")


def displayable(file_name):
    for ext in ("jpg", "JPG", "jpeg", "JPEG", "png", "PNG"):
        if file_name.endswith(ext):
            return True
    return False


def load_pictures(root: str, mode: Mode) -> deque:
    """
    Parse picture directory.

    Parse directory tree for pictures and sort them into categories.
    Return a deque containing all pictures sorted by their names.

    Args:
        root: path to the root of the directory tree for the pictures
        mode: mode of the application, so that only necessary pictures are loaded

    Returns:
        deque: double ended queue of picture objects
    """

    # paths of subdirectories

    export_path = os.path.join(root, 'export')

    # list all picture names

    pictures = []

    if mode == Mode.CATEGORIZING or mode == Mode.EDITING:
        src_path = os.path.join(root, 'src')
        picture_names = set()

        for path, dirs, files in os.walk(src_path):
            for picture in files:
                if picture.endswith((".xmp", ".XMP")):
                    continue
                name, *ext = picture.split('.')

                picture_names.add(name)

        for name in sorted(list(picture_names)):
            exported_to_public = any(name in pic for pic in os.listdir(
                os.path.join(export_path, 'public')))

            pictures.append(
                Picture(name, find_jpg(os.path.join(src_path, "jpg"), name),
                        mode, is_public=exported_to_public))

    if mode == Mode.EDITING:
        edit_path = os.path.join(root, 'edit')

        for directory in os.listdir(edit_path):
            picture_names.add(directory)
            for picture in os.listdir(os.path.join(edit_path, directory)):
                exported_to_public = any(directory in pic for pic in os.listdir(
                    os.path.join(export_path, 'public')))

                preview = os.path.join(edit_path, directory,
                                       picture) if displayable(picture) else ""

                pictures.append(Picture(picture, preview, mode,
                                        exported_to_public=exported_to_public))

    if mode == Mode.VIEW_ALL:
        private_path = os.path.join(export_path, 'private')
        for picture in os.listdir(private_path):
            name, *ext = picture.split('.')
            pictures.append(Picture(name, find_jpg(private_path, name), mode))

    if mode == Mode.VIEW_ALL or mode == Mode.VIEW_PUBLIC:
        public_path = os.path.join(export_path, 'public')
        for picture in os.listdir(public_path):
            if os.path.isfile(os.path.join(public_path, picture)):
                name, *ext = picture.split('.')
                pictures.append(
                    Picture(name, find_jpg(public_path, name), mode))

    if len(pictures) > 0:
        return deque(sorted(pictures, key=lambda x: x.name))
    else:
        return deque([Picture("No picture available", "", mode)])


def _reject_src(root, picture):
    for subdir in os.listdir(os.path.join(root, "src")):
        for pic_file in os.listdir(os.path.join(root, "src", subdir)):
            if picture.name in pic_file:
                old_path = os.path.join(root, 'src', subdir, pic_file)
                new_path = os.path.join(root, 'rejected', 'src', subdir,
                                        pic_file)

                print(f"From: {old_path}\nTo: {new_path}")

                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                os.rename(old_path, new_path)


def apply_actions(root: str, pictures: Container[Picture]):
    for picture in pictures:
        if picture.action is None:
            continue

        if picture.action == "reject":
            # root/src/jpg
            # root/src
            _reject_src(root, picture)
        elif picture.action == "private":
            # first move jpg to private folder
            jpg_path = os.path.join(root, "src", "jpg")
            old_path = find_jpg(jpg_path, picture.name)
            new_path = os.path.join(root, "export", "private",
                                    os.path.basename(old_path))
            print(f"From: {old_path}\nTo: {new_path}")

            os.rename(old_path, new_path)

            # then reject
            _reject_src(root, picture)
        else:
            raise IOError(f"Picture {picture.name} has undefined "
                          f"action: {picture.action}")


@lru_cache()
def get_picture_angle(path) -> int:
    # TODO: Maybe replace exif reading?
    """
    from PIL import Image
    import piexif

    im = Image.open(filename)
    exif_dict = piexif.load(im.info["exif"])
    # process im and exif_dict...
    w, h = im.size
    exif_dict["0th"][piexif.ImageIFD.XResolution] = (w, 1)
    exif_dict["0th"][piexif.ImageIFD.YResolution] = (h, 1)
    exif_bytes = piexif.dump(exif_dict)
    im.save(new_file, "jpeg", exif=exif_bytes)

    exif_dict = piexif.load(im.info["exif"])
    exif_dict["0th"][piexif.ImageIFD.Orientation]
    """
    if path is None or not os.path.exists(path):
        return 0

    angle = 0
    with PILImage.open(path) as img:
        # Often, the picture is not rotated correctly.
        # The correct orientation is
        # written to the Exif metadata by the camera.

        exif_data = img._getexif()
        if exif_data:
            try:
                orientation = {
                    ExifTags.TAGS[k]: v
                    for k, v in exif_data.items() if k in ExifTags.TAGS
                }['Orientation']
            except KeyError as e:
                print('KeyError!!!!', path)
                print(e)
                orientation = 0
            if orientation == 3:
                angle = 180
            elif orientation == 6:
                angle = 270
            elif orientation == 8:
                angle = 90

    return angle
