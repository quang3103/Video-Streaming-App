from random import randint
import sys, os, traceback, threading, socket, KThread

from VideoStream import VideoStream
from RtpPacket import RtpPacket

class ServerWorker:
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'
	PLAYSKIP = 'PLAYSKIP'
	FORWARD = 'FORWARD'
	NORMAL = 'NORMAL'
	DESCRIBE = 'DESCRIBE'
	NEXT = 'NEXT'

	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2

	clientInfo = {}
	skipto = -1

	def __init__(self, clientInfo):
		self.clientInfo = clientInfo
		self.streamInfo = '\n'.join([
			'Server IP Address: {}'.format(self.clientInfo['rtspSocket'][1][0]),
			'Port listenning for requests: {}'.format(str(self.clientInfo['serverPort'])),
			'Streaming: video',
			'Protocol: RTSP/1.0 - (Real Time Streaming Protocol)',
			'          RTP - (Real-time Transport Protocol)',
			'RTP Payload format: RFC 2435 - (RTP Payload Format for JPEG-compressed Video)',
			'Encoding Format: UTF-8',
		])
		#print(streamInfo)

	def run(self):
		threading.Thread(target=self.recvRtspRequest).start()

	def recvRtspRequest(self):
		"""Receive RTSP request from the client."""
		connSocket = self.clientInfo['rtspSocket'][0]
		while True:
			data = connSocket.recv(512)
			if data:
				print("Data received:\n" + data.decode("utf-8"))
				self.processRtspRequest(data.decode("utf-8"))

	def processRtspRequest(self, data):
		"""Process RTSP request sent from the client."""
		# Get the request type
		request = data.split('\n')
		line1 = request[0].split(' ')
		requestType = line1[0]


		# Get the RTSP sequence number
		seq = request[1].split(' ')

		# Process SETUP request
		if requestType == self.SETUP:
			if self.state == self.INIT:
				# Update state
				print("processing SETUP\n")

				try:
					# Get the media file name
					filename = ""
					for sub_dir in line1[1:-1]:
						filename += sub_dir+' '
					print("Setup filename=", filename)
					self.clientInfo['videoStream'] = VideoStream(filename)
					#self.clientInfo['videoStream'].
					self.state = self.READY

					# Generate a randomized RTSP session ID
					self.clientInfo['session'] = randint(100000, 999999)
					self.clientInfo['rtpPort'] = request[2].split(' ')[3]
					# Create a new socket for RTP/UDP
					self.clientInfo['rtpSocket'] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
					self.clientInfo['rtpSocket'].bind(('', int(self.clientInfo['rtpPort'])))
					# Send RTSP reply
					self.firstReplyRtsp(self.OK_200, seq[1])
					while True:
						try:
							message, clientAddr = self.clientInfo['rtpSocket'].recvfrom(20400)
							if message:
								print('MESSAGE:',message.decode())
								print('CLIENT:', clientAddr)
								self.clientInfo['clientAdress'] = clientAddr
								self.clientInfo['rtpSocket'].sendto('RTP PORT OKE'.encode(), self.clientInfo['clientAdress'])
								break
						except:
							continue
				except IOError:
					self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])

		# Process PLAY request
		elif requestType == self.PLAY:
			if self.state == self.READY:
				print("processing PLAY\n")
				self.state = self.PLAYING
				self.clientInfo['event'] = threading.Event()
				self.replyRtsp(self.OK_200, seq[1])

				self.clientInfo['worker'] = KThread.KThread(target=self.sendRtp)
				self.clientInfo['worker'].start()

		# Process PLAYSKIP request
		elif requestType == self.PLAYSKIP:
			if self.state == self.PLAYING:
				print("processing PLAYSKIP\n")
				self.replyRtsp(self.OK_200, seq[1])
				self.skipto = int(request[3])
				print("SERVER: set to ", self.skipto)

		# Process PLAYSKIP request
		elif requestType == self.FORWARD:
			if self.state == self.PLAYING:
				print("processing FORWARD\n")
				self.replyRtsp(self.OK_200, seq[1])
				self.clientInfo['worker'] =KThread.KThread(target=self.sendRtp)
				self.clientInfo['worker'].start()
				print("SERVER: Speed x2")

		# Process NORMAL request
		elif requestType == self.NORMAL:
			if self.state == self.PLAYING:
				print("processing NORMAL\n")
				self.replyRtsp(self.OK_200, seq[1])
				self.clientInfo['worker'].kill()
				print("SERVER: Normal Speed")

		# Process PAUSE request
		elif requestType == self.PAUSE:
			if self.state == self.PLAYING:
				print("processing PAUSE\n")
				self.state = self.READY

				self.clientInfo['event'].set()

				self.replyRtsp(self.OK_200, seq[1])

		# Process TEARDOWN request
		elif requestType == self.TEARDOWN:
			print("processing TEARDOWN\n")

			self.clientInfo['event'].set()

			self.replyRtsp(self.OK_200, seq[1])

			self.clientInfo['videoStream'].close()

			self.clientInfo['worker'].kill()
			# Close the RTP socket
			self.clientInfo['rtpSocket'].close()


	def sendRtp(self, skipto=-1):
		"""Send RTP packets over UDP."""
		while True:
			self.clientInfo['event'].wait(0.05)

			# Stop sending if request is PAUSE or TEARDOWN
			if self.clientInfo['event'].isSet():
				break


			if self.skipto == -1:
				data = self.clientInfo['videoStream'].nextFrame()
				if data:
					frameNumber = self.clientInfo['videoStream'].frameNbr()
					#print('# Send frame number: {} #'.format(frameNumber))
					try:
						address = self.clientInfo['clientAdress']
						#print('client address:', self.clientInfo['clientAdress'])
						port = int(self.clientInfo['rtpPort'])
						if frameNumber % 50 != 1:
							self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber), self.clientInfo['clientAdress'])
					except:
						print("Connection Error")
			else:
				data = self.clientInfo['videoStream'].getFrame(self.skipto)
				if data:
					frameNumber = self.clientInfo['videoStream'].frameNbr()
					try:
						address = self.clientInfo['rtspSocket'][1][0]
						port = int(self.clientInfo['rtpPort'])
						if frameNumber % 50 != 1:
							self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber), self.clientInfo['clientAdress'])
					except:
						print("Connection Error")
				self.skipto = -1

	def makeRtp(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0

		rtpPacket = RtpPacket()

		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)

		return rtpPacket.getPacket()

	def replyRtsp(self, code, seq):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			#print("200 OK")
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			#print("404 NOT FOUND")
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send("RTSP/1.0 404 NOT FOUND".encode())
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")

	def firstReplyRtsp(self, code, seq):
		if code == self.OK_200:
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) #normal RSTP reply
			reply = reply + '\nTotal frame: {}\n'.format(str(self.clientInfo['videoStream'].totalFrames)) #total Frame
			reply = reply + self.streamInfo # the stream info
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			#print("404 NOT FOUND")
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send("RTSP/1.0 404 NOT FOUND".encode())
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")

	def sendString(self, string):
		connSocket = self.clientInfo['rtspSocket'][0]
		print(string)
		connSocket.send(string.encode())
