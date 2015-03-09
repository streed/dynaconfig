from dynaconfig.endpoints import Config
import unittest

class ConfigTest(unittest.TestCase):

  def setUp(self):
    self.config = Config()

  def test_TestCreateNullAuditTrail(self):
    audit = self.config._create_audit({}, {}, 0)["changes"]
    self.assertEquals([], audit)

  def test_TestCreateAddedSingleValues(self):
    audit = self.config._create_audit({}, {"hello": "world"}, 0)["changes"]
    self.assertEquals([{"key": "hello", "value": "world", "action": "added"}], audit)

  def test_TestModifySingleValue(self):
    audit = self.config._create_audit({"hello": "world!"}, {"hello": "world"}, 0)["changes"]
    self.assertEquals([{"key": "hello", "value": "world", "action": "updated"}], audit)

  def test_TestDeletingSingleValue(self):
    audit = self.config._create_audit({"hello": "world!"}, {}, 0)["changes"]
    self.assertEquals([{"key": "hello", "value": "world!", "action": "removed"}], audit)
