from nautilus_file_converter.converters.image import ImageConverter


_CONVERTERS = [ImageConverter()]


def get_converters():
    return list(_CONVERTERS)

