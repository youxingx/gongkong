# -*- coding:utf-8 -*-
import re
import time
import socket
import data
import serial
import struct
from math import radians, cos, sin, asin, sqrt,tan,atan,pi,acos
from operator import itemgetter

#雷达阈值
LONGRADARLENGTH = 2
LONGRADARWIDTH = 2
LONGRADARPROBABILITY = 5
LONGSPEED = 50
# TRACKWIDTH = [-3,1]
TRACKWIDTH = [-2,0]

# LEFTRADARLENGTH = [0,4]
# LEFTRADARWIDTH = [0,2]
LEFTRADARLENGTH = [1,5]
LEFTRADARWIDTH = [1,3]
LEFTRADARPROBABILITY = 5
LEFTSPEED = 20
# LEFTOBSRANGE = [-3,1]
LEFTOBSRANGE = [-8,3]

RIGHTRADARLENGTH = [1,5]
RIGHTRADARWIDTH = [1,3]
RIGHTRADARPROBABILITY = 5
RIGHTSPEED = 20
RIGHTOBSRANGE = [-3,8]
MAXTARGETNUM = 4
# MEASURESTATEFILTER = 3
# MEASURESTATEFILTER = 6

def AP(*args,**kw):
	# 前后车通信处理函数
	if (args[0]=='GET'):
		# print('data:', kw['data'])
		if 'ID' in kw['data']:
			if(kw['data']['ID'] == data.Data.ini['fwdTrainID'] and kw['data']['LocalIp'] == data.Data.ini['fwdTrainIP']):
				data.Data.FB_GPS[0] = {'Lat':kw['data']['Lat'],'Lon':kw['data']['Lon'],'Speed':kw['data']['Speed'],'Dir':kw['data']['Dir'],
							'distance_font':'invalid','ID':data.Data.LOCAL_ID}
				if data.Data.Statelist[5]['Status'] == '1':
					# 本地的GPS状态正常
					if data.Data.LOCAL_GPS['Lat'] !='invalid' and data.Data.LOCAL_GPS['Lon'] !='invalid':
						distance_F=haversine(float(data.Data.FB_GPS[0]['Lat'][1:]),float(data.Data.FB_GPS[0]['Lon'][1:]),float(data.Data.LOCAL_GPS['Lat'][1:]),float(data.Data.LOCAL_GPS['Lon'][1:]))
						if data.Data.LONG_RADAT_DIST!='0' and 100>=float(data.Data.LONG_RADAT_DIST)>=0:
							distance_F=data.Data.LONG_RADAT_DIST
						data.Data.FB_GPS[0]['distance_font'] = str(distance_F)
						data.Data.TrainMsg['TrainFwd'] = str(distance_F)
				data.Data.FBL_TIMEOUT['F']=5
			if(kw['data']['ID'] == data.Data.ini['backTrainID'] and kw['data']['LocalIp'] == data.Data.ini['backTrainIP']):
				data.Data.FB_GPS[1] = {'Lat':kw['data']['Lat'],'Lon':kw['data']['Lon'],'Speed':kw['data']['Speed'],'Dir':kw['data']['Dir'],
							'distance_font':'invalid','ID':data.Data.LOCAL_ID}
				if data.Data.Statelist[5]['Status'] == '1':
					# 本地的GPS状态正常
					if data.Data.LOCAL_GPS['Lat'] !='invalid' and data.Data.LOCAL_GPS['Lon'] !='invalid':
						distance_B=haversine(float(data.Data.FB_GPS[1]['Lat'][1:]),float(data.Data.FB_GPS[1]['Lon'][1:]),float(data.Data.LOCAL_GPS['Lat'][1:]),float(data.Data.LOCAL_GPS['Lon'][1:]))
						data.Data.FB_GPS[1]['distance_font'] = str(distance_B)
						data.Data.TrainMsg['TrainBack'] = str(distance_B)
				data.Data.FBL_TIMEOUT['B']=5
			data.Data.Statelist[6]['Status'] = '1'
			# print('TrainMsg:',data.Data.TrainMsg)
	elif args[0]=='F':
		data.Data.Statelist[7]={'Device':'7','Status':str(args[1])}
		data.Data.FB_GPS[0]={'Lat':'invalid','Lon':'invalid','Speed':'invalid','Dir':'invalid','distance_font':'invalid'}
		data.Data.TrainMsg['TrainFwd'] = str(data.Data.LONG_RADAT_DIST)
		if data.Data.Statelist[8]['Status'] == '2':
			# 后车通讯也故障
			data.Data.Statelist[6]['Status'] = '2'
	elif args[0]=='B':
		data.Data.Statelist[8]={'Device':'8','Status':str(args[1])}
		data.Data.FB_GPS[1]={'Lat':'invalid','Lon':'invalid','Speed':'invalid','Dir':'invalid','distance_font':'invalid'}
		data.Data.TrainMsg['TrainBack'] = '0'
		if data.Data.Statelist[7]['Status'] == '2':
			# 前车通讯也故障
			data.Data.Statelist[6]['Status'] = '2'

