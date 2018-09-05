# -*- coding:utf-8 -*-
import serial
import serial.tools.list_ports
import threading
import binascii
import time
import data 
import analysis
import re
import struct
import asyncio
import init

class Serials(data.Data,object):
	"""docstring for Serials"""
	# 串口类
	# def __init__(self,com,*callback,**kw):
	def __init__(self, com, bps=115200, bytesize=8, parity='N', stopbits=1, *callback,**kw):
		# 初始化函数，设置串口的接收
		self.cb=callback[0]
		# 设置串口每一帧的结束字节
		self.split=callback[1]
		# 串口读取缓存
		self.buff=''
		self.refresh=time.time()
		self.funcs=[]
		self.foreverfuncs=[]
		# 打开串口
		try:
			# self.ser=serial.Serial('COM'+str(com),**kw)
			# self.ser=serial.Serial('COM'+str(com), bps, bytesize, parity, stopbits, **kw)
			self.ser=serial.Serial(str(com), bps, bytesize, parity, stopbits, **kw)
			if self.ser.isOpen():
				threading.Thread(target=self.Ser_rw).start()
		except Exception as e:
			print(e)
	# 串口读取函数，每隔10ms读取一次串口数据，将数据读取到buff中，通过回调函数进行处理
	def Ser_rw(self):
		while 1:
			n=self.ser.inWaiting()
			if(n>0):
				# self.buff+=self.ser.read(n).decode()
				try:
					self.buff+=self.ser.read(n).decode()
					self.refresh=time.time()
					while len(self.buff):
						index=self.buff.find(self.split)
						if(index>=0):
							raw=self.buff[0:index+len(self.split)]
							# print('raw:',raw)
							# 回调处理函数
							self.cb(raw)
							# 将数据放到日志记录的缓冲区
							self.set_raw(raw)
							self.buff=self.buff[index+len(self.split):]
						else:
							break
				except Exception as e:
					pass
					# print(e)
			self.Executefunc()
			if time.time()-self.refresh>=5:
				self.cb(self.name,2)
				time.sleep(1)
			time.sleep(0.01)
	def Registfunc(self,func,mode=0,*args,**kw):
		if mode==1:
			self.funcs.append([0,func,*args,kw])
		else:
			self.funcs.append([0,func,*args,kw])
	def Relievefunc(self):
		self.funcs=[]
	def Executefunc(self):
		if len(self.funcs):
			for func in self.funcs:
				func[1](func[2],**func[3])
				if func[0]==1:
					self.foreverfuncs.append(func)
			self.funcs=self.foreverfuncs
	def Write(self,s,mode=0):
		self.Registfunc(self.ser.write,mode,s.encode())         

