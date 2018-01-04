from __future__ import absolute_import, print_function, unicode_literals

from io import StringIO
try:
    from unittest import mock
except ImportError:
    import mock

import simplejson as json
import pytest

from pystorm.exceptions import StormWentAwayError
from pystorm.serializers.json_cbor_serializer import JSONCBORSerializer

from .serializer import SerializerTestCase


class TestJSONSerializer(SerializerTestCase):

    INSTANCE_CLS = JSONCBORSerializer

    def test_read_message_dict_with_normal_tuple(self):
        msg_dict = {'hello': "world", 'tuple': [1, 2, 3]}
        self.instance.input_stream = StringIO(self.instance.serialize_dict(msg_dict))
        assert self.instance.read_message() == msg_dict

    def test_read_message_dict_with_cbor_tuple(self):
        msg_dict = {'hello': "world", 'tuple': '\x82\xa1ehelloeworld\x01'}
        self.instance.input_stream = StringIO(self.instance.serialize_dict(msg_dict))
        assert self.instance.read_message() == msg_dict

    def test_read_message_list(self):
        msg_list = [3, 4, 5]
        self.instance.input_stream = StringIO(self.instance.serialize_dict(msg_list))
        assert self.instance.read_message() == msg_list

    def test_send_message(self):
        msg_dict = {'hello': "world", 'tuple': [{'hello': 'world'}, 1]}
        expected_output = """{"hello": "world", "tuple": "gqFlaGVsbG9ld29ybGQB"}\nend\n"""
        self.instance.output_stream = StringIO()
        self.instance.send_message(msg_dict)
        assert self.instance.output_stream.getvalue() == expected_output

    def test_send_message_raises_stormwentaway(self):
        string_io_mock = mock.MagicMock(autospec=True)
        def raiser(): # lambdas can't raise
            raise IOError()
        string_io_mock.flush.side_effect = raiser
        self.instance.output_stream = string_io_mock
        with pytest.raises(StormWentAwayError):
            self.instance.send_message({'hello': "world",})

    @mock.patch('pystorm.serializers.serializer.log.exception', autospec=True)
    def test_send_message_bad_value(self, log_mock):
        msg_dict = {'hello': b'\xfc\x89'}
        self.instance.output_stream = StringIO()
        self.instance.send_message(msg_dict)
        log_mock.assert_called_with('Failed to send message: %r', msg_dict)
