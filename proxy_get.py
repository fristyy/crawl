#coding:utf-8
#使用代理获取数据
import urllib.request
import asyncio,aiohttp

import requests
from bs4 import BeautifulSoup 

import ssl
#ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain (_ssl.c:1045)
#某些IP报错，看是否能解决pyhon升级到2.7.9以后，引入了一个新特性，当使用urllib打开https的链接时，会检验一次ssl证书。而当目标网站使用的是自签名证书时，就会抛出urllib2.URLError的错误。
#全局取消证书验证（当项目对安全性问题不太重视时，推荐使用）
ssl._create_default_https_context = ssl._create_unverified_context
#无效

baseurl = "https://www.nvshenheji.com"
url = 'https://www.baidu.com'
frurl = 'https://www.google.com'

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}
#headers = {#'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		#'Connection': 'keep-alive',
		#'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
		#}

class proxyDT5:
	def __init__(self):
		self.proxyWeburl = 'http://www.data5u.com/'
		self.ip_list =[]

	#端口破解,此网站浏览器显示端口与爬虫所取数据不一致，port后class属性字母串为端口的数据源。
	def _decrypt(self,src):
		s = 'ABCDEFGHIZ'
		dst = ''
		for c in src:
			dst += str(s.find(c))
		dst = int(dst) >> 3
		return dst
	
	#regex = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')正则匹配IP地址
	#regex = re.compile('<li class="port (.*?)">')正则匹配port
	
	
	def _ip_get(self,url):
		r = requests.get(self.proxyWeburl,headers=headers)
		bsobj = BeautifulSoup(r.text)
		for tag in bsobj.find_all('ul','l2'):
			self.ip_list.append((tag.li.string,self._decrypt(tag.find_all("li", "port")[0]['class'][1])))
		print(self.ip_list)
				
				
	async def aio_handler(self, proxy, session):
		proxy = 'http://'+proxy[0]+':'+ str(proxy[1])
		try:
			async with session.get(url,proxy = proxy,headers=headers,timeout=20) as req:  
				pagcontent = await req.read()
				print(f'{proxy}useable,content{len(pagcontent)}')
			return proxy
		except:
			continue
			
				
	async def aio_test(self):
		conn = aiohttp.TCPConnector(limit=10)
		async with aiohttp.ClientSession(connector=conn) as session:
			_useableIpTask = [self.aio_handler(proxy, session) for proxy in self.ip_list]
			useableIpList = await asyncio.gather(*_useableIpTask)
			useableIpList= [ i for i in filter(None,useableIpList)]
		print(useableIpList)
		return useableIpList
			
	def get_proxy(self):	
		self._ip_get(self.proxyWeburl)
		#test(iplist)
		__proxylist = asyncio.run(self.aio_test())
		return __proxylist