#baudrate=115200,bytesize=serial.SEVENBITS,parity=serial.PARITY_EVEN
class Serial_Angle(data.Data):
	def __init__(self,com,**kw):
		if init.debug==1:
			if kw is None:
				kw={'baudrate':115200}
		else:
			if kw is None:
				kw={'baudrate':115200,'bytesize':serial.SEVENBITS,'parity':serial.PARITY_EVEN}
		self.info=analysis.Angle
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
						try:
							buf = self.ser.read(count)
							if self.checkData(buf):
								# print('data correct')
								angle = round(self.calAngle(buf)*360/self.rate/self.resolution,2)
								# print('angle:',angle)
								self.info('Angle',1,angle=angle)
							else:
								print('data error')
							self.errCount = 0
						except Exception as e:
							print(e)
					time.sleep(0.01)
				if count != 7:
					if count>0:
						buf = self.ser.read(count)
					self.errCount = self.errCount + 1
					if self.errCount > 5:
						self.info('Angle',2)
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
	# # 角度传感器类,继承自串口类
	# def __init__(self,com,**kw):
	# 	# if init.debug==1:
	# 	# 	kw={'baudrate':115200}
	# 	# else:
	# 	# 	if kw is None:
	# 	# 		kw={'baudrate':115200,'bytesize':serial.SEVENBITS,'parity':serial.PARITY_EVEN}
	# 	# 初始化角度传感器对象
	# 	# super().__init__(com,self.Callback,chr(0x0d),**kw)#ord('\r') chr(0x0d)
	# 	super().__init__(com, 9600, 7, 'N', 1, self.Callback,chr(0x0d),**kw)
	# 	#起始位：1 位（0）、数据位：7 位、校验位：偶校验、停止位：1 位（1）、编码标准：ASCⅡ码
	# 	self.info=analysis.Angle #设备 状态 数据
	# 	self.name='Angle'
	# 	self.rate=8
	# 	self.resolution=1024

	# # 角度传感器数据回调处理函数
	# def Callback(self,s,mode=0):
	# 	if mode==0:
	# 		# 正常状态
	# 		raw=s.encode()
	# 		# print('raw:',raw)
	# 		# 角度报文数据解析
	# 		if raw[0]==0x02 and re.match(r'^.\d{2}D(\+|-)\d{10}\r$',s):
	# 			angle=round(int(s[4:15])*360/self.rate/self.resolution,2)
	# 			addr=int(s[1:3])
	# 			if self.resolution==1.0:
	# 				print('当前未设置ANGLE单圈分辨率,默认值为1.0')
	# 			return self.info('Angle',1,angle=angle,addr=addr)
	# 		# 设置报文回复数据解析
	# 		elif raw[0]==0x03 and re.match(r'^.\d{2}P\d{1}\r$',s):
	# 			addr=int(s[1:3])
	# 			state=raw[4]
	# 			if state==0x30:
	# 				print('ADDR %s CLR SUCCESS'%addr)
	# 			if state==0x33:
	# 				print('CLR OUT OF RANGE')
	# 			if state==0x34:
	# 				print('NO AUTHORITY')
	# 			if state==0x35:
	# 				print('WRITE ERROR')
	# 			return self.info('Angle',state,addr=addr)
	# 	elif mode==2:
	# 		# 长时间没有数据
	# 		return self.info('Angle',2)
	# 	return 0

	# # 设置当前角度
	# def SetAngle(self, Addr, angle = 0):
	# 	data = 'CLR%02d%s%07d\r' % (Addr, '+' if angle>=0 else '-', abs(angle))
	# 	super().Write(data)

	# # 读取角度值
	# def ReadOrder(self, Addr):
	# 	super().Write('R%s\r' % Addr,1)

class Serial_GPS(Serials):
	# GPS类，继承自串口类
	def __init__(self,com,**kw):
		if kw is None:
			kw={'baudrate':115200,}
		# 初始化GPS对象
		# super().__init__(com,self.Callback,chr(0x0d)+chr(0x0a),**kw)#ord('\r') chr(0x0d)
		super().__init__(com, 115200, 8, 'N', 1, self.Callback, chr(0x0d)+chr(0x0a), **kw)
		#起始位：1 位（0）、数据位：7 位、校验位：偶校验、停止位：1 位（1）、编码标准：ASCⅡ码
		self.info=analysis.Gps
		self.name='GPS'

	# GPS数据回调处理函数
	def Callback(self,s,mode=0):
		if mode==0:
			# 正常状态
			index=s.rfind('$')
			if index >=0:
				s=s[index:]
				if(re.match(r'^\$GPRMC,[0-9.]*,(A|V),[0-9.]*,(N|S),[0-9.]*,(E|W),[0-9.]*,[0-9.]*,\d{6},.{3},.,.\*(\w\w)\r\n',s)):
				# if(re.match(r'\$(GPRMC|GPGGA).*\*\d{2}$',s)):
					if not analysis.XOR8(1,-5,s):
						s=s.split(',')
						if(s[0]=='$GPRMC'):
							if(s[2]=='A'):
								# 有效值
								UTC=str(2000+int(s[9][-2:]))+'-'+s[9][2:4]+'-'+s[9][:2]+' '+s[1][:2]+':'+s[1][2:4]+':'+s[1][4:]
								Lat=s[4]+str(float(s[3][:2])+float(s[3][2:])/60)
								Lon=s[6]+str(float(s[5][:3])+float(s[5][3:])/60)
								Speed=str(round(float(s[7])*1.852,2))
								Dir=s[8]
								return self.info('GPS',1,Lat=Lat,Lon=Lon,Speed=Speed,Dir=Dir,UTC=UTC)
								
							elif(s[2]=='V'):
								# 无效值
								print('GPS INVALID')
								return self.info('GPS',3)
		elif mode==2:
			# 长时间没有数据
			return self.info('GPS',2)
					
