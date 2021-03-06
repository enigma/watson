# -*- coding: utf-8 -*-
from watson.filters.string import Trim, RegEx, Numbers, Upper, Lower, StripTags, HtmlEntities


class TestTrim(object):

    def test_trim_string(self):
        filter = Trim()
        assert filter(' Test') == 'Test'
        assert filter('Test') == 'Test'


class TestUpper(object):

    def test_to_upper(self):
        filter = Upper()
        assert filter('test') == 'TEST'


class TestLower(object):

    def test_to_upper(self):
        filter = Lower()
        assert filter('TEST') == 'test'


class TestRegEx(object):

    def test_replace_string(self):
        filter = RegEx('ing', replacement='ed')
        assert filter('testing') == 'tested'


class TestNumbers(object):

    def test_remove_numbers(self):
        filter = Numbers()
        assert filter('ab1234') == '1234'


class TestStripTags(object):

    def test_strip_tags(self):
        filter = StripTags()
        assert filter('test<div>blah</div>') == 'testblah'


class TestHtmlEntities(object):

    def test_encode(self):
        filter = HtmlEntities()
        assert filter('<div>test</div>') == '&lt;div&gt;test&lt;/div&gt;'
