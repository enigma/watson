# -*- coding: utf-8 -*-
import abc
import collections
import re
from watson.di import ContainerAware
from watson.events.types import Event
from watson.http.messages import Response, Request
from watson.common.imports import get_qualified_name
from watson.common.contextmanagers import ignored


class Base(ContainerAware, metaclass=abc.ABCMeta):

    """The base class for all controllers.
    """

    """The interface for controller classes.
    """
    @abc.abstractmethod
    def execute(self, **kwargs):
        raise NotImplementedError(
            'You must implement execute')  # pragma: no cover

    @abc.abstractmethod
    def get_execute_method_path(self, **kwargs):
        raise NotImplementedError(
            'You must implement get_execute_method_path')  # pragma: no cover

    def __repr__(self):
        return '<{0}>'.format(get_qualified_name(self))


class HttpMixin(object):

    """A mixin for controllers that can contain http request and response
    objects.

    Attributes:
        _request: The request made that has triggered the controller
        _response: The response that will be returned by the controller
    """
    _request = None
    _response = None
    _event = None

    @property
    def event(self):
        """The event that was triggered that caused the execution of the
        controller.

        Returns:
            watson.events.types.Event
        """
        return self._event

    @event.setter
    def event(self, event):
        """Set the request object.

        Args:
            watson.events.types.Event event: The triggered event.

        Raises:
            TypeError if the event type is not a subclass of
            watson.events.types.Event
        """
        if not isinstance(event, Event):
            raise TypeError(
                'Invalid request type, expected watson.events.types.Event')
        self._event = event

    @property
    def request(self):
        """The HTTP request relating to the controller.

        Returns:
            watson.http.messages.Request
        """
        return self._request

    @request.setter
    def request(self, request):
        """Set the request object.

        Args:
            watson.http.messages.Request request: The request associated with
            the controller.

        Raises:
            TypeError if the request type is not of
            watson.http.messages.Request
        """
        if not isinstance(request, Request):
            raise TypeError(
                'Invalid request type, expected watson.http.messages.Request')
        self._request = request

    @property
    def response(self):
        """The HTTP response related to the controller.

        If no response object has been set, then a new one will be generated.

        Returns:
            watson.http.messages.Response
        """
        if not self._response:
            self.response = Response()
        return self._response

    @response.setter
    def response(self, response):
        """Set the request object.

        Args:
            watson.http.messages.Response response: The response associated
            with the controller.

        Raises:
            TypeError if the request type is not of
            watson.http.messages.Response
        """
        if not isinstance(response, Response):
            raise TypeError(
                'Invalid response type, expected watson.http.messages.Response')
        self._response = response

    def url(self, route_name, **params):
        """Converts a route into a url.

        Args:
            string route_name: The name of the route to convert
            dict params: The params to use on the route

        Returns:
            The assembled url.
        """
        if not params:
            params = {}
        router = self.container.get('router')
        return router.assemble(route_name, **params)

    def redirect(self, path, params=None, status_code=302, clear=False):
        """Redirect to a different route.

        Redirecting will bypass the rendering of the view, and the body of the
        request will be displayed.

        Also supports Post Redirect Get (http://en.wikipedia.org/wiki/Post/Redirect/Get)
        which can allow post variables to accessed from a GET resource after a
        redirect (to repopulate form fields for example).

        Args:
            string path: The URL or route name to redirect to
            dict params: The params to send to the route
            int status_code: The status code to use for the redirect
            bool clear: Whether or not the session data should be cleared

        Returns:
            A watson.http.messages.Response object.
        """
        self.response.status_code = status_code
        if self.request.is_method(('POST', 'PUT')):
            self.response.status_code = status_code if status_code != 302 else 303
            self.request.session['post_redirect_get'] = dict(self.request.post)
        if clear:
            self.clear_redirect_vars()
        try:
            url = self.url(path, **params or {})
        except KeyError:
            url = path
        self.response.headers.add('location', url, replace=True)
        return self.response

    @property
    def redirect_vars(self):
        """Returns the post variables from a redirected request.
        """
        return self.request.session.get('post_redirect_get', {})

    def clear_redirect_vars(self):
        """Clears the redirected variables.
        """
        del self.request.session['post_redirect_get']

    @property
    def flash_messages(self):
        """Retrieves all the flash messages associated with the controller.

        Usage:
            # within controller action
            self.flash_messages.add('Some message')
            return {
                'flash_messages': self.flash_messages
            }

            # within view
            {% for namespace, message in flash_messages %}
                {{ message }}
            {% endfor %}

        Returns:
            A watson.mvc.controllers.FlashMessagesContainer object.
        """
        if not hasattr(self, '_flash_messages_container'):
            self._flash_messages_container = FlashMessagesContainer(
                self.request.session)
        return self._flash_messages_container