def Gps(*args,**kw):
	# gps数据处理函数
	distance_F='0'
	distance_B='0'
	data.Data.Statelist[5]={'Device':'5','Status':str(args[1])}
	if kw:
		data.Data.LOCAL_GPS={'Lat':kw['Lat'],'Lon':kw['Lon'],'Speed':kw['Speed'],'Dir':kw['Dir'],
							'distance_font':'invalid','ID':data.Data.LOCAL_ID,'LocalIp':data.Data.LOCAL_IP}
		# print('serial LOCAL_GPS:', data.Data.LOCAL_GPS)
		if data.Data.Statelist[7]['Status'] == '1':
			# 前车GPS状态正常
			if data.Data.FB_GPS[0]['Lon'] !='invalid' and data.Data.FB_GPS[0]['Lat'] !='invalid':#前车
				distance_F=haversine(data.Data.FB_GPS[0]['Lat'][1:],data.Data.FB_GPS[0]['Lon'][1:],kw['Lat'][1:],kw['Lon'][1:])
				# 长雷达设备状态正常，长雷达探测前车距离<100m
				if data.Data.Statelist[3]['Status']=='1' and 100>=float(data.Data.LONG_RADAT_DIST)>=0:
					distance_F=data.Data.LONG_RADAT_DIST
			else:
				distance_F=data.Data.LONG_RADAT_DIST
		else:
			# 前车GPS状态出错
			distance_F=data.Data.LONG_RADAT_DIST
		# if data.Data.FB_GPS[1]['distance_font']!='invalid':
		# 	distance_B=data.Data.FB_GPS[1]['distance_font']
		if data.Data.Statelist[7]['Status'] == '1':
			# 后车GPS状态正常
			if data.Data.FB_GPS[1]['Lon'] !='invalid' and data.Data.FB_GPS[1]['Lat'] !='invalid':#后车
				distance_B=haversine(float(data.Data.FB_GPS[1]['Lat'][1:]),float(data.Data.FB_GPS[1]['Lon'][1:]),float(kw['Lat'][1:]),float(kw['Lon'][1:]))
		else:
			distance_B='0'
		data.Data.LOCAL_GPS['distance_font']=distance_F
		# print('distance_F:', distance_F)
		# print('distance_B:', distance_B)
		data.Data.TrainMsg={		'TrainFwd':str(distance_F),
									'TrainBack':str(distance_B),
									'TrainRate':str(kw['Speed'])}
	else:
		# data.Data.LOCAL_GPS={'Lat':'invalid','Lon':'invalid','Speed':'invalid','Dir':'invalid','distance_font':'invalid'}
		# LOCAL_GPS={'Lon':'invalid','Lat':'invalid','Speed':'invalid','Dir':'invalid','distance_font':'invalid','ID':'0000','LocalIp':str(LOCAL_IP)}
		data.Data.LOCAL_GPS['Lon'] = 'invalid'
		data.Data.LOCAL_GPS['Lat'] = 'invalid'
		data.Data.LOCAL_GPS['Speed'] = 'invalid'
		data.Data.LOCAL_GPS['Dir'] = 'invalid'
		data.Data.LOCAL_GPS['distance_font'] = '0'
		data.Data.TrainMsg['TrainFwd'] = data.Data.LONG_RADAT_DIST
		data.Data.TrainMsg['TrainBack'] = '0'

def Angle(*args,**kw):
	# 角度处理函数
	data.Data.Statelist[4]={'Device':str(4),'Status':str(args[1])}
	if kw:
		data.Data.AngleMsg={'AngleData':str(kw['angle'])}
	else:
		data.Data.AngleMsg={'AngleData':'invalid'}
	# print('AngleMsg:',data.Data.AngleMsg)
