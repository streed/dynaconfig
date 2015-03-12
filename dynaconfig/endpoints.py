import datetime
import rethinkdb as r

from flask import request, g
from flask.ext.restful import Resource, abort

from dynaconfig import db, auth

from time import time

def config_id(config_name, config_environment):

  return "{}-{}-{}".format(g.user.id, config_name, config_environment)

class Config(Resource):

  decorators = [auth.login_required]

  def get(self, config_name, config_environment):
    current_config = r.table("config").get(config_id(config_name, config_environment)).run(db.conn)

    if current_config:
      return current_config
    else:
      return abort(404, message="Could not find config with name='{}' for user id={}".format(config_environment, config_name))

  def post(self, config_name, config_environment):
    values = request.json

    current_config = r.table("config").get(config_id(config_name, config_environment)).run(db.conn)
    if current_config:
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
        "id": config_id(config_name, config_environment),
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

  decorators = [auth.login_required]

  def put(self, config_name, config_environment, version):
    current_config = r.table("config").get(config_id(config_name, config_environment)).run(db.conn)
    if current_config:
        current_version = current_config["version"]
        audit_trail = current_config["audit_trail"]
        values = self._revert_config(current_config["values"], audit_trail, version, current_version)
        return r.table("config").get(_id).update({
          "version": version,
          "last_version": r.row["version"],
          "values": r.literal(values)
        }).run(db.conn)
      else:
        return abort(404, message="Version={} for config with name='{}' for user id={} could not be found".format(version, config_environment, config_name))
    else:
      return abort(404, message="Could not find config with name='{}' for user id={}".format(config_environment, config_name))

  def _revert_config(self, config, audits, current_version, expected_version):
    assert(not current_version == expected_version)

    if current_version > expected_version:
      changes = reversed([a for audit_map in map(lambda audit: audit["changes"] if audit["version"] >= expected_version else [], audits) for a in audit_map])
    elif expected_version > current_version:
      changes =[a for audit_map in map(lambda audit: audit["changes"] if audit["version"] <= expected_version else [], audits) for a in audit_map]

    for change in changes:
      action = change["action"]
      key = change["key"]
      value = change["value"]
      if action in ["updated", "removed"]:
        config[key] = value
      elif action == "added":
        if expected_version == 0:
          config[key] = value
        else:
          del config[key]

    return config

