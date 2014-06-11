import cherrypy
import os

class DBServer(object):
	def __init__(self, db_dir):
		self.db_dir = db_dir

	@cherrypy.tools.response_headers(headers = [('Content-Type', 'text/plain'),('Access-Control-Allow-Origin', '*')])
	def data(self):
		return open(os.path.join(self.db_dir,"report.txt")).read()
	data.exposed = True

def get_app(config=None):
	db_dir = os.environ.get("DB_DIR")

	cherrypy.tree.mount(DBServer(db_dir), '/', config=config)
	return cherrypy.tree


def start():
	get_app()
	cherrypy.engine.start()
	cherrypy.engine.block()

if __name__ == '__main__':
	start()
