# -*- coding:utf-8 -*-
# 本文件为测试文件，用于测试各模块是否正常工作
import socket 
import threading
import time
import asyncio
import re
import serial
import json
import datetime

def TCP_Client_test(host='127.0.0.1',port=4000,msg=None):
	while True:
		while True:
			try:
				client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
				client.connect((host,port))
				break
			except Exception as e:
				client.close()
				print('主机可能未开启,1秒后重试',e)
				time.sleep(1)
		while True:
			try:
				replydata = dict()
				replydata['Time'] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
				replydata['Method'] = "302"
				MethodBody = dict()
				MethodBody['FwdTrainID'] = '1001'
				MethodBody['BackTrainID'] = '1003'
				MethodBody['LocalID'] = '1002'
				MethodBody['FwdIP'] = "192.168.1.14"
				MethodBody['BackIP'] = "192.168.1.16"
				MethodBody['LocalIP'] = "192.168.1.12"
				replydata['MethodBody'] = MethodBody
				client.send(json.dumps(replydata).encode())
				#client.send(('client %s'%msg).encode())
				'''
				data=client.recv(10000).decode()
				if data:
					print(data)
				'''
			except Exception as e:
				print(e)
				client.close()
				break
			time.sleep(1)
		
def GPS_Collect_test(port=4000):
	client=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	client.bind(('',port))
	while True:
		try:
			data,addr=client.recvfrom(10000)
			if data:
				print('GPS:',data.decode(),addr)
		except Exception as e:
			print(e)
def GPS_Send_test(port=4000):
		sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		while True:
			sock.sendto(str({'GPS':'11.22 33.44'}).encode(),('<broadcast>',port))
			time.sleep(1)
def UDP_GET_test(host='0.0.0.0',port=4002):       
		client=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client.bind((host,port))
		while True:
			try:
				data,addr=client.recvfrom(10000)
				if data:
					# print('GET:',data.decode(),addr)
					r=json.loads(data.decode())
					# for i in r.items():
					# 	print(i)
					print(r,addr)
					client.sendto('UDP GET'.encode(),addr)
			except Exception as e:
				print(e)
def UDP_SEND_test(host='127.0.0.1',port=4002):
	sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
	while True:
			sock.sendto('UDP_SEND'.encode(),(host,port))
			time.sleep(0.1)
def Get_IP(inner=1,match=None):
	if inner==0:
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(('8.8.8.8', 80))
			ip = s.getsockname()[0]
		finally:
			s.close()
	else:
		if match==None:
			name=socket.getfqdn(socket.gethostname())
			ip=socket.gethostbyname(name)
		else:
			if isinstance(match,str):
				if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',match):
					for i in socket.gethostbyname_ex(socket.gethostname())[2]:
						if i.startswith(re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d{1,3})',match).group(1)):
							ip=i
							break
	return ip               
class COMS(object):
	def __init__(self, raw,*coms,**kw):
		com={}
		for i in coms:
			com.update({'COM'+str(i):'COM'+str(i)})
		for i,j in zip(com.keys(),range(len(coms))) :
			com[i]=serial.Serial(i)
			threading.Thread(target=self.Ser_rw,args=(com[i],raw[j],)).start()
			time.sleep(0.2)
		print('开始发送数据at:',com.keys())
	def Ser_rw(self,com,s):
		while 1:
			if com.isOpen():
					if not isinstance(s,bytes):
						com.write(s.encode())
					else:
						com.write(s)
			time.sleep(1)

class SERIALPORT(object):
	def __init__(self,port,**kw):
		self.sarray = []
		self.space = 60
		self.status = '&100000000821100000000000084|'
		self.origindis = 10
		# for i in range(5):
		# 	self.sarray.append(self.generateData(i,self.origindis+i*self.space,0,1,1,5,4,2,4,4,0))
		self.com = serial.Serial('COM'+str(port))
		threading.Thread(target=self.serport_rw).start()

	def generateData(self,id,lonsht,latsht,dynamicfeature,mstate,probability,length,width,lonspeed,rcs,latspeed):
		lonsht = round((lonsht + 500)*5)
		latsht = round((latsht + 204.6)*5)
		length = round(length*5)
		width = round(width*5)
		lonspeed = round((lonspeed+128)*4)
		latspeed = round((latspeed+64)*4)
		return '&200%02x%04x%03x%01x%01x%01x%02x%02x%03x%02x%03x|'%(id,lonsht,latsht,dynamicfeature,mstate,probability,length,width,lonspeed,rcs,latspeed)

	def serport_rw(self):
		time.sleep(2)
		rate = 0.4
		cnt = 0
		while True:
			# if self.com.isOpen():
				# print('s:',self.s)
				# print('encoded s:',self.s.encoded())
			self.com.write(self.status.encode())
			time.sleep(0.1)
			self.sarray = []
			for i in range(5):
				templonsht = self.origindis+i*self.space-cnt*rate
				if templonsht > 0:
					self.sarray.append(self.generateData(i,templonsht,0,1,1,5,4,2,4,4,0))
				else:
					self.sarray.append(self.generateData(i,20,0,1,1,5,4,2,4,4,0))
			for s in self.sarray:
				self.com.write(s.encode())
				time.sleep(0.1)
			cnt += 1
			time.sleep(0.2)

def Tcp_test(host,port):
	client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	client.connect((host,port))
	threading.Thread(target=Tcp_send, args=(client,)).start()
	threading.Thread(target=Tcp_recv, args=(client,)).start()

