#coding:utf-8
'''nvshenheji爬虫 asyncio异步版本
https://www.nvshenheji.com/'''

from urllib.request import urlopen,urlretrieve,Request
from urllib import request,error
import os,sys,time,socket
import random

from lxml import etree
import aiohttp,asyncio
from bs4 import BeautifulSoup

from proxy_sampl import proxyDT5


baseurl = "http://www.nvshenheji.com"
localpath = "E:/scrapy/nvshenheji"	

pglist_lxml ='//div[@class="nr"]/table[4]//div[@class="page"]/a/@href'
imglist_lxml = "//div[@class='img']//img/@src"

#请求头
#headers = {}
headers = {#'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           #'Accept-Encoding': 'gzip, deflate',
            #'Cache-Control': 'max-age=0',
            #'Connection': 'keep-alive',
            #'If-None-Match': "8074a1d8816bd41:0",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
               }

## The proxy address and port:
#proxy_info = { 'host' : '140.227.71.235','port' : 3128 }
#serverlist = [
            #'104.248.161.173:8080','111.197.236.152:9999',
            #'201.184.135.90:42162','114.7.0.158:39345','119.101.116.30:9999','62.133.171.79:35335',
            #'49.156.35.230:58133','128.199.212.147:3128','128.199.212.147:3128','119.101.116.30:9999',
            #'140.227.200.38:3128','185.20.115.114:57236','85.133.207.14:56728',
            #'118.174.232.20:53450',
            #'182.160.117.130:53281','114.7.0.158:39345'
             #]
print('start get proxy! please wait!')
DT5 = proxyDT5()
serverlist = DT5.get_proxy()
## We create a handler for the proxy
#proxy = '221.7.255.167' #'112.13.170.135'
#proxy_support = request.ProxyHandler({"http":proxy})
## We create an opener which uses this handler:
#opener = request.build_opener(proxy_support)
## Then we install this opener as the default opener for urllib2:
#request.install_opener(opener)

def proxy_supporter(proxy_list,url):
	random.shuffle(proxy_list)
	for proxy in proxy_list:
		proxy_support = request.ProxyHandler({"http":proxy,"https":proxy})
		opener = request.build_opener(proxy_support)
		maxTryNum = 2
		for tries in range(maxTryNum):			
			req = Request(url,headers=headers)
			try:
				print(f"使用代理{proxy}获得数据")
				htmlcontent = opener.open(req,timeout=20)
				htmlcontent = htmlcontent.read()
				return htmlcontent
			except Exception as e:
				print(e)
				if tries <(maxTryNum-1):
					print("第%d次尝试再次连接网页"%(tries+2))
					time.sleep(3)
					continue	
				else:
					print("代理连接失败!")
	raise socket.timeout


#网页内容解析
def pagparser(url,headers=headers):				
	try:
		htmlcontent = proxy_supporter(serverlist,url)
		return htmlcontent
	except socket.timeout:
		try:
			print('尝试直接获取数据')
			req = Request(url,headers=headers)
			htmlcontent = urlopen(req).read()
			return htmlcontent
		except error.URLError:
			maxTryNum=2
			for tries in range(maxTryNum):	
				if isinstance(e.reason, socket.timeout):
					if tries <(maxTryNum-1):
						print("第%d次尝试再次连接网页"%(tries+2))
						time.sleep(3)
						continue	
					else:
						print("连接失败!")
						sys.exit(1)	
				else:
					raise


#注意！！！此处有坑，使用lxml解析可能造成内容缺失！可使用beautfulsoup(content,'html.parser')代替
#分页列表提取
def paglistparser(pagcontent):
	lxmlObj = etree.HTML(pagcontent)
	paglist = lxmlObj.xpath(pglist_lxml)[1:-1]
	if  paglist:
		return paglist
	else:
		print('lxml未解析成功，尝试Beautifulsoup解析')
		pagcontent = pagcontent.decode('gb2312','ignore')
		bsObj = BeautifulSoup(pagcontent,'html.parser')
		paglist =(url['href'] for url in bsObj.find_all('div','page')[1].find_all('a')[:-1])
		return paglist
		

#图片链接处理
def imgurlparse(pagecontent,baseurl):
	lxmlObj = etree.HTML(pagecontent)
	imgurllist = lxmlObj.xpath(imglist_lxml)
	imgurllist = [imgurl.strip() for imgurl in imgurllist]
	imgurllist = [baseurl+imgurl for imgurl in imgurllist]	
	if not imgurllist:
		print('尝试Beautifulsoup解析')
		pagecontent = pagecontent.decode('gb2312','ignore')
		bsObj = BeautifulSoup(pagecontent,'html.parser')
		imgurllist = [baseurl+src['src'] for src in bsObj.find('div','img').find_all('img')]	
	return imgurllist