def Radar(*args,**kw):
	if args[0]=='LongRadar':
		# 长程雷达处理函数
		data.Data.Statelist[3]={'Device':'3','Status':str(args[1])}
		if kw:
			if kw['measurestate'] != 2:
				# print('measurestate')
				#物体状态过滤
				if kw['lonspeed'] < LONGSPEED:
					# print('speed')
					#物体速度过滤
					if kw['probability']>=LONGRADARPROBABILITY:
						if kw['length']>=LONGRADARLENGTH and kw['width']>=LONGRADARWIDTH:
							# print('length,width,probability')
							#物体尺寸和概率过滤
							if kw['latsht']>=TRACKWIDTH[0] and kw['latsht']<=TRACKWIDTH[1]:
								#界限过滤
								# print('latsht')
								# print('lonsht:', kw['lonsht'])
								# print('dlongy:', dlongy)
								# data.Data.LONG_RADAT_DIST=kw['lonsht']-dlongy
								# data.Data.LONG_RADAT_DIST=kw['lonsht']
								data.Data.LongRadarTempData.append(kw['lonsht'])
								# print(data.Data.LONG_RADAT_DIST)
								# if float(data.Data.LONG_RADAT_DIST)<100:
								# 	data.Data.TrainMsg['TrainFwd'] = str(data.Data.LONG_RADAT_DIST)
								# data.Data.TrainMsg['TrainRate'] = str(kw['speed'])
							else:
								print('limit out of range')
						else:
							print('size out of range')
					else:
						print('probability out of range')
				else:
					print('speed out of range')
			else:
				print('measurestate out of range')
		else:
			if args[1]!=1:
				# 雷达状态错误
				# print('state:',data.Data.Statelist[3])
				data.Data.LONG_RADAT_DIST = '0'
				if data.Data.Statelist[5]['Status'] == '1' and data.Data.Statelist[7]['Status'] == '1':
					# GPS状态正常，前车距和速度采用GPS数据计算，后车距为invilid
					if data.Data.LOCAL_GPS['Lon'] != 'invalid' and data.Data.LOCAL_GPS['Lat'] != 'invalid' and data.Data.FB_GPS[0]['Lon'] !='invalid' and data.Data.FB_GPS[0]['Lat'] !='invalid':
						data.Data.TrainMsg['TrainFwd'] = haversine(float(data.Data.FB_GPS[0]['Lat'][1:]),float(data.Data.FB_GPS[0]['Lon'][1:]),float(data.Data.LOCAL_GPS['Lat'][1:]),float(data.Data.LOCAL_GPS['Lon'][1:]))
					else:
						data.Data.TrainMsg['TrainFwd'] = 'invalid'
					data.Data.TrainMsg['TrainRate'] = str(data.Data.LOCAL_GPS['Speed'])
				else:
					# GPS状态也不正常,前后车距，当前速度都为invilid
					data.Data.TrainMsg['TrainFwd'] = '0'
					data.Data.TrainMsg['TrainBack'] = '0'
					data.Data.TrainMsg['TrainRate'] = 'invalid'
				# print('TrainMsg:',data.Data.TrainMsg)
	elif args[0]=='LeftRadar' or args[0]=='RightRadar':
		if args[0]=='LeftRadar':
			# 左边的短程雷达处理函数
			data.Data.Statelist[1]={'Device':'1','Status':str(args[1])}
			if kw:
				if kw['measurestate'] != 3:
					#物体状态过滤
					if kw['lonspeed'] <= LEFTSPEED:
						if kw['length']>=LEFTRADARLENGTH[0] and kw['length']<=LEFTRADARLENGTH[1]:
							if kw['width']>=LEFTRADARWIDTH[0] and kw['width']<=LEFTRADARWIDTH[1]:
								if kw['probability']>=LEFTRADARPROBABILITY:
									if kw['latsht']>=LEFTOBSRANGE[0] and kw['latsht']<=LEFTOBSRANGE[1]:
										# print('latsht:',kw['latsht'])
										# 界限过滤
										msg = ['L#'+str(kw['objId']),kw['latsht'],kw['lonsht']]
										data.Data.LRRadarMsgAdd('L',msg)
										# print('pole:',data.Data.LRPoleTempMsg)
									else:
										print('limit out of range')
								else:
									# print('probability:',kw['probability'])
									print('probability out of range')
							else:
								# print('width:',kw['width'])
								print('width out of range')
						else:
							# print('length:',kw['length'])
							print('length out of range')
					else:
						# print('lonspeed:',kw['lonspeed'])
						print('lonspeed out of range')
				else:
					# print('measurestate:',kw['measurestate'])
					print('measurestate out of range')
			else:
				if args[1]!=1:
					# 左雷达状态错误,清空数据数组
					data.Data.LRPoleMsg = []
					data.Data.LRPoleTempMsg = []
		elif args[0]=='RightRadar':
			# 右边的短程雷达数据处理函数
			data.Data.Statelist[2]={'Device':'2','Status':str(args[1])}
			if kw :
				if kw['measurestate'] != 3:
					#物体状态过滤
					if kw['lonspeed'] <= RIGHTSPEED:
						if kw['length']>=RIGHTRADARLENGTH[0] and kw['length']<=RIGHTRADARLENGTH[1]:
							if kw['width']>=RIGHTRADARWIDTH[0] and kw['width']<=RIGHTRADARWIDTH[1]:
								if kw['probability']>=RIGHTRADARPROBABILITY:
									if kw['latsht']>=RIGHTOBSRANGE[0] and kw['latsht']<=RIGHTOBSRANGE[1]:
										# 界限过滤
										msg = ['R#'+str(kw['objId']),kw['latsht'],kw['lonsht']]
										data.Data.LRRadarMsgAdd('R',msg)
										# print('pole:',data.Data.RRPoleTempMsg)
									else:
										print('limit out of range')
								else:
									# print('probability:',kw['probability'])
									print('probability out of range')
							else:
								# print('width:',kw['width'])
								print('width out of range')
						else:
							# print('length:',kw['length'])
							print('length out of range')
					else:
						# print('speed:',kw['speed'])
						print('speed out of range')
				else:
					# print('measurestate:',kw['measurestate'])
					print('measurestate out of range')
			else:
				if args[1]!=1:
					# 右雷达状态错误,清空数据数组
					data.Data.RRPoleMsg = []
					data.Data.RRPoleTempMsg = []

