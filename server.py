import socket,os
import threading,struct,json
import progressbar,subprocess

class FtpServer(object):
	
	def __init__(self, ip='127.0.0.1',port=2121):	#初始化实例属性
		self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #定义服务端tcp socket
		self.addr = (ip, port)	#服务端地址
		self.s_dir = os.getcwd()+'/server/'	#服务端初始目录
		self.buf = 1024		#缓冲大小
		self.now_dir = {}		#存放各个线程客户端对应的所在目录位置信息

	def listdir(self,c_sock):	#列出当前目录文件夹内文件信息
		res = subprocess.check_output(['ls','-l',self.now_dir[c_sock]])	#执行系统ls -l命令
		c_sock.send(res)  #客户端socket send 结果

	def change_dir(self,c_sock,target_dir=''):	#改变目录函数
		if target_dir=='..':	#返回上级
			self.now_dir[c_sock]='/'.join(self.now_dir[c_sock].split('/')[:-2])+'/'
		elif target_dir not in os.listdir(self.now_dir[c_sock]):	#不存在目标文件夹
			# send 到客户端错误信息
			c_sock.send(('当前目录无 %s 文件夹!'% target_dir).encode('utf-8'))
			return
		elif os.path.isfile('%s%s'%(self.now_dir[c_sock],target_dir)):	#目标文件夹是一个文件
			# send 到客户端错误信息
			c_sock.send((' %s 不是一个文件夹!'% target_dir).encode('utf-8'))
			return
		else:	#找到文件夹
			self.now_dir[c_sock]+=target_dir+'/'	#更改客户端socket对应的当前目录
		# send到客户端成功信息
		c_sock.send(('切换目录成功,当前位于%s'% self.now_dir[c_sock]).encode('utf-8'))

	def send_file(self,c_sock,filename):	#发送文件函数
		dir_files=os.listdir(self.now_dir[c_sock])	#列出当前目录内文件信息
		# header_dic={
		# 	'filename':filename,
		# 	'file_size':os.path.getsize('{}/{}'.format(self.s_dir,filename))
		# }
		# header_bytes=json.dumps(header_dic).encode('utf-8')
		if filename not in dir_files:
			c_sock.send(b'0') #不存在 send 0
			return
		elif os.path.isdir(self.now_dir[c_sock]+filename):
			c_sock.send(b'2') #目标为文件夹 send 2
			return
		c_sock.send(b'1')	#存在则 send 1

		# filename=dir_files[0]
		filepath=self.now_dir[c_sock]+filename
		# 打包文件头信息，包含文件名和文件大小
		fhead = struct.pack('128sl',filename.encode('utf-8'),os.stat(filepath).st_size)
		c_sock.send(fhead)	# send 文件头信息到客户端
		with open(self.now_dir[c_sock]+filename,'rb') as f:
			for data in f:
				c_sock.send(data)	# send 文件字节流数据

	def save_sile(self,c_sock):	#保存文件函数
		fileinfo_size = struct.calcsize('128sl')	#约定的128字节文件头信息
		#接收文件头信息，解包得到文件名 文件大小
		filename,filesize=struct.unpack('128sl',c_sock.recv(fileinfo_size))
		filename=filename.decode('utf-8')

		bar = progressbar.ProgressBar(widgets=[
			'[',progressbar.Bar(),']',
    		progressbar.Percentage(),
    		' (', progressbar.ETA(), ') ',])	#文件进度
		with open('{}{}'.format(self.now_dir[c_sock],filename.strip('\0')),'wb') as f:
			print('正在接收: "%s"  大小:[ %s ]Bytes'% (filename,filesize))
			bar.start()
			recv_size=0		#定义已接收字节大小
			while recv_size<filesize:	#循环接收
				filedata=c_sock.recv(self.buf)	# recv 文件字节数据
				f.write(filedata)	#写入字节数据到文件
				recv_size+=len(filedata)
				bar.update(recv_size/filesize*100)
			bar.finish()
			print('%s 接收完毕'%filename)

	def recv(self,c_sock,ip,port):	#主监听函数
		print('new connection from {}:{}! sockfd值{}'.format(ip,port,c_sock))
		self.now_dir[c_sock]=self.s_dir #定义当前客户端对应的 当前文件夹
		c_sock.send(
			'欢迎来到 Py-Ftp!\n基本用法:\n  ls  --查看服务器目录下文件及文件夹信息\n\
  cd  文件夹名   --切换服务器目录\n  cd  ..        --切换到上一级目录\n\
  get 文件名     --从服务器获取文件\n  put 文件名     --上传文件到服务器\n\
  quit 或 exit   --退出并断开ftp连接'
		.encode('utf-8'))	# send 服务端介绍信息
		while True: 	#循环处理客户端发送的信息
			cmds=c_sock.recv(self.buf).decode('utf-8')	#接收的输入信息
			print('{}:{} send command: {}'.format(ip,port,cmds))
			if cmds=='quit':	#退出
				break
			cmd1=cmds.split()[0]	#命令
			if len(cmds.split())>1:
				cmd2=cmds.split()[1]	#参数
			if cmds=='ls':
				self.listdir(c_sock)	#列出文件夹内信息
			elif cmd1=='cd':	
				self.change_dir(c_sock,cmd2)	#改变当前目录位置
			elif cmd1=='get':
				self.send_file(c_sock,cmd2)	#客户端下载文件
			elif cmd1=='put':
				self.save_sile(c_sock)	#客户端上传文件
			else:	#其他非法命令
				c_sock.send(('未知命令: %s 请重新输入!' % cmds).encode('utf-8')) # send 错误信息
		c_sock.close()	#关闭客户端 socket
		print('客户端 {}:{} 连接关闭'.format(ip,port))
		

	def accept(self):	#接收客户端连接函数
		print('已启动守护进程监听ftp客户端连接...')
		while True:	#循环接收
			c_sock,(c_ip,c_port)=self.sock.accept()	# accept 客户端连接
			#创建客户端独立处理线程
			c_t=threading.Thread(target=self.recv,\
				name='child thread client ip:%s port:%s'% (c_ip,c_port),args=(c_sock,c_ip,c_port))
			c_t.start()

	def stop(self):	#关闭服务端
		self.sock.close()	#关闭服务端socket
		print('\nFtp-server 关闭')

	def start(self):	#服务端启动
		self.sock.bind(self.addr)	# bind 地址
		self.sock.listen()	# listen 监听连接
		#创建守护线程，不断监听接收客户端连接
		t=threading.Thread(target=self.accept,name='listen',daemon=True)
		try:
			t.start()
			t.join()
		except KeyboardInterrupt:	#捕捉ctrl c终止信号
			self.stop()	#关闭服务端socket
		

if __name__ == '__main__':
	ftp=FtpServer()	#ftp服务端实例
	ftp.start()