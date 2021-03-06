# -*- coding: utf-8 -*-
# Support functions, classes
from wsgiref import util
from watson.console import command
from watson.http.messages import Response
from watson.mvc import controllers
from watson.mvc.views import Model


def start_response(status_line, headers):
    pass


def sample_environ(**kwargs):
    environ = {}
    util.setup_testing_defaults(environ)
    environ.update(kwargs)
    return environ


class SampleActionController(controllers.Action):

    def something_action(self, **kwargs):
        return 'something_action'

    def blah_action(self):
        return 'blah_action'

    def blah_syntax_error_action(self):
        a = b


class ShortCircuitedController(controllers.Rest):

    def GET(self):
        return Response(body='testing')


class SampleRestController(controllers.Rest):

    def GET(self):
        return 'GET'


def sample_view_model():
    return (
        Model(
            format='html', template=None, data={"test": {"nodes": {"node": ["Testing", "Another node"]}}})
    )


class TestController(controllers.Rest):

    def GET(self):
        return 'Hello World!'

    def POST(self):
        return 'Posted Hello World!'


class SampleNonStringCommand(command.Base):
    name = 'nonstring'


class SampleStringCommand(command.Base):
    name = 'string'

    def execute(self):
        return 'Executed!'
