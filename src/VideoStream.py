import io
class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			#self.totalFrame = self.count_frame()
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		self.file_temp = None
		self.totalFrames = self.countFrame()
	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5)  # Get the framelength from the first 5 bits
		if data:
			#print("Frame length bytes: ", data)
			framelength = int.from_bytes(data, 'big')
			#framelength = int.from_bytes(data, 'big')
			#print("Frame length base 10: ", framelength)
			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		return data

	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum

	def getFrame(self, pos):
		"""Get frame at pos"""
		self.close()
		self.frameNum = 0
		self.file_temp = open(self.filename, 'rb')
		data = None
		for i in range(pos):
			data = self.file_temp.read(5)  # Get the framelength from the first 5 bits
			if data:
				framelength_temp = int.from_bytes(data, 'big')
				# Read the current frame
				data = self.file_temp.read(framelength_temp)
				self.frameNum += 1
		self.file = self.file_temp
		return data

	def countFrame(self):
		count = 0
		with open(self.filename, 'rb') as f:
			while True:
				data = f.read(5)
				if data:
					frame_size = int.from_bytes(data, 'big')
					f.seek(frame_size, io.SEEK_CUR)
					count += 1
				else:
					break
			f.seek(0)
		return count

	def close(self):
		self.file.close()
