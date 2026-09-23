from nautilus_file_converter.converters.audio import AudioConverter
from nautilus_file_converter.converters.document import DocumentConverter
from nautilus_file_converter.converters.image import ImageConverter
from nautilus_file_converter.converters.video import VideoConverter


_CONVERTERS = [ImageConverter(), VideoConverter(), AudioConverter(), DocumentConverter()]


def get_converters():
    return [converter for converter in _CONVERTERS if converter.available()]
