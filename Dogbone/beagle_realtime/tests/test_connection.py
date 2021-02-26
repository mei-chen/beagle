from django.test import TestCase
import mock

from beagle_realtime.base import RedisConnection


class ConnectionTestCase(TestCase):

    def setUp(self):
        self.url = 'redis://localhost:6379/0'

    def test_raise_exception(self):
        conn = RedisConnection()

        with mock.patch('beagle_realtime.base.redis.StrictRedis.from_url',
                        side_effect=Exception('Apocalypto!')) as mock_redis:
            redis_conn = conn.get_connection()
            mock_redis.assert_called_once_with(self.url)
            self.assertIsNone(redis_conn)

    def test_return_false(self):
        conn = RedisConnection()

        with mock.patch('beagle_realtime.base.redis.StrictRedis.from_url',
                        return_value=False) as mock_redis:
            redis_conn = conn.get_connection()
            mock_redis.assert_called_once_with(self.url)
            self.assertFalse(redis_conn)

    def test_return_true(self):
        conn = RedisConnection()

        with mock.patch('beagle_realtime.base.redis.StrictRedis.from_url',
                        return_value=True) as mock_redis:
            redis_conn = conn.get_connection()
            mock_redis.assert_called_once_with(self.url)
            self.assertTrue(redis_conn)
