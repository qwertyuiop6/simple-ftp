import socket,os
import threading,struct,json
import progressbar

class FtpClent(object):
	
	def __init__(self):		#初始化实例属性
		self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #定义ipv4 tcp socket
		self.s_ip='127.0.0.1'
		self.s_port=2121
		self.s_addr = (self.s_ip, self.s_port) #地址
		self.c_dir = os.getcwd()+'/client/' #客户端目录
		self.buf =1024  #缓冲区大小	

	def stop(self):	#终止连接函数
		self.sock.send(b'quit')	# send 断开请求信息
		self.sock.close()	#关闭sock连接
		print('\nFtp-Client 连接关闭')	

	def recv_msg(self):	#接收回复函数
		msg=self.sock.recv(self.buf).decode('utf-8') # recv 服务端回复
		print(msg)

	def send_file(self,filename):  #发送文件函数
		filepath=self.c_dir+filename #文件路径
		filesize=os.stat(filepath).st_size #文件大小size
		# 打包文件头信息，包含文件名和文件大小, 定义为128字节大小
		fhead = struct.pack('128sl',filename.encode('utf-8'),filesize)
		self.sock.send(fhead)  #先 send 文件头信息给服务端

		bar = progressbar.ProgressBar(widgets=[
			'[',progressbar.Bar(),']',
    		progressbar.Percentage(),
    		' (', progressbar.ETA(), ') ',])  #进度对象实例
		print('正在发送: "%s" 大小:[%s]Bytes'%(filename,filesize))

		bar.start()
		with open(self.c_dir+filename,'rb') as f:  #打开文件
			sent=0
			for data in f:
				sent+=self.sock.send(data)  #循环 send 二进制文件字节流数据
				bar.update(sent/filesize*100)
		bar.finish()

	def save_sile(self):	#保存文件函数
		fileinfo_size = struct.calcsize('128sl') #约定的文件头信息大小
		# recv 头信息流数据,解包得到文件名，文件大小信息
		filename,filesize=struct.unpack('128sl',self.sock.recv(fileinfo_size))
		filename=filename.decode('utf-8')
		bar = progressbar.ProgressBar(widgets=[
			'[',progressbar.Bar(),']',
    		progressbar.Percentage(),
    		' (', progressbar.ETA(), ') ',]) #进度对象
		
		with open('{}{}'.format(self.c_dir,filename.strip('\0')),'wb') as f:
			print('正在下载: "%s" 大小:[%s]Bytes'% (filename,filesize))
			bar.start()
			recv_size=0  	#定义已接收文件字节大小
			while recv_size<filesize:   	#循环接收
				filedata=self.sock.recv(self.buf)   # recv 文件流数据
				f.write(filedata)   	#写入文件流
				recv_size+=len(filedata)    #更新已接收字节量
				bar.update(recv_size/filesize*100)
			bar.finish()
			print('%s 下载完毕'%filename)

	def start(self):   #主函数,循环监听命令 接收回复
		self.sock.connect(self.s_addr) 	# connect 服务端地址
		print(self.sock.recv(self.buf).decode('utf-8'))  # recv 服务端欢迎信息
		try:
			while True:	#循环监听输入命令
				cmds=input('ftp@'+self.s_ip+':'+str(self.s_port)+' >> ').strip()
				if not cmds:
					print('命令不能为空！')
					continue
				if cmds=='quit' or cmds=='exit':
					break
				action=cmds.split()[0]  #命令
				if len(cmds.split())>1:
					target=cmds.split()[1]  #参数
				if action=='cd' and len(cmds.split())==1:
					print('cd命令用法: cd 文件夹')
					continue
				if action=='get':	#判断为get
					if len(cmds.split())==1:
						print('get命令用法: get 文件名')
						continue
					self.sock.send(cmds.encode('utf-8')) # send	输入信息到服务端解析
					get_f_res=self.sock.recv(self.buf)	# recv 文件存在与否信息
					if get_f_res==b'0':	
						print('服务端不存在 %s 文件'% target)
						continue
					elif get_f_res==b'2':	#文件夹
						print('%s 不是一个文件'% target)
						continue
					self.save_sile()	#保存文件
				elif action=='put':	#判断为put
					if len(cmds.split())==1:
						print('put命令用法: put 文件名')
						continue
					if target not in os.listdir(self.c_dir):	#本地文件不存在
						print('客户端不存在 %s 文件'% target)
						continue
					elif os.path.isdir(self.c_dir+target):	#文件夹
						print(' %s 不是一个文件'% target)
						continue
					self.sock.send(cmds.encode('utf-8')) # send 输入信息到服务端解析
					self.send_file(target)	#发送文件
				else: 	#其他命令
					self.sock.send(cmds.encode('utf-8')) # send 输入信息到服务端解析
					self.recv_msg() #接收服务端回复
			self.stop() #终止连接
		except KeyboardInterrupt:	#ctrl c终止信号
			self.stop() #终止连接

if __name__ == '__main__':
	ftp_client=FtpClent()  #new ftp客户端实例
	ftp_client.start()    
		