class Serial_LongRadar(Serials):
	# 长雷达类，继承自串口类
	def __init__(self,com,**kw):
		if kw is None:
			kw={'baudrate':115200,}
		# 初始化长雷达对象
		# super().__init__(com,self.Callback,'|',**kw)
		super().__init__(com, 115200, 8, 'N', 1, self.Callback, '|', **kw)
		self.info=analysis.Radar
		self.name='LongRadar'
		# self.RadarInit(11,100);

	# 长雷达数据回调处理函数
	def Callback(self,s,mode=0):
		if mode==0:
			# 正常状态
			index=s.rfind('&')
			if index >=0:
				s=s[index:]
				if re.match(r'^&(100|200)\w{21}\|$',s):
					raw=s.encode()
					if s[:4]=='&100':
						# 状态报文
						mode, angle, radius, Radarstate, Ctlstate = [int(d, 16) for d in struct.unpack('2s3s3scc', raw[4:14])]
						if((mode+ angle+radius+Radarstate+Ctlstate)%256==int(s[-3:-1],16)):
							angle/=4.0
							if(Radarstate&Ctlstate)==1:
								data.Data.LongRadarMsgCycle()
								return self.info('LongRadar',1)#链接，正常
							else:
								return self.info('LongRadar',3)
							# print(mode, angle, radius, Radarstate, Ctlstate)
					elif s[:4]=='&200':
						# 信息报文
						objId, lonsht, latsht, dynamic, measurestate, length, width, probability, lonspeed, latspeed=[int(d, 16) for d in struct.unpack('2s3s3sccccc3s3s', raw[4:23])]
						# 校验值有误差，去掉校验
						# if (objId+lonsht+latsht+dynamic+measurestate+length+width+probability+lonspeed+latspeed)%256==int(s[-3:-1],16):
						lonsht = round(lonsht*0.1,2)
						latsht = round(latsht*0.1-52)
						# length = length
						# width = width
						lonspeed = round(lonspeed*0.0625-128)
						latspeed = round(latspeed*0.25-32)
						# print('data:')
						# print('objId:', objId)
						# print('lonsht:', lonsht)
						# print('latsht:', latsht)
						# print('dynamic:', dynamic)
						# print('measurestate:', measurestate)
						# print('probability:', probability)
						# print('length:', length)
						# print('width:', width)
						# print('lonspeed:', lonspeed)
						# print('latspeed:', latspeed)
						# 报文分析
						return	self.info('LongRadar',1,objId=objId,lonsht=lonsht,latsht=latsht,
									dynamic=dynamic,measurestate=measurestate,length=length,width=width,
									probability=probability,lonspeed=lonspeed,latspeed=latspeed)
					else:
						return self.info('LongRadar',1)
		elif mode==2:
			# 连接断开状态
			return self.info('LongRadar',2)

	def RadarInit(self,radarAngle,radarRange):
		if 0<=radarAngle<=32 and 50<=radarRange<=200:
			for i in range(30):
				self.ser.write(('&333%02d%03d%s%02x|' % (radarAngle, radarRange, '0'*14, (radarAngle+radarRange)%256)).encode())
				time.sleep(1)
				# while True:
				# 	self.ser.write(('&333%02d%03d%s%02x|' % (radarAngle, radarRange, '0'*14, (radarAngle+radarRange)%256)).encode())
				# 	time.sleep(1)
		else:
			print('out of range')

class Serial_LeftRadar(Serials):
	# 短程雷达左类，继承自串口类
	def __init__(self,com,**kw):
		if kw is None:
			kw={'baudrate':115200,}
		# 初始化短程雷达左对象
		# super().__init__(com,self.Callback,'|',**kw)
		super().__init__(com, 115200, 8, 'N', 1, self.Callback, '|', **kw)
		self.info=analysis.Radar
		self.name='LeftRadar'
	# 左边的短程雷达数据回调处理函数
	def Callback(self,s,mode=0):
		if mode==0:
			# 正常状态
			index=s.rfind('&')
			if index >=0:
				s=s[index:]
				if re.match(r'^&(100|200)\w{24}\|$',s):
					raw=s.encode()
					if s[:4]=='&100':
						# 状态报文
						mode, angle, radius, Radarstate, Ctlstate = [int(d, 16) for d in struct.unpack('2s3s3scc', raw[4:14])]
						if((mode+ angle+radius+Radarstate+Ctlstate)%256==int(s[-3:-1],16)):
							angle/=4.0
							if(Radarstate&Ctlstate)==1:
								data.Data.LRRadarMsgCycle('L')
								return self.info('LeftRadar',1)#链接，正常
							# else:
							# 	return self.info('LeftRadar',3)
							# print(mode, angle, radius, Radarstate, Ctlstate)
					elif s[:4]=='&200':
						# 信息报文
						objId, lonsht, latsht, dynamic, measurestate, probability, length, width, lonspeed, rcs, latspeed=[int(d, 16) for d in struct.unpack('2s4s3sccc2s2s3s2s3s', raw[4:28])]
						lonsht = round(lonsht*0.2-500,2)
						latsht = round(latsht*0.2-204.6,2)
						length = round(length*0.2,2)
						width = round(width*0.2,2)
						lonspeed = round(lonspeed*0.25-128)
						latspeed = round(latspeed*0.25-64)
						# 报文分析
						return	self.info('LeftRadar',1,objId=objId,lonsht=lonsht,latsht=latsht,
									dynamic=dynamic,measurestate=measurestate,length=length,width=width,
									probability=probability,lonspeed=lonspeed,latspeed=latspeed)
					else:
						return self.info('LeftRadar',1)
		elif mode==2:
			# 长时间未收到左边的短程雷达数据
			return self.info('LeftRadar',2)

	# 设置雷达角度函数
	def SetOrder(self, angle, radius):
		if 0<=angle<=32 and 50<=radius<=200:
			self.write('&333%02d%03d%s%02x|' % (angle, radius, '0'*14, (angle+radius)%256))

