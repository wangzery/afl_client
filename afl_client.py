#/bin/python
import httplib
import re
import socket
import time
import urllib
import urllib2
from threading import Timer


# used by afl_client, afl_client will call fuzz-func(s) and exit func
class SendFuzzReq:
    host = ''
    url = ''
    prot = ''
    headers = ''
    body = ''
    HeaderKeys = {}
    fuzzCase = ''
    httpConn = 0
    mothed = ''

    def __init__(self, fuzzCase):
        self.initReq()
        self.setFuzzCase(fuzzCase)

    def setHost(self, host):
        self.host = host

    def setHeaders(self, headers):
        self.headers = headers 

    def setBody(self, data):
        if isinstance(data,str):
            #self.data = urllib.urlencode(data)
            self.body = data
        else:
            self.body = "%s"%data
            

    def insertHeader(self, headerKey, headerValue):
        for HeaderKey in self.HeaderKeys:
            if headerKey == HeaderKey:
                self.headers[headerKey] = headerValue

    
    def setFuzzCase(self, fuzzCase):
        self.fuzzCase = fuzzCase

    def initReq(self):
        self.setHost('www.baidu.com')
        self.port = 80
        self.url = '/'
        self.headers = {'User-Agent':'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)', 
        'Accept':'text/plain', 
        'Accept-Language':'en-US', 
        'Authorization':'Basic OSdjJGRpbjpvcGVuIANlc2SdDE==',
        'Proxy-Authorization':'Basic IOoDZRgDOi0vcGVuIHNlNidJi2==',
        'Connection':'keep-alive',
        'Proxy-Connection':'keep-alive',
        'Cookie':'$Version=1; Skin=new;',
        'Date':'Dec, 26 Dec 2017 17:30:00 GMT',
        'Host':'1.1.1.1:80',
        'Content-Type':'application',
        'Content-Length':'999',
        }
        self.headers = {'User-Agent':'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        self.HeaderKeys = self.headers.keys()
        self.body = "test by afl-fuzz"

    def getHttpConn(self):
        if not self.httpConn:
            self.httpConn = httplib.HTTPConnection(host=self.host, port=self.port, timeout=5)
        return self.httpConn


    def sendReq(self):
        #req = urllib2.Request(self.url, self.data, self.headers) 
        #req = urllib2.Request(self.url, self.data) 
        #response = urllib2.urlopen(req)
        httpConn = self.getHttpConn()
        httpConn.request(method=self.method,url=self.url, body=self.body, headers=self.headers)

        httpRep = httpConn.getresponse()
        self.rep = httpRep.read()
        headers = httpRep.getheaders()
        if httpRep:
            #print self.rep
            #print headers
            return True
        else:
            return False

    def sendExitReq(self):
        self.initReq()
        self.setBody(None)
        self.method = 'GET'
        self.insertHeader('User-Agent','afl_fuzz_exit')
        
        ret = self.sendReq()
        if ret:
            return True
        else:
            return False
    
    def fuzzHttpHeaders(self, headerKey):
        self.initReq()
        self.insertHeader(headerKey, self.fuzzCase)
        self.method = 'GET'
        ret = self.sendReq()
        if ret:
            if self.sendExitReq():
                return True
        else:
            return False

    def fuzzHttpData(self):
        self.initReq()
        self.setHost('www.baidu.com')
        self.setBody(self.fuzzCase)
        self.method = 'POST'
        ret = self.sendReq()
        if ret:
            if self.sendExitReq():
                return True
        else:
            return False

#add afl-client here:
class afl_client:
    host = ''
    port = 0
    timer = 0
    header2bFuzz = 0

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def conn2Srv(self):
        
        httpConn = httplib.HTTPConnection(host='127.0.0.1', port=8000, timeout=5)

        headers1 = {'User-Agent':'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)', 
        'Accept':'text/plain', 
        'Accept-Language':'en-US', 
        'Authorization':'Basic OSdjJGRpbjpvcGVuIANlc2SdDE==',
        'Proxy-Authorization':'Basic IOoDZRgDOi0vcGVuIHNlNidJi2==',
        'Connection':'keep-alive',
        'Proxy-Connection':'keep-alive',
        'Cookie':'$Version=1; Skin=new;',
        'Date':'Dec, 26 Dec 2017 17:30:00 GMT',
        'Host':'1.1.1.1:80',
        'Content-Type':'application',
        'Content-Length':'999',
        }
        headers2 = {'User-Agent':'afl_fuzz_exit', 
        'Accept':'text/plain', 
        'Accept-Language':'en-US', 
        'Authorization':'Basic OSdjJGRpbjpvcGVuIANlc2SdDE==',
        'Proxy-Authorization':'Basic IOoDZRgDOi0vcGVuIHNlNidJi2==',
        'Connection':'keep-alive',
        'Proxy-Connection':'keep-alive',
        'Cookie':'$Version=1; Skin=new;',
        'Date':'Dec, 26 Dec 2017 17:30:00 GMT',
        'Host':'1.1.1.1:80',
        'Content-Type':'application',
        'Content-Length':'999',
        }

        self.timer = Timer(3.0, self.sendExitSigbyTimer)
        while True:
            print 'Waitting for connecting...'
            sk = socket.socket()
            #
            sk.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            sk.bind((self.host, self.port))
            sk.settimeout(5000)
            sk.listen(128)
            flag = False
            if flag:
                self.timer.start()
                conn, address = sk.accept()
                self.timer.cancel()
            else:
                conn, address = sk.accept()

            print "Client ip:%s port:%d "%(address[0],address[1])
            recvHello = conn.recv(512)

            if recvHello == 'hello afl!':
                flag = True
                conn.sendall('hello afl!')
                print 'Handshaking success!'

                while True:
                    #timer = Timer(3.0, self.sendExitSig, args=httpConn)
                    self.timer.start()
                    recvData = conn.recv(2048)
                    self.timer.cancel()
                    print "Recv testcase:%s"%recvData
                    self.header2bFuzz = 'User-Agent'
                    
                    if fuzzType == 'header':
                        s = re.compile(r'\n(?![ \t])|\r(?![ \t\n])')
                        recvData = s.sub('/n', recvData)
                        recvData.replace('\r', '/r')
                        headers1[self.header2bFuzz] = recvData
                        #headers1['User-Agent'] = recvData
                        try:
                            httpConn.request(method='GET',url='/', body=None, headers=headers1)
                        except:
                            #exit-sig
                            print 'Failed to send testcase, maybe a malformed Http header.'
                            ##Error in httplib.py:924 
                            #httpConn.request(method='GET',url='/', body=None, headers=headers2)
                            #httpRep = httpConn.getresponse()
                            continue

                    elif fuzzType == 'body':
                        try:
                            httpConn.request(method='POST',url='/', body=recvData, headers=headers1)
                        except:
                            #exit-sig
                            print 'Failed to send testcase, maybe a malformed Http header.'
                            ##Error in httplib.py:924 
                            #httpConn.request(method='GET',url='/', body=None, headers=headers2)
                            #httpRep = httpConn.getresponse()
                            continue

                    try:
                        httpRep = httpConn.getresponse()
                    except:
                        print 'No rsp for testcase.'
                        time.sleep(1)
                    finally:
                        try:
                            httpConn.request(method='GET',url='/', body=None, headers=headers2)
                            httpRep = httpConn.getresponse()
                        except:
                            print 'Failed to send exit-sig, try again soon.'
                            time.sleep(5)
                            #try again
                            try:
                                httpConn.request(method='GET',url='/', body=None, headers=headers2)
                                httpRep = httpConn.getresponse()
                            except:
                                print 'Failed to send exit-sig again, maybe crash.'
                                sk.shutdown(2)
                                sk.close()
                                httpConn.close()
                                break
                            continue
                continue
            else:
                print 'No hello here'
            sk.shutdown(2)
            sk.close()
            httpConn.close()
        

    def sendExitSigbyTimer(self):
        #self.timer.cancel()
        headers2 = {'User-Agent':'afl_fuzz_exit', 
        'Accept':'text/plain', 
        'Accept-Language':'en-US', 
        'Authorization':'Basic OSdjJGRpbjpvcGVuIANlc2SdDE==',
        'Proxy-Authorization':'Basic IOoDZRgDOi0vcGVuIHNlNidJi2==',
        'Connection':'keep-alive',
        'Proxy-Connection':'keep-alive',
        'Cookie':'$Version=1; Skin=new;',
        'Date':'Dec, 26 Dec 2017 17:30:00 GMT',
        'Host':'1.1.1.1:80',
        'Content-Type':'application',
        'Content-Length':'999',
        }

        print 'Timeout, so timer will send a exit-sig req.'
        try:
            httpConn = httplib.HTTPConnection(host='127.0.0.1', port=8000, timeout=5)
            httpConn.request(method='GET',url='/', body=None, headers=headers2)
            httpRep = httpConn.getresponse()
            httpConn.close()
        except:
            print 'Timer failed to send exit-sig.'
        finally:
            self.timer.start()



if __name__ == '__main__':

    # for test
    a = afl_client('127.0.0.1', 8086)
    a.conn2Srv()
