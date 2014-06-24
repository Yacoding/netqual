import cherrypy
import os
import fcntl
import datetime

class DBServer(object):
	def __init__(self, db_dir, config_dir):
		self.db_dir = db_dir
		self.config_dir = config_dir

	def index_html(self):
		raise cherrypy.HTTPRedirect("/static/index.html")
	index_html.exposed = True

	@cherrypy.tools.response_headers(headers = [('Content-Type', 'text/plain'),('Access-Control-Allow-Origin', '*')])
	def data(self, project, res = "all"):
		return self.do_data(project, res)
	data.exposed = True

	def upload(self, data):
		return self.perform_upload(data)
	upload.exposed = True

	def get_projects(self):
		return self.perform_get_projects()
	get_projects.exposed = True

	def static(self):
		pass
	static._cp_config = {
		'tools.staticdir.on' : True,
		'tools.staticdir.dir' : os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "htmlstatic"),
		'tools.staticdir.index' : 'index.html'
	}
	static.exposed = True

	# -------

	def perform_upload(self, data):
		f = open(os.path.join(self.db_dir,"report.txt"), "r+")
		fcntl.flock(f.fileno(), fcntl.LOCK_EX)

		# Seek so as to append
		f.seek(0, os.SEEK_END)

		f.write(data)

		fcntl.flock(f.fileno(), fcntl.LOCK_UN)

	def perform_get_projects(self):
		f = open(os.path.join(self.config_dir,"projects.csv"))

		lines = f.readlines()

		projs = {}
		for l in lines:
			proj = l.split(",")[2]
			projs[proj] = True

		return "\n".join(projs.keys())

	def do_data(self, project, res):
		ret = ""
		f = open(os.path.join(self.config_dir,"projects.csv"))

		lines = f.readlines()

		macs = {}
		for l in lines:
			l = l.rstrip()

			if len(l) == 0:
				continue
			fields = l.split(",")
			if not macs.has_key(fields[3]):
				macs[fields[3]] = []

			date1 = fields[0]
			date2 = fields[1]

			date1parsed = parse_date(date1)
			if len(date2) > 0:
				date2parsed = parse_date(date2)
			else:
				date2parsed = None
			macs[fields[3]].append((date1parsed, date2parsed)) #range of dates

		f = open(os.path.join(self.db_dir,"report.txt"))
		for line in f:
			line = line.rstrip()
			fields = line.split(",")
			line_mac = fields[1]
			line_res = fields[2]
			line_dt = datetime.datetime.utcfromtimestamp(float(fields[0]))
			if not macs.has_key(line_mac):
				print "warning: didn't find mac {0} in projects".format(line_mac)
				continue
			for (d1,d2) in macs[line_mac]:
				if not d1 < line_dt:
					continue
				if d2 != None and not d2 > line_dt:
					continue

				if res != "all" and res != line_res:
					continue

				# If we made it here, there was a match
				ret += line + "\n"

		return ret


def parse_date(s):
	print "Parsing {0} {1}".format(s, datetime.datetime.strptime)
	return datetime.datetime.strptime(s, "%Y%m%d-%H%M%S")

#cherrypy_config = { '/index.html':
#	{
#		'tools.staticfile.on' : True,
#		'tools.staticfile.filename': os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "htmlstatic", "index.html"),
#	},
#}

def get_app(config=None):
	db_dir = os.environ.get("DB_DIR")
	config_dir = os.environ.get("CONFIG_DIR")

	cherrypy.tree.mount(DBServer(db_dir, config_dir), '', config=config)
	return cherrypy.tree


def start():
	get_app()
	cherrypy.config.update( {
		'server.socket_host': '0.0.0.0',
		'server.socket_port': 8081,
	} )
	cherrypy.engine.start()
	cherrypy.engine.block()

if __name__ == '__main__':
	# workaround strptime bug in multithreaded contexts
	datetime.datetime.strptime('', '')

	start()
