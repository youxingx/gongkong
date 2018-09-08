# -*- coding:utf-8 -*-
import socket 
import threading
import time
import asyncio
import re
import json
import data
import analysis
import datetime
import random

class Server_UDP(data.Data):
	"""docstring for Ser"""
	# udp类
	def __init__(self, host='0.0.0.0',gps_port=4006,port=4004,uip='127.0.0.1',debug=None,match=None):
		# udp对象初始化
		self.host = host
		self.port=port
		self.upper_ip=uip
		self.gps_port=gps_port
		self.debug=debug
		self.font_ip=self.ini['fwdTrainIP']
		self.behind_ip=self.ini['backTrainIP']
		self.ip='0.0.0.0'
		# self.fbinfostate = False
		if match==None:
			self.match=uip
		else:
			self.match=match
		super().set_ini({'UDP_GPS_PORT':self.gps_port})
		super().set_ini({'UDP_USER_PORT':self.port})
		super().set_ini({'UDP_USER_IP':self.upper_ip})
		print(analysis.Get_IP(match=self.match))
		super().set_ini({'TCP_IP':analysis.Get_IP(match=self.match)})
		super().get_dict()['GPS'].update({'IP':super().get_ini()['TCP_IP']})

		# 开启向前后车发送GPS数据的线程
		threading.Thread(target=self.Send_GPS,args=(self.gps_port,)).start()
		print('UDP Start FB GPS at PORT:%d'%self.gps_port)
		# 开启接收前后车GPS数据的线程
		threading.Thread(target=self.Get_GPS,args=(self.gps_port,)).start()
		print('UDP Start Collect GPS From PORT:%d'%self.gps_port)
		# 开启和TOD之间的udp通信线程
		threading.Thread(target=self.Send_upper,args=(self.upper_ip,self.port)).start()
		print('UDP Start Send MESSAGE to %s:%d'%(self.upper_ip,self.port))
		# 开启定时线程,监测能否收到前后车的数据
		threading.Thread(target=self.Timer,).start()
		print('UDP Start FB MESSAGE to %s:%d'%(self.upper_ip,self.gps_port))
		# if debug==1:
		#     threading.Thread(target=self.UDP_back_msg,args=(self.host,self.port)).start()
		#     print('UDP Start Listen at %s PORT:%d'%(self.host,self.gps_port))

	def Send_upper(self,ip,port):
		# 向TOD发送设备状态和数据线程函数
		sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		while True:
			self.SetSendlist() #设置发送数据
			# print('senddata:',str(json.dumps(data.Data.SEND_MSG)))
			if self.debug:
				# 如果是调试模式，发送给自己的主机一次，方便查看发送数据是否正确
				sock.sendto(str(json.dumps(data.Data.SEND_STA)).encode(),('127.0.0.1',port))
			# 发送状态报文
			try:
				sock.sendto(str(json.dumps(data.Data.SEND_STA)).encode(),(ip,port))
			except Exception as e:
				print('send status to tod error')
			time.sleep(0.1)
			# time.sleep(1)
			if self.debug:
				# 如果是调试模式，发送给自己的主机一次，方便查看发送数据是否正确
				sock.sendto(str(json.dumps(data.Data.SEND_MSG)).encode(),('127.0.0.1',port))
			# 发送数据报文
			try:
				sock.sendto(str(json.dumps(data.Data.SEND_MSG)).encode(),(ip,port))
			except Exception as e:
				print('send msg to tod error')
			time.sleep(0.1)
			# time.sleep(3)

	def Get_GPS(self,port):
		sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(('0.0.0.0',port))
		while True:
			tempdata,addr=sock.recvfrom(10000)
			# 数据添加到日志
			try:
				self.set_raw(tempdata.decode())
				# print('recv data:',tempdata.decode())
				# if data and addr[0]!=analysis.Get_IP(match=self.match) and addr[0]!=self.ip:
				if addr[0]!=analysis.Get_IP(match=self.match):
					analysis.AP('GET',1,addr,data=json.loads(tempdata.decode()))
				if addr[0]==self.font_ip:
					data.Data.FBL_TIMEOUT['F']=5
					# analysis.AP('GET',1,addr,data=json.loads(tempdata.decode()))
					# analysis.AP('F',1,data=json.loads(tempdata.decode()))
				if addr[0]==self.behind_ip:
					data.Data.FBL_TIMEOUT['B']=5
					# analysis.AP('GET',1,addr,data=json.loads(tempdata.decode()))
					# analysis.AP('B',1,data=json.loads(tempdata.decode()))
				data.Data.Statelist[6]['Status'] = '1'
				time.sleep(0.1)
			except Exception as e:
				print(e)

	def Send_GPS(self,port):
		sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		while True:
			# 发给前车
			try:
				sock.sendto(str(json.dumps(data.Data.LOCAL_GPS)).encode(),(self.ini['fwdTrainIP'],port))
			except Exception as e:
				print('send gps to fwd error')
			time.sleep(0.01)
			try:
				# 发给后车
				sock.sendto(str(json.dumps(data.Data.LOCAL_GPS)).encode(),(self.ini['backTrainIP'],port))
			except Exception as e:
				print('send gps to back error')
			time.sleep(1)

	def UDP_back_msg(self,host='0.0.0.0',port=4002):       
		client=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client.bind((host,port))
		while True:
			try:
				data,addr=client.recvfrom(10000)
				if data:
					print('GET:',data.decode())
					client.sendto('UDP GET'.encode(),addr)
			except Exception as e:
				print(e)
			time.sleep(0.1)

	def Timer(self):
		# 定时器线程,用于监测前后车通讯状态，若5s钟之内没有收到前后车udp报文，则认为前后车通讯故障
		while True:
			for i in data.Data.FBL_TIMEOUT.keys():
				data.Data.FBL_TIMEOUT[i]-=1
				if data.Data.FBL_TIMEOUT[i]<=0:
					analysis.AP(i,2)
			time.sleep(1)


