import os
import data
import json
import time
import re
import threading
import sys

INIT_NAME = 'Config.ini'
RAW_DIR='Raws'
LOG_DIR='Logs'
FILE_SIZE=10*1024     #k
# PATH_SIZE=10*1024     #m
PATH_SIZE=1*1024     #m
class File_init(data.Data):
	# 初始化函数，创建日志处理和配置文件处理线程
	def __init__(self,cfg_name=INIT_NAME,raw_dir=RAW_DIR,log_dir=LOG_DIR,debug=0,size=FILE_SIZE,path=PATH_SIZE):
		self.ini_name=cfg_name
		self.log_dir=log_dir
		self.raw_dir=raw_dir
		self.debug=debug
		self.size=size#文件最大，单位KB
		self.path_max=path #文件夹最大,单位MB
		# 创建配置文件处理线程
		threading.Thread(target=self.Config_init,args=(self.ini_name,)).start()
		# 创建日志文件处理线程，日志包含两种，log文件夹下的记录和raw文件夹下的记录
		# log文件夹下存储的是发送给TOD的数据记录
		# raw文件夹下存储的是个传感器的原始数据，包括GPS数据，角度传感器数据，
		threading.Thread(target=self.Logs_log).start()
		threading.Thread(target=self.Logs_raw).start()
		print('LOADING CONFIG ...')
		# 睡眠2s钟，等待配置文件读取完成
		time.sleep(2)
	def Config_init(self,name):
		if self.debug:
			print('Config_init')
		#读取配置文件
		if os.path.exists(name):
			with open(name,'r',encoding='utf-8') as f:
				r=re.sub(r'#.*\n','',f.read())#去除注释
				r=json.loads(r)
				super().set_ini(r)
				data.Data.LOCAL_GPS['ID'] = data.Data.ini['localID']
				data.Data.LOCAL_GPS['LocalIp'] = data.Data.ini['localIP']
				data.Data.FB_GPS[0]['ID'] = data.Data.ini['fwdTrainID']
				data.Data.FB_GPS[0]['IP'] = data.Data.ini['fwdTrainIP']
				data.Data.FB_GPS[1]['ID'] = data.Data.ini['backTrainID']
				data.Data.FB_GPS[1]['IP'] = data.Data.ini['backTrainIP']
				# data.Data.LOCAL_ID = data.Data.ini['localID']
		else:
			#配置文件不存在存入日志记录
			if self.debug:
				print('error!!!')
				# print('配置文件不存在，请先设置配置文件')
				print('config file not exist please set config file')
			errorMsg = {'Time':time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time())),'errorMsg':'config file loss'}
			data.Data.STORE_SEND.append(errorMsg)
			data.Data.SEND_STATE=1
		while True:
			# 定时判断配置文件是否需要更改,如果需要更改,则将数据写入配置文件中，周期为3秒
			if not os.path.exists(name) or super().get_ini_state():
				with open(name,'w',encoding='utf-8') as f:
					# l=['#配置文件为JSON格式，请务必保证格式正确，错误将无法运行，可删除文件重新运行重置\n',
					# 	'#COMS为串口号，有序，默认1,2,3,4,5对应GPS,角度传感器，左雷达，长雷达，右雷达\n'
					# ]
					# f.writelines(l)
					f.write(json.dumps(super().get_ini(),sort_keys=True,ensure_ascii=False,indent=4,separators=(',',':'),skipkeys=True))
				super().ini_state_clr()
			else:
				if not super().get_ini():
					with open(name,'r',encoding='utf-8') as f:
							r=re.sub(r'#.*\n','',f.read())#去除注释
							r=json.loads(r)
					super().set_ini(r)
			# 睡眠3s
			time.sleep(3)
	# 存储上传给TOD的报文处理函数
	def Store_send(self,s,path='Logs'):
		if s is not None:
			# 存储数据不为空，进行存储
			if not os.path.exists(path):
				# 判断文件夹是否存在，如果不存在，则建立
				os.mkdir(path)
				if(self.debug==1):
					print('create Log file')
					# print('建立日志文件夹')
			t=time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time()))
			filelist = os.listdir('./%s/'%path)
			filelist.sort()
			if filelist:
				# 获取文件夹文件列表，计算文件夹大小，若超过1G，则删除最早的文件，防止存储过多数据，把硬盘塞满
				# 1G数据能够存储3天左右的数据
				path_size=0
				for i in filelist:
					path_size+=os.path.getsize('./%s/%s'%(path,i))
				if(path_size>self.path_max*1024*1024):
					os.remove('./%s/%s'%(path,os.listdir('./%s/'%path)[0]))
				# 获取当前文件大小，若文件大于10M，则重新建一个文件，防止文件过大，不易于查找
				f=filelist[-1]
				size=os.path.getsize('./%s/%s'%(path,f))
				if(size<(self.size*1024) and re.findall(r'\d{4}\.\d{1,2}\.\d{1,2}',t)==re.findall(r'\d{4}\.\d{1,2}\.\d{1,2}',f)):
					pass
				else:
					if(self.debug==1):
						print('create Log file')
						# print('建立日志文件')
					f=t+'.txt'
			else:
				if(self.debug==1):
					print('create Log file')
					# print('建立日志文件')
				f=t+'.txt'
			# 将数据写入文件
			with open('./%s/%s'%(path,f),'a',encoding='utf-8') as f:
				try:
					f.write(json.dumps(s,sort_keys=True,ensure_ascii=False,indent=4,separators=(',',':'),skipkeys=True))
				except Exception as e:
					print(e)

	# 存储传感器收到的
	def Store_raw(self,s,path='Raws'):
		if s is not None:
			# 存储数据不为空，进行存储
			if not os.path.exists(path):
				# 判断文件夹是否存在，如果不存在，则建立
				os.mkdir(path)
				if(self.debug==1):
					# print('建立日志文件夹')
					print('create Log file')
			t=time.strftime('%Y.%m.%d-%H.%M.%S',time.localtime(time.time()))
			filelist = os.listdir('./%s/'%path)
			filelist.sort()
			if filelist:
				# 获取文件夹文件列表，计算文件夹大小，若超过1G，则删除最早的文件，防止存储过多数据，把硬盘塞满
				# 1G数据能够存储3天左右的数据
				path_size=0
				for i in filelist:
					path_size+=os.path.getsize('./%s/%s'%(path,i))
				if(path_size>self.path_max*1024*1024):
					os.remove('./%s/%s'%(path,os.listdir('./%s/'%path)[0]))
				# 获取当前文件大小，若文件大于10M，则重新建一个文件，防止文件过大，不易于查找
				f=filelist[-1]
				size=os.path.getsize('./%s/%s'%(path,f))
				if(size<(self.size*1024) and re.findall(r'\d{4}\.\d{1,2}\.\d{1,2}',t)==re.findall(r'\d{4}\.\d{1,2}\.\d{1,2}',f)):
					pass
				else:
					if(self.debug==1):
						# print('建立日志文件')
						print('create Log file')
					f=t+'.txt'
			else:
				if(self.debug==1):
					# print('建立日志文件')
					print('create Log file')
				f=t+'raw.txt'
			# 将数据写入文件
			with open('./%s/%s'%(path,f),'a',encoding='utf-8') as f:
				try:
					f.writelines(s)
				except Exception as e:
					print(e)
	# 存储上传给TOD的报文线程，每隔1s查询一次，是否需要进行数据存储
	def Logs_log(self):
		while True:
			if data.Data.SEND_STATE==1:
				self.Store_send(super().get_send(),path=self.log_dir)
			time.sleep(1)
	# 存储各传感器数据线程，每隔1s查询一次，是否需要进行数据存储
	def Logs_raw(self):
		while True:
			if data.Data.RAW_STATE==1:
				self.Store_raw(super().get_raw(),path=self.raw_dir)
			time.sleep(1)
	def Readme_init(self,name):
		pass
if __name__=='__main__':
	init=File_init()
		