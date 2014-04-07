'''Autogenerated by get_gl_extensions script, do not edit!'''
from OpenGL import platform as _p
from OpenGL.GL import glget
EXTENSION_NAME = 'GL_EXT_texture_sRGB_decode'
_p.unpack_constants( """GL_TEXTURE_SRGB_DECODE_EXT 0x8A48
GL_DECODE_EXT 0x8A49
GL_SKIP_DECODE_EXT 0x8A4A""", globals())


def glInitTextureSrgbDecodeEXT():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( EXTENSION_NAME )
