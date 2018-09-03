# -*- coding:utf-8 -*-
import time
import analysis
import threading
from operator import itemgetter

# 过滤范围
# XTHRESHOLD = [-1,1]
XTHRESHOLD = [-10,10]
YTHRESHOLD = [-1,1]
LRXRANGE = [0,2]
RLXRANGE = [0,-2]
YDISPARITY = 0.5
GPSCONTRAST = 1
CARLENGTH = 0
# 两杆间距
POLESSPACE = 50

class Data(object):
	# Data类，记录核心数据

	# 左雷达数据锁
	# LRDataLock = threading.Lock()
	# 右雷达数据锁
	# RRDataLock = threading.Lock()

	"""docstring for Data"""
	dictionary = {'GPS':{},
				'GPS_FONT':{},
				'GPS_BEHIND':{},
				'Angle':{},
				'Radar_L':{},
				'Radar_R':{},
				'LongRadar':{},
				'Timer':{}
				}
	# 配置数据，前后车id，ip
	ini={
		"TODIP":"0.0.0.0",
		"dlx":0,
		"dly":0,
		"drx":0,
		"dry":0,
		"dlongy":0,
		"localID":"0000",
		"localIP":"127.0.0.1",
		"fwdTrainID":"0000",
		"fwdTrainIP":"192.168.255.255",
		"backTrainID":"0000",
		"backTrainIP":"192.168.255.255"
	}

	# 前后车GPS数据
	FB_GPS=[{'Lat':'invalid','Lon':'invalid','Speed':'invalid','Dir':'invalid','distance_font':'invalid','ID':ini['fwdTrainID'],'IP':str(ini['fwdTrainIP'])},
			{'Lat':'invalid','Lon':'invalid','Speed':'invalid','Dir':'invalid','distance_font':'invalid','ID':ini['backTrainID'],'IP':str(ini['backTrainIP'])}] #lat long speed dir dist_f 前车 后车
	
	LastFontDis = 0
	raw_data=[]
	raw_state=0
	dictionary_state=0
	ini_state=0
	# 本车GPS数据
	LOCAL_GPS={'Lon':'invalid','Lat':'invalid','Speed':'invalid','Dir':'invalid','distance_font':'invalid','ID':ini['localID'],'LocalIp':str(ini['localIP'])}
	LONG_RADAT_DIST='0'
	TrainMsg={'TrainFwd':'0','TrainBack':'0','TrainRate':'invalid'}
	PoleMsg=[]
	LRPoleMsg=[]
	LRPoleTempMsg=[]
	RRPoleMsg=[]
	RRPoleTempMsg=[]
	LongRadarTempData = []
	LongRadarData = []
	AngleMsg={'AngleData':'invalid'}

	# 前次机械臂方向
	# LastDirect = 'M'
	# 当前机械臂方向
	# CurDirect = 'M'
	# 前次最近线杆距离
	LastPoleDis = None
	# 当前最近线杆距离
	# curPoleDis = 0

	# 设备状态列表
	#lefradar rightradar longradar angle gps ap fwd back
	Statelist=[{},{'Device':'1','Status':'2'},{'Device':'2','Status':'2'},{'Device':'3','Status':'2'},
				{'Device':'4','Status':'2'},{'Device':'5','Status':'2'},{'Device':'6','Status':'2'},
				{'Device':'7','Status':'2'},{'Device':'8','Status':'2'}]
	# 向tod发送数据报文
	SEND_MSG={}
	# 向tod发送状态报文
	SEND_STA={}
	STORE_SEND=[]
	SEND_STATE=0
	STORE_RAW=[]
	RAW_STATE=0
	FBL_TIMEOUT={'F':0,'L':0,'B':0}#前车，后车

	def SetSendlist(self):
		# print('SetSendlist:',Data.TrainMsg['TrainFwd'])
		# 设置发送数据函数
		Data.SEND_MSG={}
		Data.SEND_STA={}
		statelist=[]
		for i in Data.Statelist:
			if i:
				statelist.append(i)
		self.assignTrainMsg()
		self.assignPloeMsg()
		# 数据信息
		Data.SEND_MSG={"MsgCode":"204","Time":time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time())),
				"TrainMsg":Data.TrainMsg,
				"PoleMsg":Data.PoleMsg,
				"AngleMsg":Data.AngleMsg
				}
		# print('PoleMsg:',Data.SEND_MSG['PoleMsg'])
		Data.PoleMsg=[]
		# 状态信息
		Data.SEND_STA={"MsgCode":"203","Time":time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time())),
					"MsgBody":statelist}
		Data.STORE_SEND.append(Data.SEND_MSG)
		Data.STORE_SEND.append(Data.SEND_STA)
		Data.SEND_STATE=1

	def set_dict(self,d,raw='invalid'):
		if(raw):
			if d.values():
				Data.raw_data.append(raw+'\n')
				Data.raw_state=1
		if isinstance(d,dict):
			Data.dictionary.update(d)
			Data.dictionary_state=1

	def get_dict(self):
		return Data.dictionary
	def dict_state_clr(self):
		Data.dictionary_state=0
	def get_dict_state(self):
		return Data.dictionary_state

	def get_ini(self):
		return Data.ini
	def set_ini(self,d):
		if isinstance(d,dict):
			Data.ini.update(d)
			Data.ini_state=1
	def get_ini_state(self):
		return Data.ini_state
	def set_ini_state(self,state):
		Data.ini_state = state
	def ini_state_clr(self):
		Data.ini_state=0
	def set_raw(self,s):
		# 传感器数据添加至日志缓冲区
		if(s[-1]=='\n'):
			Data.STORE_RAW.append(time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time()))+'  '+s)
			# pass
		else:
			Data.STORE_RAW.append(time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time()))+'  '+s+'\n')
			# pass
		Data.RAW_STATE=1
	def get_raw(self):
		raw=Data.STORE_RAW
		Data.STORE_RAW=[]
		Data.RAW_STATE=0
		return raw
	def get_send(self):
		send=Data.STORE_SEND
		Data.STORE_SEND=[]
		Data.SEND_STATE=0
		return send

	def LongRadarMsgCycle():
		Data.LongRadarData = Data.LongRadarTempData
		Data.LongRadarTempData = []
		Data.LongRadarData.sort()

	def assignTrainMsg(self):
		if Data.Statelist[3]['Status'] == '1' and Data.Statelist[5]['Status'] == '1':
			# 长雷达，本车GPS状态都正常
			if Data.Statelist[7]['Status'] == '1':
				# 前车通信正常
				# 根据本车GPS数据和前车GPS数据计算前车距
				fontDis = analysis.haversine(float(Data.LOCAL_GPS['Lat'][1:]),float(Data.LOCAL_GPS['Lon'][1:]),float(Data.FB_GPS[0]['Lat'][1:]),float(Data.FB_GPS[0]['Lon'][1:]))
				aimFlag = False
				# 遍历雷达数据查找和GPS差值最小的数据
				for i in Data.LongRadarData:
					if abs(i-fontDis)<0.5:
						# 找到目标，退出
						TrainMsg['TrainFwd'] = str(round(i,2))
						LastFontDis = round(i,2)
						aimFlag = True
						break
				if not aimFlag:
					# 没有找到目标，采用上一次的值
					TrainMsg['TrainFwd'] = str(LastFontDis)
			else:
				# 前车通信不正常
				if len(Data.LongRadarData):
					# 有目标
					TrainMsg['TrainFwd'] = str(round(Data.LongRadarData[0],2))
					LastFontDis = round(Data.LongRadarData[0],2)
				else:
					# 没有找到目标，采用上一次的值
					TrainMsg['TrainFwd'] = str(LastFontDis)
			if Data.Statelist[8]['Status'] == '1':
				# 后车通信正常
				backDis = analysis.haversine(float(Data.LOCAL_GPS['Lat'][1:]),float(Data.LOCAL_GPS['Lon'][1:]),float(Data.FB_GPS[1]['Lat'][1:]),float(Data.FB_GPS[1]['Lon'][1:]))
				TrainMsg['TrainFwd'] = str(round(backDis,2))
			else:
				# 后车通信不正常
				TrainMsg['TrainFwd'] = '0'
				pass
			pass
		if Data.Statelist[5]['Status'] == '1' and  Data.Statelist[3]['Status'] != '1':
			# GPS状态正常，长雷达状态不正常
			# 根据GPS计算前后车距
			if Data.Statelist[7]['Status'] == '1':
				# 前车通信正常
				fontDis = analysis.haversine(float(Data.LOCAL_GPS['Lat'][1:]),float(Data.LOCAL_GPS['Lon'][1:]),float(Data.FB_GPS[0]['Lat'][1:]),float(Data.FB_GPS[0]['Lon'][1:]))
				TrainMsg['TrainFwd'] = str(round(fontDis,2))
				LastFontDis = round(fontDis,2)
			else:
				# 前车通信不正常
				TrainMsg['TrainFwd'] = '0'
				LastFontDis = 0
			if Data.Statelist[8]['Status'] == '1':
				# 后车通信正常
				backDis = analysis.haversine(float(Data.LOCAL_GPS['Lat'][1:]),float(Data.LOCAL_GPS['Lon'][1:]),float(Data.FB_GPS[1]['Lat'][1:]),float(Data.FB_GPS[1]['Lon'][1:]))
				TrainMsg['TrainBack'] = str(round(backDis,2))
			else:
				# 后车通信不正常
				TrainMsg['TrainBack'] = '0'
		if Data.Statelist[3]['Status'] == '1' and Data.Statelist[5]['Status'] != '1':
			# 长雷达状态正常，GPS状态不正常
			# 查找距离最近的数据
			# 前车通信不正常
			if len(Data.LongRadarData):
				# 有目标
				TrainMsg['TrainFwd'] = str(round(Data.LongRadarData[0],2))
				LastFontDis = round(Data.LongRadarData[0],2)
			else:
				# 没有找到目标，采用上一次的值
				TrainMsg['TrainFwd'] = str(LastFontDis)
			# 后车距为0
			TrainMsg['TrainBack'] = '0'
			TrainMsg['TrainRate'] = 'invalid'
		if Data.Statelist[3]['Status'] ！= '1' and Data.Statelist[5]['Status'] != '1':
			# 长雷达状态正常，GPS状态不正常
			TrainMsg={'TrainFwd':'0','TrainBack':'0','TrainRate':'invalid'}

	def LRRadarMsgCycle(radar):
		if radar == 'L':
			Data.LRPoleMsg = Data.LRPoleTempMsg
			Data.LRPoleTempMsg = []
			# print('msg:',Data.LRPoleMsg)
			# print('tempmsg:',Data.LRPoleTempMsg)
		elif radar == 'R':
			Data.RRPoleMsg = Data.RRPoleTempMsg
			Data.RRPoleTempMsg = []
			# print('msg:',Data.RRPoleMsg)
			# print('tempmsg:',Data.RRPoleTempMsg)

	def LRRadarMsgAdd(radar,msg):
		repeat = 0
		# 获取左雷达数据锁
		# data.Data.LRDataLock.acquire()
		if radar == 'L':
			for i in Data.LRPoleTempMsg:
				if i[0] == msg[0]:
					# 重复的物体，更新数据
					i[1] = msg[1]
					i[2] = msg[2]
					repeat = 1
					break
			if repeat == 0:
				# 不重复目标，直接插入
				Data.LRPoleTempMsg.append(msg)
			# print('LRPoleTempMsg:',Data.LRPoleTempMsg)
			# 按照纵向位移排序
			# data.Data.LRPoleMsg.sort(key=itemgetter(2))

			# 释放左雷达数据锁
			# data.Data.LRDataLock.release()
		elif radar == 'R':
			for i in Data.RRPoleTempMsg:
				if i[0] == msg[0]:
					# 重复的物体，更新数据
					i[1] = msg[1]
					i[2] = msg[2]
					repeat = 1
					break
			if repeat == 0:
				# 不重复目标，直接插入
				Data.RRPoleTempMsg.append(msg)
			# print('RRPoleTempMsg:',Data.RRPoleTempMsg)
		
	def assignPloeMsg(self):
		# 判断角度
		if Data.AngleMsg['AngleData'] == 'invalid' or -5<=float(Data.AngleMsg['AngleData'])<=5:
			# 查找左边最近的非虚假目标
			LNearestAim = self.LNearRealAim()
			# 查找右边最近的非虚假目标
			RNearestAim = self.RNearRealAim()
			# 角度值不存在或角度值在-5°~5°之间，认为机械臂处在中间位置，此时选取左右两边最近的物体
			if not LNearestAim and not RNearestAim:
				# 左右两边都没有探测到目标
				Data.LastPoleDis = None
				# LastDirect = 'M'
				Data.PoleMsg = []
			elif LNearestAim and not RNearestAim:
				# 左边探测到目标，右边没有探测到目标
				Data.LastPoleDis = round(LNearestAim[2],2)
				# LastDirect = 'L'
				Data.PoleMsg.append({'ID':LNearestAim[0],'PoleX':('%.2f'%(LNearestAim[1])),'PoleY':('%.2f'%(LNearestAim[2]))})
			elif not LNearestAim and RNearestAim:
				# 右边探测到目标，左边没有探测到目标
				Data.LastPoleDis = round(RNearestAim[2],2)
				# LastDirect = 'R'
				Data.PoleMsg.append({'ID':RNearestAim[0],'PoleX':('%.2f'%(RNearestAim[1])),'PoleY':('%.2f'%(RNearestAim[2]))})
			elif LNearestAim and RNearestAim:
				# 左右两边都探测到目标
				if LNearestAim[2]<=RNearestAim[2]:
					Data.LastPoleDis = round(LNearestAim[2],2)
					# LastDirect = 'L'
					Data.PoleMsg.append({'ID':LNearestAim[0],'PoleX':('%.2f'%(LNearestAim[1])),'PoleY':('%.2f'%(LNearestAim[2]))})
				else:
					Data.LastPoleDis = round(RNearestAim[2],2)
					# LastDirect = 'R'
					Data.PoleMsg.append({'ID':RNearestAim[0],'PoleX':('%.2f'%(RNearestAim[1])),'PoleY':('%.2f'%(RNearestAim[2]))})
		else:
			if float(Data.AngleMsg['AngleData'])>=0:
				# 左边
				# 查找左边最近的非虚假目标
				LNearestAim = self.LNearRealAim()
				if LNearestAim:
					Data.LastPoleDis = round(LNearestAim[2],2)
					# LastDirect = 'L'
					Data.PoleMsg.append({'ID':LNearestAim[0],'PoleX':('%.2f'%(LNearestAim[1])),'PoleY':('%.2f'%(LNearestAim[2]))})
				else:
					Data.LastPoleDis = None
					# LastDirect = 'M'
					Data.PoleMsg = []
			else:
				# 右边
				# 查找右边最近的非虚假目标
				RNearestAim = self.RNearRealAim()
				if RNearestAim:
					Data.LastPoleDis = round(RNearestAim[2],2)
					# LastDirect = 'R'
					Data.PoleMsg.append({'ID':RNearestAim[0],'PoleX':('%.2f'%(RNearestAim[1])),'PoleY':('%.2f'%(RNearestAim[2]))})
				else:
					Data.LastPoleDis = None
					# LastDirect = 'M'
					Data.PoleMsg = []

	def LNearRealAim(self):
		LTempAims = Data.LRPoleMsg
		RTempAims = Data.RRPoleMsg
		# 对tempAims按照纵向位移从小到大的顺序排序
		LTempAims.sort(key=itemgetter(2))
		# 过滤左雷达数据中侧向偏移在[-1,1]之外的数据
		aims = [d for d in LTempAims if XTHRESHOLD[0]<=d[1]<=XTHRESHOLD[1] ]
		if not len(aims):
			return None
		for aim in aims:
			vflag = False
			if Data.LastPoleDis!=None:
				if (aim[2] -Data.LastPoleDis) > 5 and aim[2] < POLESSPACE:
					# 和上一次最近的距离比较，如果此次最近的距离比上次大，且大于5m，表示上次最近的线杆消失来了新的线杆，如果距离<50m，则过滤掉;
					continue
				if (Data.LastPoleDis - aim[2]) > 4:
					# 如果此次距离比上次突然小很多，则也表示为电线，过滤掉
					continue
			# 遍历右雷达数据，和左雷达数据进行比对
			for o in RTempAims:
				if abs(o[2]-aim[2])<=YDISPARITY:
					if LRXRANGE[0]<=o[1]<=LRXRANGE[1]:
						vflag = True
						break
			if not vflag:
				return aim
		return None

	def RNearRealAim(self):
		LTempAims = Data.LRPoleMsg
		RTempAims = Data.RRPoleMsg
		# 对tempAims按照纵向位移从小到大的顺序排序
		RTempAims.sort(key=itemgetter(2))
		# 过滤左雷达数据中侧向偏移在[-1,1]之外的数据
		aims = [d for d in RTempAims if XTHRESHOLD[0]<=d[1]<=XTHRESHOLD[1] ]
		if not len(aims):
			return None
		for aim in aims:
			vflag = False
			if Data.LastPoleDis!=None:
				if (aim[2] - Data.LastPoleDis) > 5 and aim[2] < POLESSPACE:
					# 和上一次最近的距离比较，如果此次最近的距离比上次大，且大于5m，表示上次最近的线杆消失来了新的线杆，如果距离<50m，则过滤掉;
					continue
				if (Data.LastPoleDis - aim[2]) > 4:
					# 如果此次距离比上次突然小很多，则也表示为电线，过滤掉
					continue
			for o in LTempAims:
				# 遍历右雷达数据，和左雷达数据进行比对
				if abs(o[2]-aim[2])<=YDISPARITY:
					if RLXRANGE[0]<=o[1]<=RLXRANGE[1]:
						vflag = True
						break
			if not vflag:
				return aim
		return None