class FlashMessagesContainer(object):

    """Contains all the flash messages associated with a controller.

    Flash messages persist across requests until they are displayed to the user.
    """
    messages = None
    session = None
    session_key = 'flash_messages'

    def __init__(self, session):
        """Initializes the container.

        Args:
            watson.http.session.StorageMixin session: A session object containing
                the flash messages data.
        """
        self.session = session
        if self.session_key in self.session:
            self.messages = self.session[self.session_key].messages
        else:
            self.clear()
        self.session[self.session_key] = self

    def add(self, message, namespace='info'):
        """Adds a flash message within the specified namespace.

        Args:
            string message: The message to add to the container.
            string namespace: The namespace to sit the message in.
        """
        if namespace not in self.messages:
            self.messages[namespace] = []
        self.messages[namespace].append(message)

    def add_messages(self, messages, namespace='info'):
        """Adds a list of messages to the specified namespace.

        Args:
            list|tuple messages: The messages to add to the container.
            string namespace: The namespace to sit the messages in.
        """
        for message in messages:
            self.add(message, namespace)

    def clear(self):
        """Clears the flash messages from the container and session.

        This is called automatically after the flash messages have been
        iterated over.
        """
        with ignored(KeyError):
            del self.session[self.session_key]
        self.messages = collections.OrderedDict()

    # Internals

    def __iter__(self):
        for namespace, messages in self.messages.items():
            for message in messages:
                yield (namespace, message)
        else:
            self.clear()

    def __getitem__(self, key):
        return self.messages.get(key)

    def __len__(self):
        return len(self.messages)

    def __repr__(self):
        return (
            '<{0} messages: {1}>'.format(get_qualified_name(self), len(self))
        )


class Action(Base, HttpMixin):

    """A controller thats methods can be accessed with an _action suffix.

    Usage:
        class MyController(controllers.Action):
            def my_func_action(self):
                return 'something'
    """

    def execute(self, **kwargs):
        method_name = kwargs.get('action', 'index') + '_action'
        method = getattr(self, method_name)
        try:
            result = method(**kwargs)
        except TypeError as exc:
            exc_msg = str(exc)
            # There has to be a better/quicker way to determine if the cause
            # is because of kwargs
            if 'required positional argument' not in exc_msg \
                    and not exc_msg.startswith(method_name):
                raise exc
            result = method()
        return result

    def get_execute_method_path(self, **kwargs):
        template = re.sub('.-', '_', kwargs.get('action', 'index').lower())
        return [self.__class__.__name__.lower(), template]


class Rest(Base, HttpMixin):

    """A controller thats methods can be accessed by the request method name.

    Usage:
        class MyController(controllers.Rest):
            def GET(self):
                return 'something'
    """

    def execute(self, **kwargs):
        method = getattr(self, self.request.method)
        try:
            result = method(**kwargs)
        except TypeError as exc:
            exc_msg = str(exc)
            # There has to be a better/quicker way to determine if the cause
            # is because of kwargs
            if 'required positional argument' not in exc_msg \
                    and not exc_msg.startswith(self.request.method):
                raise exc
            result = method()
        return result

    def get_execute_method_path(self, **kwargs):
        template = self.request.method.lower()
        return [self.__class__.__name__.lower(), template]
