from nautilus_file_converter.converters.image import ImageConverter
from nautilus_file_converter.converters.video import VideoConverter


_CONVERTERS = [ImageConverter(), VideoConverter()]


def get_converters():
    return list(_CONVERTERS)
