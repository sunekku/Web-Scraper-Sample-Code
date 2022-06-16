from __future__ import unicode_literals
from utils.utilities import *
from utils.mongo_interface import *

import requests
import json
import string
import io
import aiohttp
import re
import urllib.request
from bs4 import BeautifulSoup
from random import randrange


class WebScraper(commands.Cog):
    '''
    Credits to Sunekku (Nuha Sahraoui).
    '''
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.last_search = ""
        self.cur_page = 0
        self.prev_search = None
        self.extensions = None
        self.prev_tag = ""

    @commands.command()
    async def nsearch(self, ctx: commands.Context, *, args:str = "sample"):
        
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        headers={'User-Agent':user_agent,}
        tags = re.split("\s", args)
        url = 'https://sample.net/search/?q='
        for i in range(len(tags)):
            url += (tags[i] + '+')
        request = urllib.request.Request(url,None,headers)
        try:
            response = urllib.request.urlopen(request)
        except ValueError:
            await ctx.send(
                "No results found. Please try another tag.")
            return
        
        
        data = response.read()
        soup = BeautifulSoup(data, 'html.parser')
        num_results = re.findall(r'(?<=/i> ).*?(?= r)', str(soup.h1))[0]
        num_results = re.split('\,', num_results)
        if 'No' in (num_results):
            await ctx.send(
                "No results found. Please try another tag.")
            return
        
        self.prev_tag = args

        num = ""
        for k in range(len(num_results)):
            num += num_results[k]
        num = int(num)
        if num % 25 != 0:
	        num_pages = num//25 + 1
        else:
            num_pages = num//25
        page = randrange(1, num_pages + 1)
        url2 = url + '&page={page}'.format(page=page)
        request = urllib.request.Request(url2,None,headers)
        response = urllib.request.urlopen(request)
        data = response.read()
        soup = BeautifulSoup(data, 'html.parser')

        list_nums = []
        for j in range(len(soup.find_all('a'))):
            entry = soup.find_all('a')[j]
            entry = BeautifulSoup(str(entry))
         
            entry = entry.a['href']
            if re.search("^/g/\d+", entry):
                search_number = int(re.findall(r"g/(\d+)/", entry)[0])
                list_nums.append(search_number)
   
        search = list_nums[randrange(len(list_nums))]
      
        await self.nsample(ctx = ctx, args = search)



    @commands.command()
    async def nsample(self, ctx: commands.Context, args:int = 295198):
        self.cur_page = 0
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        headers={'User-Agent':user_agent,}
        url = 'https://sample.net/g/{num}/'.format(num=args)
        request = urllib.request.Request(url,None,headers)
        try:
            response = urllib.request.urlopen(request)
        except:
            await ctx.send(
                "No results found. Please try another entry.")
            return
        
        
        data = response.read()
        soup = BeautifulSoup(data, 'html.parser')
        cover_url = soup.find_all('meta')[3]
        cover_url = str(cover_url)
        title = soup.find_all('meta')[2]
        title = str(title)
        title = re.findall(r'(?<=").*?(?=")', title)[0]

        artist_name = []

        data = str(soup.find_all('section')[1])
        data = BeautifulSoup(data)
        data = data.find_all('a')
        for k in range(len(data)):
	        result = data[k]
	        result = BeautifulSoup(str(result))
	        result = result.a['href']
	        if re.search('/artist/', result):
		        artist_name = re.findall(r'(?<=/).*?(?=/)', result)
        
        gallerynumber = int(re.findall(r"galleries/(\d+)/cover.", cover_url)[0])

        imgs = []
        for i in range(len(soup.find_all('noscript'))):
            s = soup.find_all('noscript')[i]
            s = str(s)
            new_soup = BeautifulSoup(s)
            x = new_soup.img['src']
            if re.search('/{}/'.format(gallerynumber), s):
                y = re.split("\.", x)
            imgs.append(y[len(y) - 1])
        self.extensions = imgs

        if artist_name:
            artist_name.pop(0)
            value = artist_name[0]
        else:
            value = "N/A"

        
        img_url = 'https://t.sample.net/galleries/{gallerynumber}/cover.'.format(gallerynumber = gallerynumber) + imgs[0]
        e = discord.Embed(
                            title=title,
                            description='ID: {postid}'.format(postid=args),
                            url=url,
                            color=0xfecbed)
        e.add_field(name='artist',
                                     value=value,
                                     inline=True)
        e.set_image(url=img_url)
        await ctx.send(embed=e)
        self.prev_search = gallerynumber
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.message):
        if "next" in message.content.lower() and message.channel.id == getCFG(message.guild.id)["sample channel"]:
            await self.sample(ctx = await self.bot.get_context(message), args = self.last_search)
        if "retry" in message.content.lower() and message.channel.id == getCFG(message.guild.id)["sample channel"]:
            await self.nsearch(ctx = await self.bot.get_context(message), args = self.prev_tag)
        if "np" in message.content.lower() and message.channel.id == getCFG(message.guild.id)["sample channel"]:
            ctx = await self.bot.get_context(message)
            self.cur_page += 1
            img_url = 'https://i.nsample.net/galleries/{gallerynumber}/{page}.'.format(gallerynumber=self.prev_search, page=self.cur_page) + self.extensions[self.cur_page]
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url) as resp:
                    if resp.status != 200:
                        await ctx.send(
                            'You have reached the end of this work.')
                    else:
                        data = io.BytesIO(await resp.read())
                        await ctx.send(
                            file=discord.File(data, img_url))


    @commands.command()
    async def sample(self, ctx: commands.Context, *, args:str = ""):
        '''
        Fetches a number of posts from Sample given a series of tags.
        Ex. $c sample hanako 2
        Use $c sample clear to purge all messages
        Creds to Sunekku on Github
        '''

        args = args.split()

        limit = 1
        tag_list = []
        if len(args) > 0:
            if args[len(args) - 1].isnumeric():
                limit = int(args[len(args) - 1])
                for i in range(len(args) - 1):
                    tag_list.append(args[i])
            else:
                for i in range(len(args)):
                    tag_list.append(args[i])

        if limit > 20:
            await ctx.send("Please enter a number lower than 20.")
        else:
            if ctx.channel.id == getCFG(ctx.guild.id)["sample channel"]:
                if "clear" in tag_list:
                    setTGT(self.bot.user)
                    await ctx.channel.purge(check=purgeCheck, bulk=True)
                else:
                    url_base = 'https://sample.com/index.php?page=dapi&s=post&q=index&json=1'
                    url_base = url_base + '&limit={limit}&tags=-rating%3asafe+sort:random+'.format(
                        limit=limit)
                    for i in range(len(tag_list)):
                        url_base = url_base + '{tag}+'.format(tag=tag_list[i])
                        
                    try:
                        posts = requests.get(url_base).json()
                    except ValueError:
                        await ctx.send(
                            "No results found. Please try another tag.")
                        return

                    if len(tag_list) == 0:
                        count = "N/A"
                    else:
                        new_tag = tag_list[0]
                        if tag_list[0].endswith('*'):
                            new_tag = tag_list[0][:len(tag_list[0]) - 1]
                        try:
                            num_results = requests.get(
                                'https://sample.com/index.php?page=dapi&s=tag&q=index&json=1&name={tags}'
                                .format(tags=new_tag)).json()
                        except:
                            count = "N/A"
                        else:
                            if len(num_results) != 0:
                                count = num_results[0]['count']
                            else:
                                count = 0
                    for i in range(len(posts)):
                        img_url = posts[i]['file_url']

                        score = posts[i]['score']
                        postid = posts[i]['id']
                        tags = ""
                        for k in range(len(tag_list)):
                            tags += " " + tag_list[k]
                        tag_string = posts[i]['tags']
                        e = discord.Embed(
                            title=tags,
                            description='ID: {postid}'.format(postid=postid),
                            url=img_url,
                            color=0xfecbed)
                        e.set_author(name='Retrieved from Sample')
                        e.add_field(name='score',
                                    value=posts[i]['score'],
                                    inline=True)
                        e.add_field(name='rating',
                                    value=posts[i]['rating'],
                                    inline=True)
                        e.add_field(name='hit count', value=count, inline=True)
                        e.set_footer(text=tag_string)
                        e.set_image(url=img_url)

                        if img_url.endswith(".webm"):
                            async with aiohttp.ClientSession() as session:
                                async with session.get(img_url) as resp:
                                    if resp.status != 200:
                                        await ctx.send(
                                            'Could not download file.')
                                    else:
                                        data = io.BytesIO(await resp.read())
                                        e.set_thumbnail(
                                            url=
                                            'https://img.icons8.com/cotton/2x/movie-beginning.png'
                                        )
                                        await ctx.send(embed=e)
                                        await ctx.send(
                                            file=discord.File(data, img_url))
                        else:
                            e.set_thumbnail(
                                url=
                                'https://vectorified.com/images/image-gallery-icon-21.png'
                            )
                            await ctx.send(embed=e)
                        
                        s = ""
                        for k in range(len(args)):
                            s = s + args[k] + " "
                        self.last_search = s

            else:
                await delSend("Please use this command in the sample channel.",
                              ctx.channel)
