import data
import analysis
import re
import socket
import time
import threading
import struct

class ShortRadar(data.Data,object):
	"""docstring for ShortRadar"""
	def __init__(self, port):
		self.info=analysis.Radar
		self.lrefresh=time.time()
		self.rrefresh=time.time()
		self.port = port
		threading.Thread(target=self.shortRadarDataRecv).start()
		threading.Thread(target=self.checkTimeout).start()

	def shortRadarDataRecv(self):
		sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(('0.0.0.0',self.port))
		while True:
			recvdata,addr=sock.recvfrom(10000)
			try:
				dedata = recvdata.decode()
				# 数据添加到日志
				self.set_raw(dedata)
				radar,msgdata = dedata[:4],dedata[4:]
				if radar == 'can0':
					radarType = 'LeftRadar'
					self.lrefresh=time.time()
				else:
					radarType = 'RightRadar'
					self.rrefresh=time.time()
				self.dataHandle(radarType,msgdata,0)
			except Exception as e:
				print(e)

	def dataHandle(self,radarType,msgdata,mode=0):
		if mode==0:
			# 正常状态
			index=msgdata.rfind('&')
			if index >=0:
				msgdata=msgdata[index:]
				if re.match(r'^&(100|200)\w{24}\|$',msgdata):
					raw=msgdata.encode()
					if msgdata[:4]=='&100':
						# 状态报文
						mode, angle, radius, Radarstate, Ctlstate = [int(d, 16) for d in struct.unpack('2s3s3scc', raw[4:14])]
						if((mode+ angle+radius+Radarstate+Ctlstate)%256==int(msgdata[-3:-1],16)):
							angle/=4.0
							if(Radarstate&Ctlstate)==1:
								if radarType=='LeftRadar':
									data.Data.LRRadarMsgCycle('L')
								else:
									data.Data.LRRadarMsgCycle('R')
								print('shortradar 100')
								return self.info(radarType,1)#链接，正常
							# else:
							# 	return self.info('LeftRadar',3)
							# print(mode, angle, radius, Radarstate, Ctlstate)
					elif msgdata[:4]=='&200':
						# 信息报文
						objId, lonsht, latsht, dynamic, measurestate, probability, length, width, lonspeed, rcs, latspeed=[int(d, 16) for d in struct.unpack('2s4s3sccc2s2s3s2s3s', raw[4:28])]
						lonsht = round(lonsht*0.2-500,2)
						latsht = round(latsht*0.2-204.6,2)
						length = round(length*0.2,2)
						width = round(width*0.2,2)
						lonspeed = round(lonspeed*0.25-128)
						latspeed = round(latspeed*0.25-64)
						print('shortradar 200')
						# 报文分析
						return	self.info(radarType,1,objId=objId,lonsht=lonsht,latsht=latsht,
									dynamic=dynamic,measurestate=measurestate,length=length,width=width,
									probability=probability,lonspeed=lonspeed,latspeed=latspeed)
			pass
		elif mode==2:
			# 长时间未收到左边的短程雷达数据
			return self.info(radarType,2)

	def checkTimeout(self):
		while True:
			if (time.time() - self.lrefresh) > 5:
				# print('left radar error')
				self.info('LeftRadar',2)
			if (time.time() - self.rrefresh) > 5:
				# print('right radar error')
				self.info('RightRadar',2)
			time.sleep(1)

if __name__ == '__main__':
	shortradar = ShortRadar(9000)
	s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	while True:
		s.sendto('can0&200000000c811000000000000ca|'.encode(),('127.0.0.1',9000))
		time.sleep(1)
