# -*- coding:utf-8 -*-
import time
import analysis
import threading
from operator import itemgetter

# 两杆间距
POLESSPACE = 50

class Data(object):
	# Data类，记录核心数据

	# 左雷达数据锁
	LeftRDataLock = threading.Lock()
	# 右雷达数据锁
	RightRDataLock = threading.Lock()
	# 长雷达数据锁
	LongRDataLock = threading.Lock()
	# 本车GPS数据锁
	LocalGPSLock = threading.Lock()
	# 前车GPS数据锁
	FontGPSLock = threading.Lock()
	# 后车GPS数据锁
	BackGPSLock = threading.lock()

	LTrainPloeState = 0
	RTrainPloeState = 0

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
		Data.LongRDataLock.acquire()
		Data.LongRadarData = Data.LongRadarTempData
		Data.LongRadarData.sort()
		Data.LongRDataLock.release()
		Data.LongRadarTempData = []

	def assignTrainMsg(self):
		if Data.Statelist[3]['Status'] == '1' and Data.Statelist[5]['Status'] == '1':
			# 长雷达，本车GPS状态都正常
			if Data.Statelist[7]['Status'] == '1':
				# 前车通信正常
				# 根据本车GPS数据和前车GPS数据计算前车距
				Data.LocalGPSLock.acquire()
				Data.FontGPSLock.acquire()
				fontDis = analysis.haversine(float(Data.LOCAL_GPS['Lat'][1:]),float(Data.LOCAL_GPS['Lon'][1:]),float(Data.FB_GPS[0]['Lat'][1:]),float(Data.FB_GPS[0]['Lon'][1:]))
				Data.LocalGPSLock.release()
				Data.FontGPSLock.release()
				aimFlag = False
				# 遍历雷达数据查找和GPS差值最小的数据
				Data.LongRDataLock.acquire()
				for i in Data.LongRadarData:
					if abs(i-fontDis)<2:
						# 找到目标，退出
						TrainMsg['TrainFwd'] = str(round(i,2))
						Data.LastFontDis = round(i,2)
						aimFlag = True
						break
				Data.LongRDataLock.release()
				if not aimFlag:
					# 没有找到目标，采用gps数据
					TrainMsg['TrainFwd'] = str(round(fontDis,2))
					Data.LastFontDis = round(fontDis,2)
			else:
				# 前车通信不正常
				if len(Data.LongRadarData):
					# 有目标
					aimFlag = False
					Data.LongRDataLock.acquire()
					for i in Data.LongRadarData:
						if abs(i-Data.LastFontDis)<0.5:
							# 找到目标，退出
							TrainMsg['TrainFwd'] = str(round(i,2))
							Data.LastFontDis = round(i,2)
							aimFlag = True
							break
					if not aimFlag:
						TrainMsg['TrainFwd'] = str(round(Data.LastFontDis,2))
					Data.LongRDataLock.release()
				else:
					# 没有找到目标，采用上一次的值
					TrainMsg['TrainFwd'] = str(Data.LastFontDis)
			if Data.Statelist[8]['Status'] == '1':
				# 后车通信正常
				Data.LocalGPSLock.acquire()
				Data.BackGPSLock.acquire()
				backDis = analysis.haversine(float(Data.LOCAL_GPS['Lat'][1:]),float(Data.LOCAL_GPS['Lon'][1:]),float(Data.FB_GPS[1]['Lat'][1:]),float(Data.FB_GPS[1]['Lon'][1:]))
				TrainMsg['TrainFwd'] = str(round(backDis,2))
				Data.LocalGPSLock.release()
				Data.BackGPSLock.release()
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
				Data.LocalGPSLock.acquire()
				Data.FontGPSLock.acquire()
				fontDis = analysis.haversine(float(Data.LOCAL_GPS['Lat'][1:]),float(Data.LOCAL_GPS['Lon'][1:]),float(Data.FB_GPS[0]['Lat'][1:]),float(Data.FB_GPS[0]['Lon'][1:]))
				Data.LocalGPSLock.release()
				Data.FontGPSLock.release()
				TrainMsg['TrainFwd'] = str(round(fontDis,2))
				Data.LastFontDis = round(fontDis,2)
			else:
				# 前车通信不正常
				TrainMsg['TrainFwd'] = '0'
				Data.LastFontDis = 0
			if Data.Statelist[8]['Status'] == '1':
				# 后车通信正常
				Data.LocalGPSLock.acquire()
				Data.BackGPSLock.acquire()
				backDis = analysis.haversine(float(Data.LOCAL_GPS['Lat'][1:]),float(Data.LOCAL_GPS['Lon'][1:]),float(Data.FB_GPS[1]['Lat'][1:]),float(Data.FB_GPS[1]['Lon'][1:]))
				Data.LocalGPSLock.release()
				Data.BackGPSLock.release()
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
				# 加锁
				aimFlag = False
				Data.LongRDataLock.acquire()
				for i in Data.LongRadarData:
					if abs(i-Data.LastFontDis)<0.5:
						# 找到目标，退出
						TrainMsg['TrainFwd'] = str(round(i,2))
						Data.LastFontDis = round(i,2)
						aimFlag = True
						break
				if not aimFlag:
					TrainMsg['TrainFwd'] = str(round(Data.LastFontDis,2))
				Data.LongRDataLock.release()
			else:
				# 没有找到目标，采用上一次的值
				TrainMsg['TrainFwd'] = str(Data.LastFontDis)
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
		elif radar == 'R':
			Data.RRPoleMsg = Data.RRPoleTempMsg
			Data.RRPoleTempMsg = []

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
		# 角度判断：>5°，机械臂在左边，-5°~5°，机械臂在中间，<-5°机械臂在右边
		if Data.AngleMsg['AngleData'] == 'invalid' or -5<float(Data.AngleMsg['AngleData'])<5:
			# 机械臂在中间，分别选取左右两边最近的杆子信息
			if self.LNearRealAim():
				pass
			else:
				pass
			if self.RNearRealAim():
				pass
			else:
				pass
		elif float(Data.AngleMsg['AngleData'])<-5:
			# 机械臂在右边，选取右边最近的杆子信息
			if self.RNearRealAim():
				pass
			else:
				pass
		elif float(Data.AngleMsg['AngleData'])>5:
			# 机械臂在左边，选取左边最近的杆子信息
			if self.RNearRealAim():
				pass
			else:
				pass

	def LNearRealAim(self):
		pass

	def RNearRealAim(self):
		pass
