'''Autogenerated by get_gl_extensions script, do not edit!'''
from OpenGL import platform as _p, constants as _cs, arrays
from OpenGL.GL import glget
import ctypes
EXTENSION_NAME = 'GL_NV_occlusion_query'
def _f( function ):
    return _p.createFunction( function,_p.GL,'GL_NV_occlusion_query',False)
_p.unpack_constants( """GL_PIXEL_COUNTER_BITS_NV 0x8864
GL_CURRENT_OCCLUSION_QUERY_ID_NV 0x8865
GL_PIXEL_COUNT_NV 0x8866
GL_PIXEL_COUNT_AVAILABLE_NV 0x8867""", globals())
glget.addGLGetConstant( GL_PIXEL_COUNTER_BITS_NV, (1,) )
glget.addGLGetConstant( GL_CURRENT_OCCLUSION_QUERY_ID_NV, (1,) )
@_f
@_p.types(None,_cs.GLsizei,arrays.GLuintArray)
def glGenOcclusionQueriesNV( n,ids ):pass
@_f
@_p.types(None,_cs.GLsizei,arrays.GLuintArray)
def glDeleteOcclusionQueriesNV( n,ids ):pass
@_f
@_p.types(_cs.GLboolean,_cs.GLuint)
def glIsOcclusionQueryNV( id ):pass
@_f
@_p.types(None,_cs.GLuint)
def glBeginOcclusionQueryNV( id ):pass
@_f
@_p.types(None,)
def glEndOcclusionQueryNV(  ):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLenum,arrays.GLintArray)
def glGetOcclusionQueryivNV( id,pname,params ):pass
@_f
@_p.types(None,_cs.GLuint,_cs.GLenum,arrays.GLuintArray)
def glGetOcclusionQueryuivNV( id,pname,params ):pass


def glInitOcclusionQueryNV():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( EXTENSION_NAME )