async def nvImgpageparse(pageurl,baseurl):
	#女神合集图片集解析
	print('开始连接分页:',pageurl)
	pagcontent = pagparser(pageurl)
	paglist = paglistparser(pagcontent)
	paglist = [baseurl+pageurl for pageurl in paglist]
	print(f'共发现:{len(paglist)}张分页')
	imglist = imgurlparse(pagcontent,baseurl)
	#imglist = [baseurl+imgurl for imgurl in imglist]
	if imglist:
		conn = aiohttp.TCPConnector(limit=5)
		async with aiohttp.ClientSession(connector=conn,headers=headers) as session:
			_imglisttask = [imglistpasre(pageurl,session,imglist) for pageurl in paglist]	
			imgurllist = await asyncio.gather(*_imglisttask)
		print(f'共发现:{len(imglist)}张图片')
	return imglist
	
async def imglistpasre(pageurl,session,imglist):
	maxTryNum = 5
	for tries in range(maxTryNum):
		try:
			print("连接网页:%s"%pageurl)
			proxy = random.choice(serverlist)
			proxy = 'http://'+proxy
			print(f'使用代理{proxy}连接分页')
			async with session.get(pageurl,headers=headers,timeout=10,proxy = proxy ) as req:  
				pagcontent = await req.read()
				imglist.extend(imgurlparse(pagcontent,baseurl))  
			break
		except Exception as e:
			print(e)
			if tries < (maxTryNum-1):
				print("第%d次尝试再次连接网页"%(tries+2))
				await asyncio.sleep(3)
				print("重新链接%s"%pageurl)
				continue
			else:
				print("页面连接下载超时!")

	
#创建文件夹
def mk_dir(localpath,title):
	dirpath = localpath+'/'+title
	if not os.path.exists(dirpath):
		os.makedirs(dirpath)
		print(dirpath,"创建成功")
		return dirpath
	else:
		print(dirpath,"目录已存在")
		return 0

#保存图片，委派生成器	
async def savemany(imglist,dirpath):
	conn = aiohttp.TCPConnector(limit=5)
	imgalt = [imgurl[-15:] for imgurl in imglist] 
	imgitem = zip(imglist,imgalt)
	async with aiohttp.ClientSession(connector=conn) as session:
		_save = [imgsave(imgurl,imgalt,dirpath,session) for imgurl,imgalt in imgitem]
		await asyncio.gather(*_save) #多任务，注意*
	
		
#保存图片，委派生成器
async def imgsave(imgurl,imgalt,dirpath,session):
	print("开始连接图片",end="\t")
	img = await imgdowload(imgurl,session) 
	if img:
		imgpath = dirpath+'/'+imgalt
		print("开始保存,alt='{}'".format(imgalt))
		with open(imgpath,'wb') as f:
			f.write(img)
			f.flush()
		return imgalt

#异步下载图片,子生成器
async def imgdowload(imgurl,session,headers=headers):
	maxTryNum = 3
	for tries in range(maxTryNum):
		try:
			print("下载图片:%s"%imgurl)
			async with session.get(imgurl,headers=headers,timeout=20) as req:  
				img = await req.read()
			return img   
		except Exception as e: 
			print(e)
			if tries < (maxTryNum-1):
				print("第%d次尝试再次连接图片链接"%(tries+2))
				await asyncio.sleep(3)
				print("重新链接%s"%imgurl)
				continue
	print("图片连接下载超时!")
	return False

def mainpageparse(baseurl):
	print('开始链接主页:',baseurl)
	mainpageContent = pagparser(baseurl)
	lxmlObj = etree.HTML(mainpageContent)
	urllist = lxmlObj.xpath("//div[@class='dan']/a/@href")
	urllist = [baseurl+url for url in urllist]
	titlelist = lxmlObj.xpath("//div[@class='dan']/a/@title")	
	conlist = list(zip(urllist,titlelist))
	return conlist 
	
async def main(startpag,endpage,mainurl,localpath):	
	conlist = mainpageparse(mainurl)
	print(f'当前主页展示全部主题{len(conlist)}')
	for theme in conlist:
		print(f'{theme[1]}')
	order = input('是否下载？([Y]下载，其它关闭程序):')
	if order != 'y':
		sys.exit()
	pagnum = 0
	for pagurl,title in conlist[startpag:endpage]:
		print('start try save theme%d:%s'%(pagnum,title))
		print('start parse:%s'%pagurl)
		imglist = await nvImgpageparse(pagurl,baseurl)
		if imglist:
			try:
				dirpath = mk_dir(localpath,title)
				if dirpath:
					await savemany(imglist,dirpath)#并发下载图片
				else:
					print("该主题可能已下载")
					break
			except Exception as e:
				print(e)
				break
		else:
			print("解析可能出现错误，未发现图片")
			continue
		pagnum += 1
	print('finish work!total theme:',pagnum)


if __name__ == '__main__':
	#本地存放地址
	asyncio.run(main(0,None,baseurl,localpath))
