import unittest
from dynaconfig.endpoints import RevertConfig

class TestRevertConfig(unittest.TestCase):

  def setUp(self):
    self.revert = RevertConfig()

  def test_RevertDoNotReverToSameVersion(self):
    self.assertRaises(AssertionError, self.revert._revert_config, {}, [], 0, 0)

  def test_RevertEmptyResultsInEmpty(self):
    config = self.revert._revert_config({}, [], 1, 0)
    self.assertEquals({}, config)

  def test_RevertDeleteToSingleValue(self):
    config = self.revert._revert_config({}, [
      {"created_at": 0, "version": 1, "changes": [{"key": "hello", "value": "world", "action": "removed"}]}
    ], 1, 0)
    self.assertEquals({"hello": "world"}, config)

  def test_RevertUpdateToSingleValue(self):
    config = self.revert._revert_config({"hello": "world"}, [
      {"created_at": 0, "version": 1, "changes": [{"key": "hello", "value": "world!", "action": "updated"}]}
    ], 1, 0)
    self.assertEquals({"hello": "world!"}, config)

  def test_RevertMultiValuwUpdateToSingleValue(self):
    config = self.revert._revert_config({"hello": "world", "do_not": "touch"}, [
      {"created_at": 0, "version": 1, "changes": [{"key": "hello", "value": "world!", "action": "updated"}]}
    ], 1, 0)
    self.assertEquals({"hello": "world!", "do_not": "touch"}, config)

  def test_RevertBackTwoVersions(self):
    config = self.revert._revert_config({"hello": "world!!"}, [
      {"created_at": 0, "version": 0, "changes": [{"key": "hello", "value": "world", "action": "added"}]},
      {"created_at": 0, "version": 1, "changes": [{"key": "hello", "value": "world!", "action": "updated"}]},
      {"created_at": 0, "version": 2, "changes": [{"key": "hello", "value": "world!!", "action": "updated"}]}
    ], 2, 0)
    self.assertEquals({"hello": "world"}, config)

  def test_GoForwardOneVersion(self):
    config = self.revert._revert_config({"hello": "world"}, [
      {"created_at": 0, "version": 1, "changes": [{"key": "hello", "value": "world!", "action": "updated"}]}
    ], 0, 1)
    self.assertEquals({"hello": "world!"}, config)

  def test_GoForwardTwoVersions(self):
    config = self.revert._revert_config({"hello": "world!!"}, [
      {"created_at": 0, "version": 0, "changes": [{"key": "hello", "value": "world", "action": "added"}]},
      {"created_at": 0, "version": 1, "changes": [{"key": "hello", "value": "world!", "action": "updated"}]},
      {"created_at": 0, "version": 2, "changes": [{"key": "hello", "value": "world!!", "action": "updated"}]}
    ], 0, 2)
    self.assertEquals({"hello": "world!!"}, config)
