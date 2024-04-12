import discord
from discord.ext import commands
from discord.ext import tasks
import asyncio

import random

import utils
import datetime
import os

class ScheduleCog(commands.Cog):

	def __init__(self, bot):
		self.bot = bot
		self.schedule_url = "https://esparven.se/none/Team/Index/165"
		self.games = utils.get_schedule(self.schedule_url)
		self.current_msg = None
		self.bot_ctx = None
		self.message_pinned = False

	@commands.Cog.listener()
	async def on_ready(self):
		print(f"Logged in as {self.bot.user} (ID:{self.bot.user.id})")
		print("----------------------")
		

	@commands.Cog.listener()
	async def on_message(self, msg):
		if msg.author == self.bot.user:
			return
		
	@commands.command()
	async def init(self, ctx):
		if self.bot_ctx is None:
			self.bot_ctx = ctx
		await ctx.channel.send(f"Bot initialized...")
		self.update_schedule.start()

	@commands.command()
	async def start(self, ctx):
		self.check_schedule.start()		
		self.check_team.start()
		await ctx.channel.send(f"Bot started :)")


	@commands.command()
	async def schedule(self, ctx):
		str2send = f"___Kommande matcher___\n"
		today = datetime.datetime.now()
		for game in self.games:
			if game[1] > today:
				game_name = game[0]
				game_datetime_str = game[1].strftime("%Y-%m-%d %H:%M")
				str2send += f"{game_name:<25}{game_datetime_str:>20}\n"
		
		await ctx.channel.send(str2send)

	@commands.command()
	async def update_url(self, msg):
		self.schedule_url = msg.content
		self.games = utils.get_schedule(self.schedule_url)
		self.games.sort(key=lambda x: x[1])
	
	@tasks.loop(hours=168)
	async def update_schedule(self):
		games_remaining = len(self.games)
		self.games = utils.get_schedule(self.schedule_url)
		total_games = len(self.games)
		self.games.sort(key=lambda x: x[1])
		self.games = self.games[(total_games - games_remaining):]
		await self.bot_ctx.channel.send("Updated schedule")

	@tasks.loop(hours=12)
	async def check_schedule(self):
		if self.message_pinned:
			return
		for idx, game in enumerate(self.games):
			if game[1] > datetime.datetime.now():
				self.games = self.games[idx:]
		if len(self.games) == 0:
			return
		next_game = self.games[0]
		if next_game[1] < datetime.datetime.now() + datetime.timedelta(days=5):
			await self.send_game_info(next_game)
		
	@tasks.loop(hours=12)
	async def check_team(self):
		if not self.message_pinned:
			return
		next_game = self.games[0]
		if next_game[1] < datetime.datetime.now() + datetime.timedelta(days=3):
			await self.generate_team()
		
	async def send_game_info(self, next_game):
		message = "___Match!___\n"
		message += "@everyone\n"
		game_name = next_game[0]
		game_datetime_str = next_game[1].strftime("%A %-d/%-m %H:%M")
		message += f"{game_name:<30}{game_datetime_str:<25}\n"
		emoji_thumb_up = '\N{THUMBS UP SIGN}'
		emoji_thumb_down = '\N{THUMBS DOWN SIGN}'
		message += f"Reagera med {emoji_thumb_up} om ni vill lira\n\n"
		message += f"Reagera med {emoji_thumb_down} om ni är lite cringe"
		self.current_msg = await self.bot_ctx.channel.send(message)
		await self.current_msg.add_reaction(emoji_thumb_up)
		await self.current_msg.add_reaction(emoji_thumb_down)
		await self.current_msg.pin()
		self.message_pinned = True


	async def generate_team(self):
		await self.current_msg.unpin()

		available_players = []
		reactions = self.current_msg.reactions
		emoji_thumbs_up = '\N{THUMBS UP SIGN}'
		for reaction in reactions:
			if reaction.emoji == emoji_thumbs_up:
				available_players = [user for user in reaction.users()]
				available_players.remove(self.bot.user)
		if len(available_players) < 5:
			await self.bot_ctx.channel.send(f"Vi saknar {5 - len(available_players)} spelare")
		else:
			players = random.sample(available_players, 5)
			await self.bot_ctx.channel.send(f"{players[0].mention}, {players[1].mention}, {players[2].mention}, {players[3].mention} och {players[4].mention} lirar")
		self.message_pinned = False
		self.games = self.games[1:]

async def main(intents):
	bot = commands.Bot(command_prefix='!', intents=intents)
	await bot.add_cog(ScheduleCog(bot))
	return bot

if __name__ == "__main__":
	TOKEN = os.environ['ANDYTOKEN']
	intents = discord.Intents.default()
	intents.reactions = True
	intents.messages = True
	intents.message_content = True
	bot = asyncio.run(main(intents))
	bot.run(TOKEN)
