import datetime
import rethinkdb as r

from flask import request
from flask.ext.restful import Resource, abort

from dynaconfig import db

from time import time

class Config(Resource):

  def get(self, user_id, config_name):
    current_config = list(r.table("config").get_all("{}-{}".format(user_id, config_name), index="name").run(db.conn))

    if current_config:
      return current_config[0]
    else:
      return abort(404, message="Could not find config with name='{}' for user id={}".format(config_name, user_id))

  def post(self, user_id, config_name):
    values = request.json

    current_config = list(r.table("config").get_all("{}-{}".format(user_id, config_name), index="name").run(db.conn))
    if current_config:
      current_config = current_config[0]
      old_audit = current_config["values"]

      _id = current_config["id"]
      old_audit = current_config["audit_trail"]
      old_values = current_config["values"]
      current_version = current_config["highest_version"] + 1

      new_audit = self._create_audit(old_values, values, current_version)
      if new_audit["changes"]:
        return r.table("config").get(_id).update({
          "version": r.row["highest_version"] + 1,
          "last_version": r.row["version"],
          "highest_version": r.row["highest_version"] + 1,
          "values": r.literal(values),
          "audit_trail": r.row["audit_trail"].default([]).append(new_audit)
        }).run(db.conn)
      else:
        return abort(302, message="Config did not change")
    else:
      return r.table("config").insert({
        "name": "{}-{}".format(user_id, config_name),
        "version": 0,
        "highest_version": 0,
        "last_version": 0,
        "values": values,
        "audit_trail": [self._create_audit({}, values, 0)]
      }).run(db.conn)

  def _create_audit(self, old_values, new_values, version):
    audit_values = []

    for k in old_values:
      if k in new_values:
        if old_values[k] != new_values[k]:
          audit_values.append({"key": k, "action": "updated", "value": new_values[k]})
      else:
        audit_values.append({"key": k, "action": "removed", "value": old_values[k]})

    new_keys = set(new_values.keys()).difference(set(old_values.keys()))

    for k in new_keys:
      audit_values.append({
        "key": k,
        "action": "added",
        "value": new_values[k]
      })

    return {"created_at": int(time() * 1000), "changes": audit_values, "version": version}

class RevertConfig(Resource):

  def put(self, user_id, config_name, version):
    current_config = list(r.table("config").get_all("{}-{}".format(user_id, config_name), index="name").run(db.conn))
    if current_config:
      current_config = current_config[0]

      if 0 <= version < current_config["highest_version"]:
        pass
      else:
        return abort(404, message="Version={} for config with name='{}' for user id={} could not be found".format(version, config_name, user_id))
    else:
      return abort(404, message="Could not find config with name='{}' for user id={}".format(config_name, user_id))

  def _revert_config(self, config, audits, current_version, expected_version):
    assert(not current_version == expected_version)

    if current_version > expected_version:
      changes =[a for audit_map in map(lambda audit: audit["changes"] if audit["version"] > expected_version else [], audits) for a in audit_map]
    elif expected_version > current_config:
      changes =[a for audit_map in map(lambda audit: audit["changes"] if audit["version"] < expected_version else [], audits) for a in audit_map]

    for change in changes:
      action = change["action"]
      key = change["key"]
      value = change["value"]
      if action in ["updated", "removed"]:
        config[key] = value
      elif action == "added":
        del config[key]

    return config