class Serial_RightRadar(Serials):
	# 短程雷达右类，继承自串口类
	def __init__(self,com,**kw):
		if kw is None:
			kw={'baudrate':115200,}
		# 初始化短程雷达右对象
		# super().__init__(com,self.Callback,'|',**kw)
		super().__init__(com, 115200, 8, 'N', 1, self.Callback, '|', **kw)
		self.info=analysis.Radar
		self.name='RightRadar'

	# 右边的短程雷达数据回调处理函数
	def Callback(self,s,mode=0):
		if mode==0:
			# 正常状态
			index=s.rfind('&')
			if index >=0:
				s=s[index:]
				if re.match(r'^&(100|200)\w{24}\|$',s):
					raw=s.encode()
					if s[:4]=='&100':
						# 信息报文
						mode, angle, radius, Radarstate, Ctlstate = [int(d, 16) for d in struct.unpack('2s3s3scc', raw[4:14])]
						if((mode+ angle+radius+Radarstate+Ctlstate)%256==int(s[-3:-1],16)):
							angle/=4.0
							if(Radarstate&Ctlstate)==1:
								data.Data.LRRadarMsgCycle('R')
								return self.info('RightRadar',1)#链接，正常
							# else:
							# 	return self.info('RightRadar',3)
							# print(mode, angle, radius, Radarstate, Ctlstate)
					elif s[:4]=='&200':
						# 状态报文
						objId, lonsht, latsht, dynamic, measurestate, probability, length, width, lonspeed, rcs, latspeed=[int(d, 16) for d in struct.unpack('2s4s3sccc2s2s3s2s3s', raw[4:28])]
						lonsht = round(lonsht*0.2-500,2)
						latsht = round(latsht*0.2-204.6,2)
						length = round(length*0.2,2)
						width = round(width*0.2,2)
						lonspeed = round(lonspeed*0.25-128)
						latspeed = round(latspeed*0.25-64)
						# 报文分析
						return	self.info('RightRadar',1,objId=objId,lonsht=lonsht,latsht=latsht,
									dynamic=dynamic,measurestate=measurestate,length=length,width=width,
									probability=probability,lonspeed=lonspeed,latspeed=latspeed)
					else:
						print('!!!')
						return self.info('RightRadar',1)
		elif mode==2:
			# 长时间未收到右边的短程雷达数据
			return self.info('RightRadar',2)

	# 设置雷达角度函数
	def SetOrder(self, angle, radius):
		if 0<=angle<=32 and 50<=radius<=200:
			self.write('&333%02d%03d%s%02x|' % (angle, radius, '0'*14, (angle+radius)%256))

def check(a,b):
	# 雷达校验码计算，hex函数返回0x格式的字符串，取最后两个值
	return hex(a+b)[-2:]

if __name__=='__main__':
	a=Serial_LeftRadar(2)

	s5=b'&2000302F21F131170000005e|'
	objId, lonsht, latsht, dynamic, measurestate, length, width, probability= [int(d, 16) for d in struct.unpack('2s3s3sccccc', s5[4:17])]
	
	y=lonsht*0.1
	x=latsht*0.1-52
	print(objId, x, y, dynamic, measurestate, length, width, probability,hex(int(objId+lonsht+latsht+dynamic+measurestate+length+width+probability)%256))

	