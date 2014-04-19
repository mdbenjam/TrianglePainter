'''Autogenerated by get_gl_extensions script, do not edit!'''
from OpenGL import platform as _p, constants as _cs, arrays
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_EXT_texture_buffer_object'
def _f( function ):
    return _p.createFunction( function,_p.GL,'GL_EXT_texture_buffer_object',False)
_p.unpack_constants( """GL_TEXTURE_BUFFER_EXT 0x8C2A
GL_MAX_TEXTURE_BUFFER_SIZE_EXT 0x8C2B
GL_TEXTURE_BINDING_BUFFER_EXT 0x8C2C
GL_TEXTURE_BUFFER_DATA_STORE_BINDING_EXT 0x8C2D
GL_TEXTURE_BUFFER_FORMAT_EXT 0x8C2E""", globals())
glget.addGLGetConstant( GL_TEXTURE_BUFFER_EXT, (1,) )
glget.addGLGetConstant( GL_MAX_TEXTURE_BUFFER_SIZE_EXT, (1,) )
glget.addGLGetConstant( GL_TEXTURE_BINDING_BUFFER_EXT, (1,) )
glget.addGLGetConstant( GL_TEXTURE_BUFFER_DATA_STORE_BINDING_EXT, (1,) )
glget.addGLGetConstant( GL_TEXTURE_BUFFER_FORMAT_EXT, (1,) )
@_f
@_p.types(None,_cs.GLenum,_cs.GLenum,_cs.GLuint)
def glTexBufferEXT( target,internalformat,buffer ):pass


def glInitTextureBufferObjectEXT():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( EXTENSION_NAME )