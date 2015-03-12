import sys
from dynaconfig import app, authDb

if __name__ == "__main__":
  if len(sys.argv) == 2 and sys.argv[1] == "db":
    print "Creating tables"
    authDb.create_all()
  app.run(debug=True)
