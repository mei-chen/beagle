'''Serve a sense2vec model over a GET request.'''
# from sense2vec_service_word.service import load

from service.service import load

APP = load()

if __name__ == '__main__':
    from wsgiref import simple_server
    httpd = simple_server.make_server('127.0.0.1', 8000, APP)
    print("the server is running on port 8000")
    httpd.serve_forever()