def Tcp_send(sock):
	time.sleep(10)
	replydata = dict()
	replydata['Time'] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
	replydata['MsgCode'] = "302"
	MethodBody = dict()
	MethodBody['FwdTrainID'] = '1001'
	MethodBody['BackTrainID'] = '1003'
	MethodBody['LocalID'] = '1002'
	MethodBody['FwdIP'] = "192.168.10.14"
	MethodBody['BackIP'] = "192.168.10.105"
	MethodBody['LocalIP'] = "192.168.10.103"
	replydata['MethodBody'] = MethodBody
	sock.send(json.dumps(replydata).encode())
	#print('send data:',json.dumps(replydata).encode())
	data2 = json.loads(sock.recv(10000).decode('utf-8'))
	print('data2:',data2)
	#if data['Method'] == '202':
		#print(data)
	time.sleep(1)

def Tcp_recv(sock):
	while True:
		recvdata = sock.recv(10000).decode()
		data = json.loads(recvdata)
		if data['MsgCode'] == '201':
			replydata = dict()
			replydata['Time'] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
			replydata['MsgCode'] = "301"
			MethodBody = dict()
			MethodBody['Result'] = '1'
			MethodBody['Reason'] = ''
			MethodBody['FwdTrainID'] = '1001'
			MethodBody['BackTrainID'] = '1003'
			MethodBody['LocalID'] = '1002'
			MethodBody['FwdIP'] = "192.168.10.11"
			MethodBody['BackIP'] = "192.168.10.13"
			MethodBody['LocalIP'] = "192.168.10.12"
			replydata['MethodBody'] = MethodBody
			sock.send(json.dumps(replydata).encode())

class testser(object):
	"""docstring for testser"""
	def __init__(self,com,**kw):
		self.rate=8
		self.resolution=1024
		self.queryAngle = [0x01,0x52,0x53]
		self.errCount = 0
		try:
			# self.ser=serial.Serial('COM'+str(com),**kw)
			# self.ser=serial.Serial('COM'+str(com), bps, bytesize, parity, stopbits, **kw)
			self.ser=serial.Serial(str(com), 9600, 8, 'N', 1, **kw)
			if self.ser.isOpen():
				threading.Thread(target=self.Ser_rw).start()
		except Exception as e:
			print(e)

	def Ser_rw(self):
		while True:
			try:
				# 查询当前角度
				self.ser.write(self.queryAngle)
				count = 0
				curTime = time.time()
				# while count < 7 and (time.time()-curTime)<=0.5:
				while count < 7:
					count = self.ser.inWaiting()
					if count == 7:
						buf = self.ser.read(count)
						if self.checkData(buf):
							print('data correct')
							angle = round(self.calAngle(buf)*360/self.rate/self.resolution,2)
							print('angle:',angle)
							# self.info('Angle',1,angle=angle,addr=addr)
						else:
							print('data error')
						self.errCount = 0
					time.sleep(0.01)
				if count != 7:
					if count>0:
						buf = self.ser.read(count)
					self.errCount = self.errCount + 1
					if self.errCount > 5:
						pass
			except Exception as e:
				print(e)
			time.sleep(1)

	def checkData(self,buf):
		result = 0x00
		for i in range(len(buf)-1):
			result += buf[i]
		if result%256 == buf[-1]:
			return True
		else:
			return False

	def calAngle(self,buf):
		return buf[2]*256*256*256+buf[3]*256*256+buf[4]*256+buf[5]

if __name__ == '__main__':
	angleSerial = testser('COM11')
	# leftR = SERIALPORT(23)
	# leftR.sarray = ['&100000000821100000000000084|','&2000009D93FD1270C0C20077100|','&2000109CE3FF12705052008E100|']
	# threading.Thread(target=Tcp_test,args=('127.0.0.1',5000)).start()
	# threading.Thread(target=TCP_Client_test,args=('127.0.0.1',4000,'msg',)).start()
	# threading.Thread(target=GPS_Collect_test,args=(4000,)).start()
	# threading.Thread(target=GPS_Send_test,args=(4000,)).start()
	# threading.Thread(target=UDP_GET_test,args=('0.0.0.0',4002,)).start()
	# #threading.Thread(target=UDP_SEND_test,args=('127.0.0.1',4002,)).start()
	#s=['$GPRMC,044549.60,A,3955.7333600,N,11607.6355300,E,13.6,325.1,010616,999,E,A*12\r\n',b'\x0201D+0000002685\r',
	#b'&2000102F1eF131170000002c|',b'&200040FF22F131170000003f|',b'&2000302F21F131170000005e|']
	#s=['$GPRMC,044549.60,A,3955.7333600,N,11607.6355300,E,13.6,325.1,010616,999,E,A*12\r\n',b'\x0201D+0000002685\r']
	# gpsSerial=SERIALPORT(21)
	# gpsSerial.s ='$GPRMC,044549.60,A,3955.7333600,N,11607.6355300,E,13.6,325.1,010616,999,E,A*12\r\n'
	
	# angleSerial=SERIALPORT(22)
	# angleSerial.s = b'\x0201D+0000002685\r'

	# leftRSerial=SERIALPORT(23)
	# leftRSerial.s ='&200010bb844c1350a0594c69|'

	# longRSerial=SERIALPORT(24)
	# longRSerial.s ='&200010bb83ff1350a14800df|'

	# rightRSerial=SERIALPORT(23)
	# rightRSerial.s ='&200010bb83b61350a0594cd3|'

	# 01 44 00 00 0A 7D CC
	# 31 32 33 34 35 36 37