def virturalData1(fdistance,pdistance):
	# 虚拟数据
	disStand = 20
	statelist=[{'Device':'1','Status':'2'},{'Device':'2','Status':'1'},{'Device':'3','Status':'1'},
				{'Device':'4','Status':'1'},{'Device':'5','Status':'1'},{'Device':'6','Status':'1'},
				{'Device':'7','Status':'1'},{'Device':'8','Status':'1'}]
	data.Data.SEND_STA={"MsgCode":"203","Time":time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time())),
					"MsgBody":statelist}
	distance_F = fdistance
	distance_B = 100
	TrainRate = 80
	data.Data.TrainMsg={
							'TrainFwd':str(distance_F),
							'TrainBack':str(distance_B),
							'TrainRate':str(TrainRate)
						}
	data.Data.PoleMsg = [
							{'ID':1,'PoleX':'5.00','PoleY':('%.2f'%pdistance)},{'ID':2,'PoleX':'5.00','PoleY':'8.20'},
							{'ID':3,'PoleX':'5.00','PoleY':'9.00'},{'ID':4,'PoleX':'-5.00','PoleY':'8.40'},
							{'ID':5,'PoleX':'-5.00','PoleY':'8.60'},{'ID':6,'PoleX':'-5.00','PoleY':'8.80'}
						]
	data.Data.AngleMsg = {'AngleData':'80'}
	data.Data.SEND_MSG = {"MsgCode":"204","Time":time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time())),
				"TrainMsg":data.Data.TrainMsg,
				"PoleMsg":data.Data.PoleMsg,
				"AngleMsg":data.Data.AngleMsg
				}

def virturalData2():
	# 虚拟数据
	disStand = 20
	statelist=[{'Device':'1','Status':'2'},{'Device':'2','Status':'1'},{'Device':'3','Status':'1'},
				{'Device':'4','Status':'1'},{'Device':'5','Status':'1'},{'Device':'6','Status':'1'},
				{'Device':'7','Status':'1'},{'Device':'8','Status':'1'}]
	data.Data.SEND_STA={"MsgCode":"203","Time":time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time())),
					"MsgBody":statelist}
	distance_F = 60
	distance_B = 60
	TrainRate = 80
	data.Data.TrainMsg={
							'TrainFwd':str(distance_F),
							'TrainBack':str(distance_B),
							'TrainRate':str(TrainRate)
						}
	data.Data.PoleMsg = [
							{'ID':1,'PoleX':'5.00','PoleY':'3.00'},{'ID':2,'PoleX':'5.00','PoleY':'4.00'},
							{'ID':3,'PoleX':'5.00','PoleY':'9.00'},{'ID':4,'PoleX':'-5.00','PoleY':'6.00'},
							{'ID':5,'PoleX':'-5.00','PoleY':'7.00'},{'ID':6,'PoleX':'-5.00','PoleY':'8.00'}
						]
	data.Data.AngleMsg = {'AngleData':'80'}
	data.Data.SEND_MSG = {"MsgCode":"204","Time":time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time())),
				"TrainMsg":data.Data.TrainMsg,
				"PoleMsg":data.Data.PoleMsg,
				"AngleMsg":data.Data.AngleMsg
				}


