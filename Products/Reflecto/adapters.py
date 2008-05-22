from zope.component import getUtility

from interfaces import IReflectoConfiguration

def form_adapter(context):
    return getUtility(IReflectoConfiguration,
                      name='reflecto_config',
                      context=context)
