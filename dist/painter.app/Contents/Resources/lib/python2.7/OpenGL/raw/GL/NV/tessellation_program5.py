'''Autogenerated by get_gl_extensions script, do not edit!'''
from OpenGL import platform as _p
from OpenGL.GL import glget
EXTENSION_NAME = 'GL_NV_tessellation_program5'
_p.unpack_constants( """GL_MAX_PROGRAM_PATCH_ATTRIBS_NV 0x86D8
GL_TESS_CONTROL_PROGRAM_NV 0x891E
GL_TESS_EVALUATION_PROGRAM_NV 0x891F
GL_TESS_CONTROL_PROGRAM_PARAMETER_BUFFER_NV 0x8C74
GL_TESS_EVALUATION_PROGRAM_PARAMETER_BUFFER_NV 0x8C75""", globals())


def glInitTessellationProgram5NV():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( EXTENSION_NAME )
