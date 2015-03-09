import datetime
import rethinkdb as r

from flask import request
from flask.ext.restful import Resource, abort

from dynaconfig import db

class Config(Resource):

  def get(self, user_id, config_name):
    config = r.table("config").get_all("{}-{}".format(user_id, config_name), index="name").run(db.conn)
    return config.next()

  def post(self, user_id, config_name):
    config = self._default_values(user_id, config_name)
    response = r.table("config").insert(config).run(db.conn)

    if response["inserted"] < 1:
      abort(500, "Could not create config with name '{}'".format(config_name))
    else:
      config["id"] = response["generated_keys"][0]

      return config



  def _validate_config(self, json):
    return "name" in json

  def _default_values(self, user_id, config_name):
    _config = {}
    _config["name"] = "{}-{}".format(user_id, config_name)
    _config["current_version"] = 0
    _config["last_version"] = 0
    _config["highest_version"] = 0
    return _config

class ConfigValues(Resource):

  def get(self, user_id, config_name):
    pass

  def post(self, user_id, config_name):
    values = request.json

    response = r.table("config").get_all("{}-{}".format(user_id, config_name), index="name").run(db.conn)
    response = list(response)
  
    if response:
      config = response[0]
      config["highest_version"] = config["highest_version"] + 1
      current_version = config["highest_version"]


      old_values = r.table("config_values").get_all("{}-{}".format(user_id, config_name), index="config_id").run(db.conn)
      old_values = list(old_values)

      _id = None
      old_audit = []
      if not old_values:
        old_values = []
      else:
        old_config = old_values[0]
        _id = old_config["id"]
        old_audit = old_config["audit_trail"]
        old_values = old_config["values"]

      if not _id:
        response = r.table("config_values").insert({
          "config_id": "{}-{}".format(user_id, config_name),
          "version": current_version,
          "values": values,
          "audit_trail": [self._create_audit(old_values, values, current_version)]
        }).run(db.conn)
      else:
        new_audit = self._create_audit(old_values, values, current_version)
        if len(new_audit["changes"]) > 0:
          old_audit.append(new_audit)
          response = r.table("config_values").get(_id).update({
            "version": current_version,
            "values": r.literal(values),
            "audit_trail": r.doc["audit_trail"].default([]).append(new_audit)
          }).run(db.conn)

          r.table("config").get_all("{}-{}".format(user_id, config_name), index="name").update({
            "highest_version": r.row["highest_version"] + 1,
            "current_version": r.row["highest_version"] + 1
          }).run(db.conn)
        else:
          return "No Change"

      return response

  def _create_audit(self, old_values, new_values, version):
    audit_values = []

    for k in old_values:
      if k in new_values:
        if old_values[k] != new_values[k]:
          audit_values.append({"key": k, "action": "updated", "value": new_values[k]})
      else:
        audit_values.append({"key": k, "action": "removed"})

    new_keys = set(new_values.keys()).difference(set(old_values))

    for k in new_keys:
      audit_values.append({"key": k, "action": "added", "value": new_keys[k]})

    return {"created_at": r.now(), "changes": audit_values, "version": version}

