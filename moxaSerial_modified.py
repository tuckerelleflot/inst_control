import time
import socket

MOXA_DEFAULT_TIMEOUT = 1.0

class Serial_TCPServer(object):

	def __init__(self,port,timeout=MOXA_DEFAULT_TIMEOUT):
		# port is a tuple of form (IP addr, TCP port)
		self.port = port

	def connect(self):
		self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.sock.setblocking(0)
		self.settimeout(1.0)
		self.sock.connect(self.port)

	# Reads exactly n bytes, waiting up to timeout.
	def readexactly(self,n):
		t0 = time.time()
		msg = ""
		timeout = self.gettimeout()
		while len(msg) < n:
			newtimeout = timeout-(time.time()-t0)
			if newtimeout <= 0.0: break
			self.settimeout(newtimeout)
			try:
				msg = self.sock.recv(n,socket.MSG_PEEK)
			except:
				pass
		# Flush the message out if you got everything
		if len(msg) == n: msg = self.sock.recv(n)
		# Otherwise tell nothing and leave the data in the buffer
		else: msg = ''
		self.settimeout(timeout)
		return msg


	# Reads whatever is in the buffer right now, but is O(N) in buffer size.
	def readbuf_slow(self,n):
		msg = ''
		self.sock.setblocking(0)
		try:
			for i in range(n):
				msg += self.sock.recv(1)
		except: pass
		self.sock.setblocking(1)	# belt and suspenders
		self.settimeout(self.__timeout)
		return msg

	# Log recode of readbuf.  Usable for large buffers.
	def readbuf(self,n):
		if n == 0: return ''
		try:
			msg = self.sock.recv(n)
		except: msg = ''
		n2 = min(n-len(msg),n/2)
		return msg + self.readbuf(n2)


	# Will probably read whatever arrives in the buffer, up to n or the timeout
	# Use read for certainty
	def readpacket(self,n):
		try:
			msg = self.sock.recv(n)
		except:
			msg = ''
		return msg

	# Will read whatever arrives in the buffer, up to n or the timeout
	def read(self,n):
		msg = self.readexactly(n)
		n2 = n-len(msg)
		if n2 > 0: msg += self.readbuf(n2)
		return msg

	def readline(self,term='\n'):
		msg = ''
		while True:
			c = self.readexactly(1)
			if c == term or c == '':
				return msg
			msg += c

	def readall(self):
		msg = ""
		while 1:
			c = self.readexactly(1)
			if c == '\r': return msg
			if c == '': return False
			msg += c
		return msg

	def write(self,str):
		self.sock.send(str + '\r\n')

	def writeread(self,str):
		self.flushInput()
		self.write(str)
		return self.readall()

	# Erases the input buffer at this moment
	def flushInput(self):
		self.sock.setblocking(0)
		try:
			while len(self.sock.recv(1))>0: pass
		except: pass
		self.sock.setblocking(1)
		self.sock.settimeout(self.__timeout)

	# Sets the socket in timeout mode
	def settimeout(self,timeout):
		assert timeout > 0.0
		self.__timeout = timeout
		self.sock.settimeout(timeout)
	# We don't query the socket's timeout or check that they're still correct
	# Since self.sock e is public this could be the wrong timeout!
	def gettimeout(self):
		return self.__timeout

	timeout = property(gettimeout,settimeout)
	
	def close(self):
	    self.sock.close()
	
	def shutdown(self):
	    self.sock.shutdown()
	    
	def query(self, msg):
	    self.write(msg)
	    time.sleep(.1)
	    return self.readline()

def test1():
	x = Serial_TCPServer(('google.com',80),timeout=1.15)
	x.write('GET /\n')
	print x.readexactly(1000)

def test2():
	x = Serial_TCPServer(('google.com',80),timeout=0.15)
	x.write('GET /\n')
	print x.read(10000)
