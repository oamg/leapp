import subprocess, os, sys

inject = '''
import os, json
l, g = dict(), dict()
getter = """
import {{module}}
DB=getattr({{module}}, 'DATABASES', dict())
CACHE=getattr({{module}}, 'CACHES', dict())
"""
mod = os.environ['DJANGO_SETTINGS_MODULE']
exec(compile(getter.format(module=mod), '<generated>', 'exec'), g, l)
os.write({write}, json.dumps(dict(db=l['DB'],
                                  cache=l['CACHE']), indent=4))
os.close({write})
'''

target = None
if len(sys.argv) > 2:
    print("Invalid invocation: django_analyzer.py [MANAGE_PY]")
    exit(-1)
elif len(sys.argv) == 1:
    target = 'manage.py'
else:
    target = sys.argv[1]


r, w = os.pipe()
pid = os.fork()
if pid > 0:
    os.close(r)
    p = subprocess.Popen(['python', target, 'shell'], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=open(os.devnull, 'w'))
    p.communicate(inject.format(write=str(w)))
    os.close(w) # Popen forks underneath so we need to close `w` here as well
    os.wait()
else:
    os.close(w)
    while True:
        data = os.read(r, 1024)
        if not data:
            break
        print(data)
