#coding:utf-8
'''nvshenheji爬虫 asyncio异步版本
https://www.nvshenheji.com/'''

from urllib.request import urlopen
from urllib import request,error
import os,sys,time,socket
import random
from tqdm import tqdm

from lxml import etree
import aiohttp,asyncio
from bs4 import BeautifulSoup

from proxy_sampl import proxyDT5


baseurl = "http://www.nvshenheji.com"
localpath = "E:/scrapy/nvshenheji"	

pglist_lxml ='//div[@class="nr"]/table[4]//div[@class="page"]/a/@href'
imglist_lxml = "//div[@class='img']//img/@src"

baseurl = "https://www.nvshenheji.com"
localpath = "E:/scrapy/nvshenheji"	

pglist_lxml ='//div[@class="nr"]/table[4]//div[@class="page"]/a/@href'
imglist_lxml = "//div[@class='img']//img/@src"

Falseimg = []  #下载未成功的图片url收集

headers = {#'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           #'Accept-Encoding': 'gzip, deflate',
            #'Cache-Control': 'max-age=0',
            #'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
               }

serverlist = [ 
              'http://35.245.208.185:3128',  
              'http://125.27.10.209:59790', 
              'http://14.207.121.183:8080', 
              'http://1.20.100.219:60095', 
              'http://185.22.174.69:10010', 
              'http://193.41.88.58:53281', 
              'http://180.159.252.111:9000', 
              'http://216.54.73.122:46564', 
              'http://51.15.69.7:3129']
             
#本段代码自动获取免费代理
#print('start get proxy! please wait!')
#DT5 = proxyDT5()
#serverlist = DT5.get_proxy()

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
	imgurllist = (imgurl.strip() for imgurl in imgurllist)
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
	paglist = (baseurl+pageurl for pageurl in paglist)
	print(f'分析完毕，共发现:{len(paglist)}张分页')
	imglist = imgurlparse(pagcontent,baseurl)
	if imglist:
		with tqdm(total=len(paglist),ncols=70) as pbar:  #分析进度显示
			conn = aiohttp.TCPConnector(limit=5)
			async with aiohttp.ClientSession(connector=conn,headers=headers) as session:
				_imglisttask = [imglistpasre(pageurl,session,imglist,pbar) for pageurl in paglist]	
				imgurllist = await asyncio.gather(*_imglisttask)
		print(f'共发现:{len(imglist)}张图片')
	return imglist

#获取分页图片列表	
async def imglistpasre(pageurl,session,imglist,pbar):
	maxTryNum = 5
	proxy = random.choice(serverlist)
	for tries in range(maxTryNum):
		try:
			async with session.get(pageurl,headers=headers,timeout=10,proxy = proxy ) as req:  
				pagcontent = await req.read()
				imglist.extend(imgurlparse(pagcontent,baseurl))  
			pbar.update(1)
			break
		except Exception as e:
			print(e) 
			if tries < (maxTryNum-1):
				await asyncio.sleep(3)
				continue
			else:
				print("页面连接下载超时!")
				sys.exit(1)

	
#创建文件夹
def mk_dir(localpath,title):
	dirpath = localpath+'/'+title
	if not os.path.exists(dirpath):
		os.makedirs(dirpath)
		print(dirpath,"创建成功")
		return dirpath
	elif not os.listdir(dirpath):
		print(dirpath,"空目录已存在")
		return dirpath
	else:
		print(dirpath,"目录已存在")
		return 0

#保存图片，委派生成器	
async def savemany(imglist,dirpath):
	conn = aiohttp.TCPConnector(limit=10)
	rerul = re.compile('/\w+.jpg')
	imgalt = [rerul.findall(imgurl)[-1] for imgurl in imglist] 
	imgitem = zip(imglist,imgalt)
	print('开始下载图片>>>')
	with tqdm(total=len(imgalt),ncols=70) as pbar:
		async with aiohttp.ClientSession(connector=conn) as session:
			_save = [imgsave(imgurl,imgalt,dirpath,session, pbar) for imgurl,imgalt in imgitem]
			await asyncio.gather(*_save) #多任务，注意*
	for falseimg in Falseimg:
		print(f'下载失败图片{falseimg}')
	
		
#保存图片，委派生成器
async def imgsave(imgurl,imgalt,dirpath,session, pbar):
	try:
		img = await imgdowload(imgurl,session) 
	except Exception as e:
		print('开始连接图片时发生错误',e)
	if img:
		try:
			imgpath = dirpath+'/'+imgalt
			#print("开始保存,alt='{}'".format(imgalt))
			with open(imgpath,'wb') as f:
				f.write(img)
				f.flush()
			pbar.update(1)
			return imgalt
		except Exception as e:
			print('保存时出现错误',e)
			sys.exit()

#异步下载图片,子生成器
async def imgdowload(imgurl,session,headers=headers):
	maxTryNum = 3
	#proxy = random.choice(serverlist)
	for tries in range(maxTryNum):
		try:
			async with session.get(imgurl,timeout=20) as req: 
				img = await req.read()
			return img   
		except Exception as e: 
			#print('图片下载时发生错误:',e)
			if tries < (maxTryNum-1):
				#print("第%d次尝试再次连接图片链接"%(tries+2))
				await asyncio.sleep(3)
				continue
	#print("图片连接下载超时!")
	Falseimg.append(imgurl)
	return 0

#主页分析，主获取主题列表 
def mainpageparse(baseurl):
	print('开始链接主页:',baseurl)
	mainpageContent = pagparser(baseurl)
	lxmlObj = etree.HTML(mainpageContent)
	urllist = lxmlObj.xpath("//div[@class='dan']/a/@href")
	urllist = [baseurl+url for url in urllist]
	titlelist = lxmlObj.xpath("//div[@class='dan']/a/@title")	
	conlist = list(zip(urllist,titlelist))
	return conlist 

#自动检索首页推荐栏全部主题，并判断是否已下载过。	
async def main(startpag=0,endpage=None,mainurl=baseurl,localpath=localpath):	
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
		dirpath = mk_dir(localpath,title)
		if not dirpath:
			print('该主题可能已下载')
			break
		imglist = await nvImgpageparse(pagurl,baseurl)
		if imglist:
			
			try:	
				await savemany(imglist,dirpath)#并发下载图片
			except Exception as e:
				print('下载保存时错误',e)
				break
		else:
			print("解析可能出现错误，未发现图片")
			continue
		pagnum += 1
	print('finish work!total theme:',pagnum)
	sys.exit()

#单独下载某主题
async def subTheme(themeurl,title):
	dirpath = mk_dir(localpath,title)
	if not dirpath:
		print('该主题可能已下载')
		sys.exit(0)
	imglist = await nvImgpageparse(themeurl,baseurl)
	if imglist:
		try:
			await savemany(imglist,dirpath) #并发下载图片
		except Exception as e:
			print(e)
			sys.exit(0)
	else:
		print("解析可能出现错误，未发现图片")
		sys.exit(0)
	print('finish work!total theme:')	

if __name__ == '__main__':
	#启动主页下载
	#asyncio.run(main())	
	#启动单独下载
	asyncio.run(subTheme('https://www.nvshenheji.com/Candy/linmeihuizi_ef89683e.html','[Candy糖果画报]Vol.046_嫩模林美惠子Mieko沙巴旅拍蓝色紧身泳衣完美曲线写真51P'))
