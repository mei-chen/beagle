
from service.service import load

APP = load()

if __name__ == '__main__':
    from wsgiref import simple_server
    httpd = simple_server.make_server('127.0.0.1', 3000, APP)
    print("the Delorean is running on port 3000")
    httpd.serve_forever()




