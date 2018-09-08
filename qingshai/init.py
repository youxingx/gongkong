# -*- coding:utf-8 -*-
import server
import serials
import file
import time
import data
import shortradar

debug=1
def main():
	# 创建一个文件对象，包含对配置文件以及日志文件的处理
	Log_Cfg=file.File_init(debug=debug)
	# 创建一个GPS对象，通过串口对gps数据进行处理  COM1
	Serial_GPS=serials.Serial_GPS('/dev/ttymxc1')
	# 创建一个角度对象，通过串口对角度传感器数据进行处理  COM6
	Serial_Angle=serials.Serial_Angle('/dev/ttyHBB1')
	# 创建一个长程雷达对象，通过串口对长程雷达数据进行处理  COM4
	Serial_LongRadar=serials.Serial_LongRadar('/dev/ttymxc4')
	# 创建短程雷达对象，通过回环网络udp通信对长程雷达数据进行处理  ip:127.0.0.1 port:9000
	Udp_ShortRadar=shortradar.ShortRadar(port=9000)
	# 创建一个udp对象，处理udp数据
	UDP_Server=server.Server_UDP(debug=debug,uip='192.168.183.3',port=4004) #默认本机UDP，match为GPS回环过滤地址（网段）
	# 创建一个TCP对象，处理和TOD之间的Tcp通信
	TCP_Server=server.Server_TCP(debug=debug,port=5000)
	
if __name__=='__main__':
	main()

