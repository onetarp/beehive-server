from . import web 

@web.route('/')
def web_root():
    return 'You found web!!!'

@web.route("/wcc/test/")
def hello():
    rl = [] # result list

    rl.append("<h1 style='color:green'>Hello There!</h1>")
    rl.append('args = ' + str(request.args))
    rl.append('<br>')
    d = request.args.to_dict()
    rl.append('to_dict = ' + str(d))
    rl.append('<br>')
    rl.append('<br>')
    rl.append('items:  ' + str(d.items()))
    rl.append('<br>')
    rl.append('<br>')
    for x in d.keys():
        rl.append('   {} : {} <br>'.format(x, d[x]))
    debug = request.args.get('debug', 'False')
    rl.append('<br>')
    rl.append('debug :  {}'.format(debug))
    return ''.join(rl)
    
    