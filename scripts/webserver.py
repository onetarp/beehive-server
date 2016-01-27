#!/usr/bin/env python
import web, os.path, logging, re, urlparse, sys, json
from export import export_generator, list_node_dates
# container
# docker run -it  --link beehive-cassandra:cassandra --rm -p 80:80 waggle/beehive-server /usr/lib/waggle/beehive-server/scripts/webserver.py 
# optional: -v ${DATA}/export:/export

LOG_FORMAT='%(asctime)s - %(name)s - %(levelname)s - line=%(lineno)d - %(message)s'
formatter = logging.Formatter(LOG_FORMAT)

handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)

logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logging.getLogger('export').setLevel(logging.DEBUG)


port = 80
self_url = 'http://beehive1.mcs.anl.gov'

web.config.log_toprint = True


def read_file( str ):
    print "read_file: "+str
    if not os.path.isfile(str) :
        return ""
    with open(str,'r') as file_:
        return file_.read().strip()
    return ""





urls = (
    '/api/1/nodes/(.+)/latest',     'api_nodes_latest',
    '/api/1/nodes/(.+)/export',     'api_export',
    '/api/1/nodes/(.+)/dates',      'api_dates',
    '/api/1/nodes/',                'api_nodes',
    '/nodes/(.+)',                  'web_node_page',
    '/',                            'index'
)

app = web.application(urls, globals())



    
    
class index:        
    def GET(self):
        
        web.header('Content-type','text/html')
        web.header('Transfer-Encoding','chunked')
        
        
        yield "This is the Waggle Beehive web server.\n\n\n"
        
        # TODO: use API call !
        nodes_dict = list_node_dates()
        for node_id in nodes_dict.keys():
            yield '<a href="%s/nodes/%s/">node_id</a><br>' % (self_url, node_id)
        
        yield "\n\nAvailable API resources:\n\n"
        
        
        for i in range(0, len(urls), 2):
            yield  "    " +  urls[i] + "\n"
        
        
        
class web_node_page:
    def GET(self, node_id):
        web.header('Content-type','text/html')
        web.header('Transfer-Encoding','chunked')
        #TODO check that node_id exists!
        
        yield "Node "+node_id+"\n\n\n"
        
        nodes_dict = list_node_dates()
        
        if not node_id in nodes_dict:
            raise web.notfound()
        
        for date in nodes_dict[node_id]:
            yield '<a href="%s/api/1/nodes/%s/export?date=%s">%s</a><br>' % (self_url, node_id, date, node_id)


class api_nodes:        
    def GET(self):
        
        #query = web.ctx.query
        
        
        #web.header('Content-type','text/plain')
        #web.header('Transfer-Encoding','chunked')
        
        nodes_dict = list_node_dates()
        
        obj = {}
        obj['data'] = nodes_dict.keys()
        
        return  json.dumps(obj, indent=4)
        
            
class api_dates:        
    def GET(self, node_id):
        
        query = web.ctx.query
        
        nodes_dict = list_node_dates()
        
        if not node_id in nodes_dict:
            raise web.notfound()
        
        
        obj = {}
        obj['data'] = nodes_dict[node_id]
        
        return json.dumps(obj, indent=4)
        
        
        
                        

class api_nodes_latest:        
    def GET(self, node_id):
        
        query = web.ctx.query
        
        
        web.header('Content-type','text/plain')
        web.header('Transfer-Encoding','chunked')
        
        for row in export_generator(node_id, '', True):
            yield row+"\n"



class api_export:        
    def GET(self, node_id):
        web.header('Content-type','text/plain')
        web.header('Transfer-Encoding','chunked')
        
        query = web.ctx.query.encode('ascii', 'ignore') #get rid of unicode
        if query:
            query = query[1:]
        #TODO parse query
        logger.info("query: %s", query)
        query_dict = urlparse.parse_qs(query)
        
        try:
            date_array = query_dict['date']
        except KeyError:
            logger.warning("date key not found")
            raise web.notfound()
        
        if len(date_array) == 0:
            logger.warning("date_array empty")
            raise web.notfound()
        date = date_array[0]
            
        logger.info("date: %s", str(date))
        if date:
            r = re.compile('\d{4}-\d{1,2}-\d{1,2}')
            if r.match(date):
                logger.info("accepted date: %s" %(date))
    
                for row in export_generator(node_id, date, False):
                    yield row+"\n"
            else:
                logger.warning("date format not correct")
                raise web.notfound()
        else:
            logger.warning("date is empty")
            raise web.notfound()

if __name__ == "__main__":
    web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))
    app.run()



