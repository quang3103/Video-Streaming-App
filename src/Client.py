from tkinter import *
import tkinter.font as TkFont
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os, io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from ClientUI import *
from RtpPacket import RtpPacket
from time import time
from tkinter import filedialog
import requests

class Client:
	#state
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	#command
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	PLAYSKIP = 4
	FORWARD = 5
	NORMAL = 6
	NEXT = 7


	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.title("RTP Stream - Client")
		self.master.iconphoto(False,PhotoImage(file="hcmut.png"))
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.frameNbr = 0
		self.totalframe = 0
		self.loss_count = 0
		self.ping = 0
		self.remaining = 0
		#self.received_count = 0
		self.prevSkip = 0
		self.skipTime = int(time())
		self.prefix = ""
		self.isSlide = False
		self.isPlay = False
		self.isForward = False
		self.isEnd = False
		self.isBrowse = False  #no need
		self.isFull = False
		self.isSkip = False
		self.togglestats = False

		self.timePlot = [0, 0, 0, 0, 0]
		self.valuePlot = [0, 0, 0, 0, 0]
		self.pingPlot = [0, 0, 0, 0, 0]

		self.streamInfo = ""
		self.totalTime = [int(round(time() *1000))]
		self.substractTimeList = list()

		self.key = 'aio_XiUB37wuN11MQFiaR2ltrBsqa09L'
		self.createWidgets()
		self.addIfHaveFileName()
		self.auth_key = {'X-AIO-Key': self.key}
		self.requestAdafruit()

		# self.style = ttk.Style()


	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI
	def createWidgets(self):
		# """Build GUI."""
		# self.style.theme_use('clam')
		helvBIG = TkFont.Font(family='Comic Sans MS', size=20)
		helv16 = TkFont.Font(family='Comic Sans MS', size=12)
		helv10 = TkFont.Font(family='Comic Sans MS', size=10, weight=TkFont.BOLD)
		# Create Setup button
		self.setup = Button(self.master, font=helv16, width=6,
		                    padx=1, pady=1, relief=FLAT, activebackground='#ffd6ad', cursor="dot")
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup["state"] = ACTIVE
		self.setup.grid(row=3, column=0, padx=2, pady=2)

		# Create Play button
		self.start = Button(self.master,font=helv16, width=6, padx=1, pady=1, relief=FLAT, activebackground='#ffd6ad', cursor="dot")
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start["state"] = DISABLED
		self.start.grid(row=3, column=1, padx=2, pady=2)

		# Create Pause button
		self.pause = Button(self.master, font=helv16, width=6,
		                    padx=1, pady=1, relief=FLAT, activebackground='#ffd6ad', cursor="dot")
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause["state"] = DISABLED
		self.pause.grid(row=3, column=2, padx=2, pady=2)

		# Create Teardown button
		self.teardown = Button(self.master, font=helv16,
		                       width=8, padx=1, pady=1, relief=FLAT, activebackground='#ffd6ad', cursor="X_cursor")
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown["state"] = DISABLED
		self.teardown.grid(row=3, column=3, padx=2, pady=2)

		# Create Forward button
		self.forward = Button(self.master, font=helv16,
                        width=12, padx=1, pady=1, relief=FLAT, activebackground='#ffd6ad', cursor='boat')
		self.forward["text"] = "Fast Forward"
		self.forward["command"] = self.Forward
		self.forward["state"] = DISABLED
		self.forward.grid(row=3, column=4, padx=2, pady=2)

		# Create Next button
		self.next = Button(self.master, font=helvBIG,
                    activebackground='#ffd6ad', relief=FLAT, cursor="dot")
		self.next["text"] = ">>"
		self.next["command"] =  self.nextMovie
		self.next["state"] = DISABLED
		self.next.grid(row=3, column=5, sticky=W)

		# Create Describe
		self.describe = Button(self.master, font=helv10,
		    			 padx=1, pady=1, relief=FLAT, activebackground='#ffd6ad')
		self.describe["text"] = "Describe"
		self.describe["command"] =  self.describeCallBack
		self.describe["state"] = DISABLED
		self.describe.grid(row=0, column=5, padx=2, pady=2, sticky=E)
				# Create Describe
		self.stat = Button(self.master, font=helv10,
		    			 padx=1, pady=1, relief=FLAT, activebackground='#ffd6ad')
		self.stat["text"] = "Stats"
		self.stat["command"] =  self.toggleStats
		self.stat.grid(row=0, column=5, padx=2, pady=2, sticky=W)

		#Create slider
		self.slider = Scale(self.master, label="Current frame: 0/"+ str(self.totalframe), font=helv10, command=self.onSlideChange,
		                    orient=HORIZONTAL, length=400, width=10, bd=0, showvalue=0, state=DISABLED, relief=FLAT, sliderrelief=RAISED, troughcolor='#595959', activebackground='#f5b85d')
		self.slider.grid(row=2, column=0, columnspan=5, padx=2, sticky=W+E)

		#Create button SKIP
		self.skip = Button(self.master,  font=helv10, text="Skip",
		                	relief=FLAT, cursor='sb_h_double_arrow')
		self.skip["command"] = self.playSkip
		self.skip["state"] = DISABLED
		self.skip.grid(row=2, column=5, sticky=W+S)
		#Create button FULL
		self.full = Button(self.master,  font=helv10, text="< >",
                     relief=FLAT, cursor='sb_h_double_arrow')
		self.full["command"] = self.fullScreen
		#self.skip["state"] = DISABLED
		self.full.grid(row=2, column=5, sticky=E+S)

		#Create a label to MOVIE
		self.label = Label(self.master)
		self.label.grid(row=1, column=0, columnspan=5, sticky=W + N + S + E, padx=5, pady=5)

		#Create a label to display the loss rate
		self.label_loss = Label(self.master, font=helv16,
		                        text="Packet Lost: " + str(self.loss_count), fg="#ff0000",  relief=GROOVE)
		self.label_loss.grid(row=2, column=6)
		self.pingLabel = Label(self.master, font=helv16,
                         text="Average Latency(ms): " + str(self.loss_count), fg="#121aff")
		self.pingLabel.grid(row=3, column=6, sticky=W)
		self.timeEstLabel = Label(self.master, font=helv16,
                         text="Time remaining(estimated): " + str(self.remaining), fg="#121aff")
		self.timeEstLabel.grid(row=2, column=6, sticky=W)

		#Create button CHOOSE
		self.browse = Button(self.master,  font=helv10, text="Browse to playlist",
                     cursor="exchange", command=self.addToPlaylist)
		self.browse.grid(row=1, column=5, sticky=S)

		# Create a label to display PLAYLIST
		self.playlistframe = LabelFrame(self.master, font=helv10,
		                        text="Playlist", fg="#ff0000")
		self.playlistframe.grid(row=1, rowspan=3, column=5, sticky=N)
		self.playlist = Listbox(self.playlistframe,relief=FLAT, font=helv16, width=14, height=14, selectmode=SINGLE, cursor="draft_small", bg='#f0f0f0',fg='#4769ff',activestyle='dotbox')
		self.playlist.grid()

		self.fig = Figure(figsize=(
			7,4), facecolor='#f0f0f0')
		self.ax = self.fig.add_subplot(111)
		self.ax2 = self.ax.twinx()
        #self.a = self.f.add_subplot(1, 1, 1)
		#self.ax.plot(self.timePlot, self.valuePlot)
		self.canvas = FigureCanvasTkAgg(self.fig, self.master)
		self.canvas.get_tk_widget().grid(row=1, column=6, padx=5,pady=5, sticky=W)
		self.ax.clear()
		self.ax2.clear()
		self.ax.set_title('FPS/Average Latency of Stream')
		self.ax.set_xlabel('time')
		self.ax.set_ylabel('# of frame')
		self.ax2.set_ylabel('Average Latency')
		self.canvas.draw()


	# START CONFIG UI
	def toggleStats(self):
		if self.togglestats:
			self.master.geometry("")
			self.togglestats = False
		else:
			self.master.geometry("678x550")
			self.togglestats = True

	def fullScreen(self):
		self.isFull = not self.isFull
		if self.isEnd:
			photo = ImageTk.PhotoImage(Image.open("temp.png"))
			self.label.configure(image=photo)
			self.label.image = photo
			self.master.geometry("")


	def initFigure(self):
		self.ax.clear()
		self.ax2.clear()
		self.timePlot = [0, 0, 0, 0, 0]
		self.valuePlot = [0, 0, 0, 0, 0]
		self.pingPlot = [0, 0, 0, 0, 0]
		self.ax.set_title('FPS/Average Latency of Stream')
		self.ax.set_xlabel('time')
		self.ax.set_ylabel('# of frame')
		self.ax2.set_ylabel('Average Latency')
		self.canvas.draw()

	def addToPlaylist(self):
		#file = self.fileDialog()
		#
		self.playlist.delete(0, END)
		url = 'https://io.adafruit.com/api/v2/thanhdanh27600/feeds/cn/data?limit=1'
		get_data = requests.get(url, headers=self.auth_key)
		response = get_data.text.split('"')
		name_list = response[response.index('value') + 2]
		#print(name_list)
		for i in name_list.split('_'):
			self.playlist.insert(END, i)
		self.playlist.delete(END)

	def fileDialog(self):
		filechoose = filedialog.askopenfilename(
        	initialdir="./", title="Select A File", filetype=(("Accepted Media Files", "*.mjpeg"), ("All files", "*.*")))
		self.isBrowse = True
		self.prefix = ""
		for i in filechoose.split('/')[:-1]:
			self.prefix+=i+'/'
		return filechoose

	def addIfHaveFileName(self):
		if self.fileName != "None":
			self.playlist.insert(END, self.fileName)


	def onSlideChange(self, newvalue):
		"""Slider handler."""
		# if int(newvalue) <= int(self.frameNbr):
		# 	self.isSlide = True
		# else:
		if abs(int(newvalue) - self.frameNbr) > 10 and newvalue!=0:
			self.isSlide = True
		else:
			self.isSlide = False

	def requestAdafruit(self):

		print(requests.get(
			'https://io.adafruit.com/api/v2/thanhdanh27600/feeds?x-aio-key='+self.key).text[:30],'...CONNECTED')
		#
		# #delay 1 second before play.
		# self.playMovie()



	# END CONFIG UI

	def setupMovie(self):
		"""Setup button handler."""
		if len(self.playlist.curselection()) == 0:
			tkinter.messagebox.showerror("Alert", "Please choose file to play")
		self.fileName = self.playlist.get(self.playlist.curselection())

		#self.received_count = 0
		self.loss_count = 0

		self.label_loss["text"] = "Packet Lost: " + str(0)
		self.slider['label'] = "Current frame: " + str(0) + "/" + str(self.totalframe)

		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)

	def exitClient(self):
		"""Teardown button handler."""
	#TODO
		self.sendRtspRequest(self.TEARDOWN)
		# Delete the cache image from video
		try:
			files_in_directory = os.listdir("./cache")
			filtered_files = [file for file in files_in_directory if file.endswith(".jpg")]
			for file in filtered_files:
				path_to_file = os.path.join("./cache/", file)
				os.remove(path_to_file)
		except:
			return

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	#TODO

	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			# Create a new thread to listen for RTP packets
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)


	def playSkip(self):
		"""Slider handler."""
		#print("State: ", self.state, "skip: ", newvalue)
		if self.state == self.PLAYING:
			self.isSlide = False
			self.isSkip = True
			self.sendRtspRequest(self.PLAYSKIP, int(self.slider.get()))

	def Forward(self):
		"""Forward handler."""
		if self.state == self.PLAYING:
			if self.isForward:
				self.isForward = False
				self.forward['text'] = "Fast Forward"
				self.sendRtspRequest(self.NORMAL)
			else:
				self.isForward = True
				self.forward['text'] = "Normal Speed"
				self.sendRtspRequest(self.FORWARD)

	def nextMovie(self):
		if self.state == self.PLAYING or self.state == self.READY:
			self.exitClient()
			self.playlist["state"] = NORMAL
			cur = self.playlist.curselection()[0]
			length = self.playlist.size()
			next = (cur + 1) % length
			self.playlist.selection_clear(cur)
			self.playlist.selection_set(next)
			self.fileName = self.playlist.get(self.playlist.curselection())
			tkinter.messagebox.showinfo("Next movie", "Next movie: " + self.playlist.get(self.playlist.curselection()) + " will be automatically setup.")
			self.setupMovie()
			# tkinter.messagebox.showinfo("Next song", "Next song: " + self.playlist.get(
			# 	self.playlist.curselection()) + " will be automatically Setup and Play")
			self.playlist["state"] = DISABLED

			#self.received_count = 0
			self.loss_count = 0

			self.label_loss["text"] = "Packet Lost: 0"
			self.slider['label'] = "Current frame: 0/" + str(self.totalframe)

			# self.playMovie()


	def describeCallBack(self):
		self.pauseMovie()
		str_temp = "Sesson ID: " + str(self.sessionId) + '\n\n'
		for i in self.streamInfo:
			str_temp += str(i + '\n\n')
		tkinter.messagebox.showinfo("Describe", str_temp)
		if self.isPlay:
			self.playMovie()
	#TODO

	def listenRtp(self):
		"""Listen for RTP packets."""
		#TODO
		previous_time = int(time())
		current_time = previous_time
		frame_count = 0
		packetLost = 0

		while True:
			try:
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					currFrameNbr = rtpPacket.seqNum()
					#print("Current Seq Num: " + str(currFrameNbr))
					frame_count += 1
					packetLost = currFrameNbr - self.frameNbr
					self.frameNbr = currFrameNbr
					self.slider['label'] = "Current frame: " + str(currFrameNbr) + "/" + str(self.totalframe)
					#print('# Playing Frame Number: {} #'.format(rtpPacket.seqNum()))
					#self.received_count = self.received_count + 1
					self.updateMovie(self.writeFrame(rtpPacket.getPayload()))

					self.totalTime.append(int(round(time() * 1000)))

					if (len(self.totalTime) >= 2):
						self.substractTimeList.append(self.totalTime[-1] - self.totalTime[-2])

					# Update statistic
					if abs(packetLost) > 1:
						#print("\n============ LOST ============\n")
						self.loss_count += packetLost
						self.label_loss["text"] = "Packet Lost: " + str(self.loss_count)
					current_time = int(time())
					if current_time - previous_time >= 1:
						# print('Average Latency per Frame: {} millisecond'.format(
						# 	sum(self.substractTimeList) / (self.frameNbr - 1)))
						if not(self.isSlide):
							self.slider.set(currFrameNbr)
						previous_time = current_time
						self.timePlot.remove(self.timePlot[0])
						self.timePlot.append(int(self.timePlot[-1]+1))
						self.valuePlot.remove(self.valuePlot[0])
						self.valuePlot.append(frame_count)

						if len(self.substractTimeList) > frame_count:
							pass
						self.pingPlot.remove(self.pingPlot[0])
						self.pingPlot.append(round(sum(self.substractTimeList[-frame_count:]) / frame_count, 1))
						self.pingLabel['text'] = "Average Latency(ms): " + str(self.pingPlot[-1])
						self.remaining = (self.totalframe - self.frameNbr)/frame_count
						self.timeEstLabel['text'] = "Time remaining(estimated): " + str(
							round(self.remaining, 1)) + 's'
						self.ax2.plot(self.timePlot, self.pingPlot, c='red', ls='dashed', marker='o', markersize=2.5, lw=.5)
						self.ax.plot(self.timePlot, self.valuePlot, c='green', ls='dashed', marker='o', markersize=2.5, lw=.5)
						frame_count = 0
						self.canvas.draw()
				if self.frameNbr == self.totalframe:
					self.slider.set(0)
					self.slider['label'] = "Current frame: " + str(self.totalframe) + "/" + str(self.totalframe)
					self.timeEstLabel['text'] = "Time remaining(estimated): 0"
					self.isEnd = True
					if self.isFull:
						self.master.geometry("")
						photo = ImageTk.PhotoImage(Image.open("temp.png"))
						self.label.configure(image=photo)
						self.label.image = photo
					self.exitClient()
					break
			except (IOError):
				if (self.state == self.PLAYING):
					if (self.frameNbr == self.totalframe - 1):
						self.slider['label'] = "Current frame: " + \
							str(self.totalframe) + "/" + str(self.totalframe)
						self.isEnd = True
						self.exitClient()
						break
					else:
						print('--- Request Timeout ---')
				# Stop listening upon requesting PAUSE or TEARDOWN
				if self.playEvent.isSet():
					break
				# Upon receiving ACK for TEARDOWN request,
				# close the RTP socket
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					self.teardownAcked == 0
					break

	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
	#TODO
		cachename = "./cache/" + str(self.sessionId) + ".jpg"
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		return cachename

	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
	#TODO
		image = Image.open(imageFile)
		if self.isFull:
			self.master.geometry(str(int(self.master.winfo_screenwidth()/1.5) + 165) + "x" +
                            str(int(self.master.winfo_screenheight()/1.5) + 100))
			image = image.resize((int(self.master.winfo_screenwidth()/1.5), int(self.master.winfo_screenheight()/1.5)))
			photo = ImageTk.PhotoImage(image)
			self.label.configure(image=photo)
		else:
			if not self.togglestats:
				self.master.geometry("")
			image = image.resize((int(self.master.winfo_screenwidth()/3), int(
				image.height*((self.master.winfo_screenwidth()/3)/image.width))))
			photo = ImageTk.PhotoImage(image)
			self.label.configure(image=photo)
		self.label.image = photo

	def clearMovie(self):
		self.label.image = None



	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		try:
			self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			#print("New RTSP created:", self.rtspSocket)
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning(
				'Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)
	#TODO

	def sendRtspRequest(self, requestCode, value=-1):
		"""Send RTSP request to the server."""
		#-------------
		# TO COMPLETE
		#-------------
		# Setup request
		request = "None"
		if requestCode == self.SETUP and (self.state == self.INIT or self.state == self.TEARDOWN):
			self.connectToServer()
			threading.Thread(target=self.recvRtspReply).start()
			# Update RTSP sequence number.
			self.rtspSeq += 1
			# Write the RTSP request to be sent.
			request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
				str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

			# Keep track of the sent request.
			self.requestSent = self.SETUP

		# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
			self.rtspSeq += 1
			request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
				str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.PLAY

			# Play skip
		elif requestCode == self.PLAYSKIP and self.state == self.PLAYING:
			self.rtspSeq += 1
			request = 'PLAYSKIP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
				str(self.rtspSeq) + '\nSession: ' + str(self.sessionId) + '\n' + str(value)
			self.requestSent = self.PLAYSKIP
			# Play forward
		elif requestCode == self.FORWARD and self.state == self.PLAYING:
			self.rtspSeq += 1
			request = 'FORWARD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
				str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.FORWARD
			# Play normal
		elif requestCode == self.NORMAL and self.state == self.PLAYING:
			self.rtspSeq += 1
			request = 'NORMAL ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
				str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.NORMAL

		# Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			self.rtspSeq += 1
			request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
				str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.PAUSE

		# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			self.rtspSeq += 1
			request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
				str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			self.requestSent = self.TEARDOWN

		# Next song request
		# elif requestCode == self.NEXT and not self.state == self.INIT:
		# 	self.rtspSeq += 1
		# 	request = 'NEXT ' + self.fileName + ' RTSP/1.0\nCSeq: ' + \
		# 		str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)
		# 	self.requestSent = self.NEXT
		else:
			return
	# Send the RTSP request using rtspSocket.
		self.rtspSocket.send(request.encode())

		print('\nData sent:\n' + request)

	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
		while True:
			reply = self.rtspSocket.recv(1024)

			if reply:
				self.parseRtspReply(reply)

			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break

	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
		data = data.decode("utf-8")
		#print("DATA BACK: ", data)
		lines = data.split('\n')

		# 404
		if lines[0].split(' ')[1] == '404':
			print("FILE NOT FOUND")
			return
		if lines[0].split(' ')[1] == '500':
			print('CONNECTION ERROR')
			return

		seqNum = int(lines[1].split(' ')[1])

		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session

			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200:
					if self.requestSent == self.SETUP:
						# Update RTSP state.
						self.master.title("RTP Stream - Client - "+self.fileName)
						self.state = self.READY
						self.totalframe = int(lines[3].split(':')[1])
						self.streamInfo = lines[4:]
						self.slider['to'] = self.totalframe
						# UI Handle
						self.next["state"] = ACTIVE
						self.start["state"] = ACTIVE
						self.setup["state"] = DISABLED
						self.teardown["state"] = ACTIVE
						self.browse["state"] = DISABLED
						self.playlist["state"] = DISABLED
						self.describe["state"] = ACTIVE
						self.isSlide = False
						self.initFigure()
						# Open RTP port.
						self.openRtpPort()
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
						self.isPlay = True
						# UI Handle
						self.next["state"] = ACTIVE
						self.start["state"] = DISABLED
						self.pause["state"] = ACTIVE
						self.slider["state"] = ACTIVE
						self.skip["state"] = ACTIVE
						self.forward["state"] = ACTIVE
					elif self.requestSent == self.PLAYSKIP:
						self.frameNbr = int(self.slider.get())
						self.isSkip = False
						#print("U SKIP, BRO!")
					elif self.requestSent == self.FORWARD:
						self.pause["state"] = DISABLED
						#print("U Forward, BRO!")
					elif self.requestSent == self.NORMAL:
						self.pause["state"] = ACTIVE
						#print("U Normal, BRO!")
					elif self.requestSent == self.PAUSE:
						# UI Handle
						self.start["state"] = ACTIVE
						self.pause["state"] = DISABLED
						self.slider["state"] = DISABLED
						self.skip["state"] = DISABLED
						self.forward["state"] = DISABLED
						self.state = self.READY
						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
					# elif self.requestSent == self.NEXT:
					# 	self.state = self.INIT
					# 	self.isBrowse = False
					# 	self.isPlay = False

					# 	self.setup["state"] = ACTIVE
					# 	self.start["state"] = DISABLED
					# 	self.pause["state"] = DISABLED
					# 	self.teardown["state"] = DISABLED
					# 	self.skip["state"] = DISABLED
					# 	self.slider["state"] = ACTIVE
					# 	self.frameNbr = 0
					# 	self.slider.set(0)
					# 	self.slider["state"] = DISABLED
					# 	self.describe["state"] = DISABLED
					# 	if self.isForward:
					# 		self.isForward = False
					# 		self.forward['text'] = "Fast Forward"
					# 	self.forward["state"] = DISABLED
					# 	self.playlist["state"] = NORMAL
					# 	self.browse["state"] = ACTIVE
					# 	self.next["state"] = DISABLED
					# 	self.sessionId = 0
					# 	self.requestSent = -1
					# 	self.initFigure()
					# 	self.teardownAcked = 1

					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						self.isBrowse = False
						self.isPlay = False
						# UI Handle
						self.setup["state"] = ACTIVE
						self.start["state"] = DISABLED
						self.pause["state"] = DISABLED
						self.teardown["state"] = DISABLED
						self.skip["state"] = DISABLED
						self.slider["state"] = ACTIVE
						self.frameNbr = 0
						self.slider.set(0)
						self.slider["state"] = DISABLED
						self.describe["state"] = DISABLED
						if self.isForward:
							self.isForward = False
							self.forward['text'] = "Fast Forward"
						self.forward["state"] = DISABLED
						self.playlist["state"] = NORMAL
						self.browse["state"] = ACTIVE
						self.next["state"] = DISABLED
						self.sessionId = 0
						self.requestSent = -1
						#self.clearMovie()
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1

	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...

		# Set the timeout value of the socket to 0.5sec
		# ...
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)

		try:
			# Bind the socket to the address using the RTP port given by the client user
				ackMessage = 'OPEN RTP PORT SUCCESSFULLY'
				self.rtpSocket.sendto(ackMessage.encode(), (self.serverAddr, self.rtpPort))
				while True:
					try:
						message = self.rtpSocket.recv(20480)
						if message:
							print(message.decode())
							break
					except:
						continue
			#elf.rtpSocket.connect((self.serverAddr, self.rtpPort))
		except:
			tkinter.messagebox.showwarning(
				'Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)


	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
			#print("state:" ,self.state)
			#if self.state != self.READY:
			try:
				self.exitClient()
			except:
				pass
			self.master.destroy()  # Close the gui window
			os._exit(1)

		else:  # When the user presses cancel, resume playing.
			if self.isPlay:
				self.playMovie()