class Server_TCP(data.Data):
	# TCP类
	def __init__(self,host='0.0.0.0',port=4000,listen_num=500,debug=None):
		# TCP初始化函数
		self.host=host
		self.port=port
		self.listen_num=listen_num
		self.__loop=asyncio.new_event_loop()
		#self.__cnt=dict()
		#self.timer=5
		self.__funcs=dict()
		self.debug=debug
		threading.Thread(target=self.asyncio_loop,args=(self.__loop,)).start()
		asyncio.run_coroutine_threadsafe(self.Start(),self.__loop)
	def debug(self,*args):
		print({"test":args})
		return {"test":args}
	def Get_online_num(self):
		return len(len(self.__cnt))
	def Resigter_func(self,func):
		self.__funcs[str(func)]=func
	def Relieve_func(self,func):
		if func in self.__funcs.values():
			self.__funcs.pop(str(func))
	def Tcp_msg(self,*args,**kw):
		result={}
		for func in kw.values():
			r=func(args[0])
			if isinstance(r,dict):
				result.update(r)
			if self.debug==1:
				print(result)
		return str(json.dumps(result)).encode()
	def asyncio_loop(self,loop):
		asyncio.set_event_loop(loop)
		loop.run_forever()
	async def Timer(self):
		while True:
			print('tcp Timer')
			b=list()
			if(len(self.__cnt)>0):
				for i in self.__cnt.keys():
					self.__cnt[i][1]-=1
					if(self.__cnt[i][1]<0):
						b.append(i)
			if(len(b)>0):
				for i in b:
					self.__cnt.pop(i)
			for i in data.Data.FBL_TIMEOUT.keys():
				data.Data.FBL_TIMEOUT[i]-=1
				if data.Data.FBL_TIMEOUT[i]<=0:
					analysis.AP(i,2)
			await asyncio.sleep(1)
	async def Start(self):
		# TCP初始化线程，绑定ip和端口号
		server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		server.bind((self.host,self.port))
		server.setblocking(0)
		server.listen(self.listen_num)
		#asyncio.run_coroutine_threadsafe(self.Timer(),self.__loop)
		print('TCP Start listen at %s:%s'%(self.host,self.port))
		while True:
			sock,addr=await self.__loop.sock_accept(server)
			self.fbinfostate = False
			#self.__cnt[addr]=[sock,self.timer]
			asyncio.run_coroutine_threadsafe(self.tcp_w(sock,addr),self.__loop)
			asyncio.run_coroutine_threadsafe(self.tcp_r(sock,addr),self.__loop)
	async def tcp_r(self,sock,addr):
			# TCP接收处理线程
			while True:
				recvdata = await self.__loop.sock_recv(sock,10000)
				if not recvdata:
					# 连接断开
					break
				if(recvdata != b''):
					try:
						dataFormat = json.loads(recvdata.decode())
						print(dataFormat)
						#self.__cnt[addr][1]=self.timer
						if dataFormat['MsgCode'] == '301':
							# 查询id，ip后，TOD回复报文
							if 'MethodBody' in dataFormat.keys():
								if 'Result' in dataFormat['MethodBody'].keys() and dataFormat['MethodBody']['Result']=='1':
									if 'LocalID' in dataFormat['MethodBody'].keys():
										self.ini['localID'] = dataFormat['MethodBody']['LocalID']
										data.Data.LOCAL_GPS['ID'] = data.Data.ini['localID']
										# data.Data.LOCAL_ID = data.Data.ini['localID']
									if 'LocalIP' in dataFormat['MethodBody'].keys():
										self.ini['localIP'] = dataFormat['MethodBody']['LocalIP']
										data.Data.LOCAL_GPS['LocalIp'] = data.Data.ini['localIP']
									if 'FwdTrainID' in dataFormat['MethodBody'].keys():
										self.ini['fwdTrainID'] = dataFormat['MethodBody']['FwdTrainID']
										data.Data.FB_GPS[0]['ID'] = data.Data.ini['fwdTrainID']
									if 'FwdIP' in dataFormat['MethodBody'].keys():
										self.ini['fwdTrainIP'] = dataFormat['MethodBody']['FwdIP']
										data.Data.FB_GPS[0]['IP'] = data.Data.ini['fwdTrainIP']
									if 'BackTrainID' in dataFormat['MethodBody'].keys():
										self.ini['backTrainID'] = dataFormat['MethodBody']['BackTrainID']
										data.Data.FB_GPS[1]['ID'] = data.Data.ini['backTrainID']
									if 'BackIP' in dataFormat['MethodBody'].keys():
										self.ini['backTrainIP'] = dataFormat['MethodBody']['BackIP']
										data.Data.FB_GPS[0]['IP'] = data.Data.ini['backTrainIP']
									self.fbinfostate = True
									super().set_ini_state(1)
						elif dataFormat['MsgCode'] == '302':
							# 配置前后车id，ip报文
							replydata = dict()
							MethodBody = dict()
							MethodBody['Result'] = '1'
							MethodBody['Reason'] = ''
							if 'MethodBody' in dataFormat.keys():
								if 'LocalID' in dataFormat['MethodBody'].keys():
									self.ini['localID'] = dataFormat['MethodBody']['LocalID']
									data.Data.LOCAL_GPS['ID'] = data.Data.ini['localID']
									# data.Data.LOCAL_ID = data.Data.ini['localID']
								else:
									MethodBody['Result'] = '2'
									MethodBody['Reason'] = 'Msg error! LocalID loss'
								if 'LocalIP' in dataFormat['MethodBody'].keys():
									self.ini['localIP'] = dataFormat['MethodBody']['LocalIP']
									data.Data.LOCAL_GPS['LocalIp'] = data.Data.ini['localIP']
								else:
									MethodBody['Result'] = '2'
									MethodBody['Reason'] = 'Msg error! LocalIP loss'
								if 'FwdTrainID' in dataFormat['MethodBody'].keys():
									self.ini['fwdTrainID'] = dataFormat['MethodBody']['FwdTrainID']
									data.Data.FB_GPS[0]['ID'] = data.Data.ini['fwdTrainID']
								else:
									MethodBody['Result'] = '2'
									MethodBody['Reason'] = 'Msg error! FwdTrainID loss'
								if 'FwdIP' in dataFormat['MethodBody'].keys():
									self.ini['fwdTrainIP'] = dataFormat['MethodBody']['FwdIP']
									data.Data.FB_GPS[0]['IP'] = data.Data.ini['fwdTrainIP']
								else:
									MethodBody['Result'] = '2'
									MethodBody['Reason'] = 'Msg error! FwdIP loss'
								if 'BackTrainID' in dataFormat['MethodBody'].keys():
									self.ini['backTrainID'] = dataFormat['MethodBody']['BackTrainID']
									data.Data.FB_GPS[1]['ID'] = data.Data.ini['backTrainID']
								else:
									MethodBody['Result'] = '2'
									MethodBody['Reason'] = 'Msg error! BackTrainID loss'
								if 'BackIP' in dataFormat['MethodBody'].keys():
									self.ini['backTrainIP'] = dataFormat['MethodBody']['BackIP']
									data.Data.FB_GPS[0]['IP'] = data.Data.ini['backTrainIP']
								else:
									MethodBody['Result'] = '2'
									MethodBody['Reason'] = 'Msg error! BackIP loss'
							else:
								MethodBody['Result'] = '2'
								MethodBody['Reason'] = 'Msg error! MethodBody loss'
							if MethodBody['Result'] == '1':
								super().set_ini_state(1)
								MethodBody['TrainID'] = self.ini['localID']
							nowtime = datetime.datetime.now()
							replydata['Time'] = nowtime.strftime('%Y/%m/%d %H:%M:%S')
							replydata['MsgCode'] = '202'
							replydata['MethodBody'] = MethodBody
							try:
								sock.send(json.dumps(replydata).encode())
							except Exception as e:
								sock.close()
								print('连接突然断开',e)
								break
					except Exception as e:
						# print('what the fuck:',e)
						pass
			return 0
			
	async def tcp_w(self,sock,addr):
			# TCP发送报文
			print('fbinfostate:',self.fbinfostate)
			while not self.fbinfostate:
				querydata = dict()
				nowtime = datetime.datetime.now()
				MethodBody = dict()
				querydata['Time'] = nowtime.strftime('%Y/%m/%d %H:%M:%S')
				querydata['MsgCode'] = '201'
				MethodBody['TrainID'] = data.Data.ini['localID']
				querydata['MethodBody'] = MethodBody
				try:
					sock.send(json.dumps(querydata).encode())
				except Exception as e:
					sock.close()
					print('连接突然断开',e)
					break
				await asyncio.sleep(1)
			return 0

if __name__ == '__main__':
	
	server_UDP=Server_UDP(debug=1)
	server_TCP=Server_TCP(debug=1)
	#Get_IP()