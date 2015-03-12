from flask import Flask
from flask_rethinkdb import RethinkDB
from flask.ext import restful
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

app = Flask(__name__)
app.config["RETHINKDB_DB"] = "dynaconfig"
app.config["SECRET_KEY"] = "dynaconfig"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

api = restful.Api(app)
db = RethinkDB()
db.init_app(app)

authDb = SQLAlchemy(app)
auth = HTTPBasicAuth()

class User(authDb.Model):
  __tablename__ = 'users'
  id = authDb.Column(authDb.Integer, primary_key=True)
  username = authDb.Column(authDb.String(32), index=True)
  password_hash = authDb.Column(authDb.String(64))

  def hash_password(self, password):
    self.password_hash = pwd_context.encrypt(password)

  def verify_password(self, password):
    return pwd_context.verify(password, self.password_hash)

  def generate_auth_token(self, expiration=600):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    return s.dumps({'id': self.id})

  @staticmethod
  def verify_auth_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
      data = s.loads(token)
    except SignatureExpired:
      return None    # valid token, but expired
    except BadSignature:
      return None    # invalid token
    user = User.query.get(data['id'])
    return user

@auth.verify_password
def verify_password(username_or_token, password):
  # first try to authenticate by token
  user = User.verify_auth_token(username_or_token)
  if not user:
    # try to authenticate with username/password
    user = User.query.filter_by(username=username_or_token).first()
    if not user or not user.verify_password(password):
      return False
  g.user = user
  return True

@app.route('/api/users', methods=['POST'])
def new_user():
  username = request.json.get('username')
  password = request.json.get('password')
  if username is None or password is None:
    abort(400)    # missing arguments
  if User.query.filter_by(username=username).first() is not None:
    abort(400)    # existing user
  user = User(username=username)
  user.hash_password(password)
  authDb.session.add(user)
  authDb.session.commit()
  return (jsonify({'username': user.username}), 201, {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/api/users/<int:id>')
def get_user(id):
  user = User.query.get(id)
  if not user:
    abort(400)
  return jsonify({'username': user.username})


@app.route('/api/token')
@auth.login_required
def get_auth_token():
  token = g.user.generate_auth_token(600)
  return jsonify({'token': token.decode('ascii'), 'duration': 600})

from dynaconfig.endpoints import Config, RevertConfig
api.add_resource(RevertConfig, "/config/revert/<string:config_name>/<string:config_environment>/<int:version>")
api.add_resource(Config, "/config/<string:config_name>/<string:config_environment>")

