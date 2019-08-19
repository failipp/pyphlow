import os
from collections import deque
from typing import Optional, Deque, Container, Union

from PIL import ExifTags
from PIL import Image as PILImage

from pyphlow.tools.remove import main as remove_pictures

TEST_PATH = ("~/programming/python/projects/pyphlow/"
             "pyphlow/tools/test/2019-02-04 Winter")


class Picture:
    """
    Represent a picture and its specific workflow. A Picture is not defined
    by one file but by a name and multiple files on the hard disk.
    For one Picture there must be a .jpg file. There also can be an exported
    .jpg file, a raw file and an .xmp darktable file.
    """

    def __init__(self, basepath, name, **kwargs):
        self._name = name
        self._basepath = basepath

        self._jpg = None
        self._raw = None
        self._export = None
        self._darktable_file = None

        self._reject_raw = False
        self._reject_jpg = False

        # JPG picture
        if os.path.exists(os.path.join(basepath, f"1jpg/{name}.JPG")):
            self._jpg = f"1jpg/{name}.JPG"
        elif os.path.exists(os.path.join(basepath, f"1jpg/{name}.jpg")):
            self._jpg = f"1jpg/{name}.jpg"

        # Raw picture
        if f"{name}.ARW" in os.listdir(os.path.join(basepath, '1raw')):
            # ARW is specific for Sony cameras
            self._raw = f"1raw/{name}.ARW"

            if os.path.exists(os.path.join(basepath, f"{self._raw}.xmp")):
                self._darktable_file = f"{self._raw}.xmp"

        """
        if self._raw and not self._jpg:
            print(f"Generating JPG file {name}.JPG")
            with rawpy.imread(os.path.join(basepath, self._raw))as raw:
                rgb = raw.postprocess()
            self._jpg = f"1jpg/{name}.JPG"
            imageio.imsave(os.path.join(basepath, self._jpg), rgb)
            """

        self._show_export = True
        if os.path.exists(os.path.join(basepath, f"3export/{name}.JPG")):
            self._export = f"3export/{name}.JPG"
        elif os.path.exists(os.path.join(basepath, f"3export/{name}.jpg")):
            self._export = f"3export/{name}.jpg"

        if not self._jpg:
            # There must be a .JPG file for the program to work
            raise FileNotFoundError(
                f"{name}.JPG does not exist and can not be generated!")

        self._angle: int = self._get_angle()

    def _get_angle(self) -> int:
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

        angle = 0
        with PILImage.open(self.preview_path) as img:
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
                    print('KeyError!!!!', self.name)
                    print(e)
                    orientation = 0
                if orientation == 3:
                    angle = 180
                elif orientation == 6:
                    angle = 270
                elif orientation == 8:
                    angle = 90

        return angle

    def reject_raw(self):
        if self.exists:
            self._reject_jpg = False
            self._reject_raw = True

    def reject_all(self):
        self._reject_jpg = True
        self._reject_raw = True

    def keep(self):
        if self.exists:
            self._reject_jpg = False
            self._reject_raw = False

    @property
    def preview_path(self):
        if self._export and self._show_export:
            picture = self._export
        else:
            picture = self._jpg

        return os.path.join(self._basepath, picture)

    @property
    def extensions(self):
        ext = "JPG",
        if self._raw:
            ext = *ext, "ARW"
            if self._darktable_file:
                ext = *ext, "ARW.xmp"
        return ext

    @property
    def info(self):
        if self._export:
            export = " - EXPORT" if self.show_export else " - ORIGINAL"
        else:
            export = ""
        return f"{self.name}: {','.join(self.extensions)} {export}"

    @property
    def name(self):
        return self._name

    @property
    def angle(self):
        return self._angle

    @property
    def exists(self):
        if self._jpg:
            return True
        return False

    @property
    def rejected(self) -> Container[str]:
        to_reject = tuple()

        if self._jpg and self._reject_jpg:
            to_reject = *to_reject, self._jpg
        if self._raw and self._reject_raw:
            to_reject = *to_reject, self._raw
            if self._darktable_file:
                to_reject = *to_reject, self._darktable_file

        return to_reject

    @property
    def show_export(self):
        return self._show_export if self._export else False

    @show_export.setter
    def show_export(self, value: bool):
        self._show_export = value


class PictureHandler:
    """
    Parse the directory, generate Pictures and manage them.
    """

    def __init__(self, basepath: Union[str, None] = None, **kwargs):
        basepath = os.path.abspath(basepath)

        if not os.path.exists(basepath):
            raise AttributeError(f"Path does not exist {basepath}")

        self._basepath: str = basepath

        self._pictures: Deque[Picture] = self._parse()
        self._current: Optional[Picture] = None

    def _parse(self) -> Deque[Picture]:
        jpgdir = os.path.join(self._basepath, '1jpg')
        rawdir = os.path.join(self._basepath, '1raw')

        picset = set()
        # TODO: Add extensions
        picture_extensions = ['JPG', 'ARW']

        for d in jpgdir, rawdir:
            picset.update([
                x[0] for x in (f.split('.') for f in os.listdir(d))
                if x[-1] in picture_extensions
            ])

        return deque(
            sorted((Picture(self._basepath, name) for name in picset),
                   key=lambda p: p.name))

    def apply(self) -> Picture:
        self._pictures.append(self._current)
        with open(os.path.join(self._basepath, 'rejected.txt'), 'w') as f:
            for pic in self._pictures:
                for path in pic.rejected:
                    f.write(f"{path}\n")

        remove_pictures(self._basepath)

        # os.remove(os.path.join(self._basepath, 'rejected.txt'))

        self._pictures = self._parse()
        self._current = None
        return self.next

    @property
    def next(self) -> Picture:
        if self._current is not None:
            self._pictures.append(self._current)
        self._current = self._pictures.popleft()
        while not self._current.exists:
            self._current = self._pictures.popleft()

        return self._current

    @property
    def previous(self) -> Picture:
        self._pictures.appendleft(self._current)
        self._current = self._pictures.pop()
        while not self._current.exists:
            self._current = self._pictures.pop()

        return self._current


if __name__ == '__main__':
    d = PictureHandler(TEST_PATH)
    print(d._pictures)

    for _ in range(220):
        print(d.next.preview_path)
    print(d.previous.preview_path)