def XOR8(head,tail,s):
	i=0
	for c in s[head:tail]:
		i^=ord(c.encode())
	if hex(int(s[tail+1:],16))==hex(i):
		return 0
	else:
		return hex(i)

def haversine( lat1,lon1, lat2, lon2):
	# 根据经纬度计算距离
	"""
	Calculate the great circle distance between two points 
	on the earth (specified in decimal degrees)
	"""
	# convert decimal degrees to radians
	if not isNumber(lat1) or not isNumber(lon1) or not isNumber(lat2) or not isNumber(lon2):
		return '0'
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

	# haversine formula 
	dlon = lon2 - lon1 
	dlat = lat2 - lat1 
	a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	c = 2 * asin(sqrt(a)) 
	r = 6378.137 # Radius of earth in kilometers. Use 3956 for miles
	return int(c * r * 1000)   #return m

def isNumber(x):
	# 判断x是否为数字类型
	if isinstance(x, int) or isinstance(x, float):
		return True
	else:
		return False

def Get_IP(inner=1,match=None):
	# 获取本车载控制器ip
	if inner==0:
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(('8.8.8.8', 80))
			ip = s.getsockname()[0]
		finally:
			s.close()
			return ip
	else:
		if match==None:
			name=socket.getfqdn(socket.gethostname())
			ip=socket.gethostbyname(name)
			return ip
		else:
			if isinstance(match,str):
				if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',match):
					for i in socket.gethostbyname_ex(socket.gethostname())[2]:
						if i.startswith(re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d{1,3})',match).group(1)):
							ip=i
							return ip   

if __name__=='__main__':
	s='$GPRMC,044549.60,A,3955.7333600,N,11607.6355300,E,13.6,325.1,010616,999,E,A*12\r\n'
	s2='$GPRMC,044549.60,A,3955.7433600,N,11607.6354300,E,13.6,325.1,010616,999,E,A*14'
	s1='$GPGGA,044549.60,3955.7333600,N,11607.6355300,E,1,26,0.50,96.27,M,-7.30,M,0.00,0000*61'
	s3='asdasd'
	s4=b'&100000070c811000000000d1|'
	s5=b'&200010100031311700000021|'
	s6=b'\x0201D+0000002685\r'
	s7=b'\x0301P33\r'
	#print(GPS_PARSING(s1))
	#print(ANGLE_PARSING(s6))
	# print(atan(-1.9)*180/pi)
	# print(100*tan(0.1*pi/180))
	# print(len(s5))
	#print(RARAR_PARSING(s5))
	# a=[31.9294375597,118.7848663330]
	# b=[31.8352875942,118.8064974466]
	# print(haversine(34.2676434736,108.920156846,34.2683182934,108.967080573))
	# print(haversine(a[0],a[1],b[0],b[1]))

	# print(6700*pi/180*acos(sin(a[1])*sin(0)+cos(a[1])*cos(0)*cos(a[0])))
