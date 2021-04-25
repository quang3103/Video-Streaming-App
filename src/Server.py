import sys, os, socket, requests

from ServerWorker import ServerWorker

class Server:

	def main(self):
		try:
			SERVER_PORT = int(sys.argv[1])
		except:
			print("[Usage: Server.py Server_port]\n")

		try:
			key = 'aio_XiUB37wuN11MQFiaR2ltrBsqa09L'
			UPDATE_FLAG = sys.argv[2]
			if UPDATE_FLAG == '-u':
				print("Server is updating the library..")
				files_in_directory = os.listdir("./")
				filtered_files = ""
				for file in files_in_directory:
					if file.endswith(".mjpeg"):
						filtered_files += str(file) + '_'
				print(filtered_files)
				if requests.get(
					'https://io.adafruit.com/api/v2/thanhdanh27600/feeds?x-aio-key='+key).text.find('username') == -1:
					print("Cannot connect to Adafruit")
				else:
					url = 'https://io.adafruit.com/api/v2/thanhdanh27600/feeds/cn/data'
					myobj = {'value': filtered_files}
					auth_key = {'X-AIO-Key': key}
					post_data = requests.post(url, json=myobj, headers=auth_key)
					if (post_data.text.find('value') == -1):
						print("Cannot update the value to Adafruit")
					else:
						print(post_data.text)
		except:
			print("Not update playlist!")

		rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		rtspSocket.bind((socket.gethostbyname(socket.gethostname()), SERVER_PORT))
		rtspSocket.listen(5)
		print(f"Server is listening ok {socket.gethostbyname(socket.gethostname())}:{SERVER_PORT}")
		# Receive cpython Server.py 1027lient info (address,port) through RTSP/TCP session
		while True:
			clientInfo = {}
			clientInfo['rtspSocket'] = rtspSocket.accept()
			clientInfo['serverPort'] = SERVER_PORT
			print("Accept new client: ", clientInfo)
			ServerWorker(clientInfo).run()

if __name__ == "__main__":
	(Server()).main()
