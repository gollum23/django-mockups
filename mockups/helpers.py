# -*- coding: utf-8 -*-
import copy
from django.conf import settings
from django.utils.module_loading import module_has_submodule

# For django 1.8 and earlier
try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module

try:
    from django.apps import apps

    get_model = apps.get_model
except ImportError:
    # Support django < 1.8
    from django.db.models import get_model


__all__ = ('register', 'unregister', 'create', 'create_one', 'autodiscover')


_registry = {}


def get_mockup(model, *args, **kwargs):
    """
    Gets an mockup instance for a model
    """
    if model not in _registry:
        from mockups.base import Mockup
        cls = Mockup
    else:
        cls = _registry[model]
    return cls(model, *args, **kwargs)


def register(model, mockup_cls, overwrite=False, fail_silently=False):
    '''
    Register a model with the registry.

    Arguments:

        *model* can be either a model class or a string that contains the model's
        app label and class name seperated by a dot, e.g. ``"app.ModelClass"``.

        *mockup_cls* is the :mod:`Mockup` subclass that shall be used to
        generated instances of *model*.

        By default :func:`register` will raise :exc:`ValueError` if the given
        *model* is already registered. You can overwrite the registered *model* if
        you pass ``True`` to the *overwrite* argument.

        The :exc:`ValueError` that is usually raised if a model is already
        registered can be suppressed by passing ``True`` to the *fail_silently*
        argument.
    '''
    from django.db import models
    if isinstance(model, basestring):
        model = get_model(*model.split('.', 1))
    if not overwrite and model in _registry:
        if fail_silently:
            return
        raise ValueError(
            u'%s.%s is already registered. You can overwrite the registered '
            u'mockup class by providing the `overwrite` argument.' % (
                model._meta.app_label,
                model._meta.object_name,
            ))
    _registry[model] = mockup_cls


def unregister(model_or_iterable, fail_silently=False):
    '''
    Remove one or more models from the mockups registry.
    '''
    from django.db import models
    if not isinstance(model_or_iterable, (list, tuple, set)):
        model_or_iterable = [model_or_iterable]
    for model in model_or_iterable:
        if isinstance(model, basestring):
            model = get_model(*model.split('.', 1))
        try:
            del _registry[model]
        except KeyError:
            if fail_silently:
                continue
            raise ValueError(
                u'The model %s.%s is not registered.' % (
                    model._meta.app_label,
                    model._meta.object_name,
                ))


def create(model, count, *args, **kwargs):
    '''
    Create *count* instances of *model* using the either an appropiate
    mockup that was :ref:`registry <registry>` or fall back to the
    default:class:`Mockup` class. *model* can be a model class or its
    string representation (e.g. ``"app.ModelClass"``).

    All positional and keyword arguments are passed to the mockup
    constructor. It is demonstrated in the example below which will create ten
    superusers::

        import mockups
        mockup = mockups.create('auth.User', 10)

    .. note:: See :ref:`Mockup` for more information.

    :func:`create` will return a list of the created objects.
    '''
    # try:
    #     from django.apps import apps
    #     get_model = apps.get_model
    # except ImportError:
    #     from django.db.models import get_model
    if isinstance(model, basestring):
        model = get_model(*model.split('.', 1))
    mockup = get_mockup(model, *args, **kwargs)
    return mockup.create(count)


def create_one(model, *args, **kwargs):
    '''
    :func:`create_one` is exactly the as the :func:`create` function but a
    shortcut if you only want to generate one model instance.

    The function returns the instanciated model.
    '''
    return create(model, 1, *args, **kwargs)[0]



def autodiscover():
    """
    Auto-discover INSTALLED_APPS mockup.py modules and fail silently when
    not present. This forces an import on them to register any mockup bits they
    may want.
    """

    global _registry


    import imp
    try:
        from django.apps import apps

        for app_config in apps.get_app_configs():
            _registry[app_config.name] = [app_config.path]

    except ImportError:

        for app in settings.INSTALLED_APPS:
            mod = import_module(app)
            # Attempt to import the app's mockup module.
            try:
                before_import_registry = copy.copy(_registry)
                import_module('%s.mockup' % app)
            except:
                # Reset the model registry to the state before the last import as
                # this import will have to reoccur on the next request and this
                # could raise NotRegistered and AlreadyRegistered exceptions
                # (see #8245).
                _registry = before_import_registry

                # Decide whether to bubble up this error. If the app just
                # doesn't have an mockup module, we can ignore the error
                # attempting to import it, otherwise we want it to bubble up.
                if module_has_submodule(mod, 'mockup'):
                    raise

