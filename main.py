import os
import discord
from discord.ext import commands, tasks
import requests
import asyncio
import aiohttp
import datetime
from dotenv import load_dotenv
from datetime import timezone, timedelta


# Load environment variables from .env file
load_dotenv()

# Your Discord Bot Token
TOKEN = os.getenv('DISCORD_TOKEN')

# Your YouTube API key
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Your Twitch API credentials
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_ACCESS_TOKEN = os.getenv('TWITCH_ACCESS_TOKEN')

# Dictionary to store server settings for YouTube notifications
youtube_server_settings = {
    'UCO1rM0lN25bStjzsO83W3Qg': [  # YouTube Channel 1
        {
            'server_id': # your discord server ID,  # Discord Server ID
            'channel_id': # your discord channel ID,  # Channel ID where you want to send YouTube notifications Important
            'role_id': # your discord role ID or '@everyone',     # Role ID to ping when a new YouTube video is uploaded Cdawg Fan
            'channel_name': 'Cdawg',  # Channel Name
        },
        {
            'server_id': # your discord server ID,  # Discord Server ID
            'channel_id': # your discord channel ID,  # Channel ID where you want to send YouTube notifications Video
            'role_id': # your discord role ID or '@everyone',     # Role ID to ping when a new YouTube video is uploaded Cdawg Fan
            'channel_name': 'Cdawg',  # Channel Name
        },
    ],
    'UCHU3ShHQ7GDnR-RnRU-oKOA': [  # YouTube Channel 1
        {
            'server_id': # your discord server ID,  # Discord Server ID
            'channel_id': # your discord channel ID,  # Channel ID where you want to send YouTube notifications
            'role_id': # your discord role ID or '@everyone',     # Role ID to ping when a new YouTube video is uploaded
            'channel_name': 'Cdawg Music',  # Channel Name
        },
        {
            'server_id': # your discord server ID,  # Discord Server ID
            'channel_id': # your discord channel ID,  # Channel ID where you want to send YouTube notifications
            'role_id': # your discord role ID or '@everyone',     # Role ID to ping when a new YouTube video is uploaded
            'channel_name': 'Cdawg Music',  # Channel Name
        },
    ],
    'UCNU1AHWgWknrRAfAh36YgSg': [  # YouTube Channel 2
        {
            'server_id': # your discord server ID,  # Discord Server ID
            'channel_id': # your discord channel ID,  # Channel ID where you want to send YouTube notifications
            'role_id': # your discord role ID or '@everyone',     # Role ID to ping when a new YouTube video is uploaded
            'channel_name': 'Cdawg 2',  # Channel Name
        },
        {
            'server_id': # your discord server ID,  # Discord Server ID
            'channel_id': # your discord channel ID,  # Channel ID where you want to send YouTube notifications
            'role_id': # your discord role ID or '@everyone',     # Role ID to ping when a new YouTube video is uploaded
            'channel_name': 'Cdawg 2',  # Channel Name
        },
    ]
}

# Dictionary to store Twitch channel settings
twitch_channel_settings = {
    'cdawg0012': [  # Cdawg0012's Twitch channel
        {
            'server_id': # your discord server ID,    # Server 1
            'channel_id': # your discord channel ID,  # Channel ID where you want to send Twitch notifications
            'role_id': # your discord role ID or '@everyone',     # Role ID to ping when a Twitch stream goes live
            'custom_message': 'Cdawg has gone live on Twitch\nhttps://www.twitch.tv/cdawg0012',  # Custom message with channel link
            'live': False  # Initial status, assuming offline
        },
        {
            'server_id': # your discord server ID,    # Server 2
            'channel_id': # your discord channel ID,  # Channel ID where you want to send Twitch notifications
            'role_id': # your discord role ID or '@everyone',     # Role ID to ping when a Twitch stream goes live
            'custom_message': 'Cdawg has gone live on Twitch\nhttps://www.twitch.tv/cdawg0012',  # Custom message with channel link
            'live': False  # Initial status, assuming offline
        }
    ],
    'dankdekuskrub': [  # Dank's Twitch channel
        {
            'server_id': # your discord server ID,    # Server 1
            'channel_id': # your discord channel ID,   # Channel ID where you want to send Twitch notifications
            'role_id': # your discord role ID or '@everyone',     # Role ID to ping when a Twitch stream goes live
            'custom_message': "Dank has gone live on Twitch now that's Dank\nhttps://www.twitch.tv/dankdekuskrub",  # Custom message with channel link
            'live': False                        # Initial status, assuming offline
        },
        {
            'server_id': # your discord server ID,    # Server 2
            'channel_id': # your discord channel ID,   # Channel ID where you want to send Twitch notifications
            'custom_message': "Dank has gone live on Twitch now that's Dank\nhttps://www.twitch.tv/dankdekuskrub",  # Custom message with channel link
            'live': False                        # Initial status, assuming offline
        }
    ]
}

# Initialize bot with intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
bot = commands.Bot(command_prefix='!', intents=intents)


def utc_to_local(utc_time):
    return datetime.datetime.now()


@tasks.loop(minutes=1)  # Check YouTube every minute
async def check_youtube_loop():
    try:
        print("Checking YouTube...")
        await check_youtube()
        print("YouTube check completed.")
    except Exception as e:
        print(f"An error occurred in the YouTube check loop: {e}")

@tasks.loop(minutes=1)  # Check Twitch every minute
async def check_twitch_loop():
    try:
        print("Checking Twitch...")
        await check_live_status()
        print("Twitch check completed.")
    except Exception as e:
        print(f"An error occurred in the Twitch check loop: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name="Code was created by Cdawg0012 (https://cdawg.live)"))
    check_youtube_loop.start()  # Start the YouTube check loop
    check_twitch_loop.start()   # Start the Twitch check loop

async def check_youtube():
    current_time_local = datetime.datetime.now()

    if (current_time_local.minute == 2 and current_time_local.hour in [3, 9, 15, 21]) or \
       (current_time_local.minute == 12 and current_time_local.hour in [0, 6, 12, 18]):
        print(f"Time is {current_time_local.strftime('%H:%M')}. Checking YouTube now.")
        for channel_id, settings in youtube_server_settings.items():
            latest_video = get_youtube_latest_video(channel_id)
            if latest_video:
                video_log_file = f'youtube_video_log_{channel_id}.txt'
                uploaded_video_ids = read_video_log(video_log_file)
                if latest_video['video_id'] not in uploaded_video_ids:
                    uploaded_video_ids.add(latest_video['video_id'])
                    log_new_video(video_log_file, latest_video['video_id'])
                    for setting in settings:
                        server_id = setting['server_id']
                        guild = bot.get_guild(server_id)
                        if guild:
                            await send_youtube_notification(setting, latest_video, guild)
                        else:
                            print(f"Guild with ID {server_id} not found.")
            else:
                print(f"No videos found for channel {channel_id}")
    else:
        print("Not time for checking YouTube.")

def get_youtube_latest_video(channel_id):
    url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=1&order=date&type=video&key={YOUTUBE_API_KEY}'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'items' in data and data['items']:
            latest_video_id = data['items'][0]['id']['videoId']
            latest_video_title = data['items'][0]['snippet']['title']
            return {'video_id': latest_video_id, 'video_title': latest_video_title}
        else:
            print(f"No videos found for channel {channel_id}")
            return None
    except Exception as e:
        print(f"Error fetching latest video for channel {channel_id}: {e}")
        return None
    
def log_new_video(file_name, video_id):
    with open(file_name, 'a') as f:
        f.write(f"{video_id}\n")

def read_video_log(file_name):
    uploaded_video_ids = set()
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            for line in f:
                uploaded_video_ids.add(line.strip())
    return uploaded_video_ids


async def send_youtube_notification(setting, latest_video, guild):
    server_id = setting['server_id']
    channel_id = setting['channel_id']
    role_id = setting.get('role_id')
    channel_name = setting['channel_name']
    
    message = f"New video posted by {channel_name}: {latest_video['video_title']} https://youtu.be/{latest_video['video_id']}"
    
    if role_id:
        if role_id == "@everyone":
            message = f"@everyone {message}"
        else:
            role = discord.utils.get(guild.roles, id=role_id)
            if role:
                message = f"{role.mention} {message}"
            else:
                print(f"Role with ID {role_id} not found.")

    channel = guild.get_channel(channel_id)
    if channel:
        await channel.send(message)
    else:
        print(f"Channel with ID {channel_id} not found in server {guild.name}.")


async def check_live_status():
    for twitch_username, channels in twitch_channel_settings.items():
        url = f"https://api.twitch.tv/helix/streams?user_login={twitch_username}"
        headers = {
            'Client-ID': TWITCH_CLIENT_ID,
            'Authorization': 'Bearer ' + TWITCH_ACCESS_TOKEN
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'data' in data and data['data']:
                            for channel in channels:
                                if not channel['live']:
                                    channel['live'] = True
                                    custom_message = channel['custom_message']
                                    server_ids = channel['server_id']
                                    if isinstance(server_ids, int):
                                        server_ids = [server_ids]
                                    for server_id in server_ids:
                                        guild = bot.get_guild(server_id)
                                        if guild:
                                            role_id = channel.get('role_id')
                                            if role_id:
                                                if role_id == '@everyone':
                                                    custom_message = f"@everyone {custom_message}"
                                                else:
                                                    role = guild.get_role(int(role_id))
                                                    if role:
                                                        custom_message = f"{role.mention} {custom_message}"
                                                    else:
                                                        print(f"Role with ID {role_id} not found in server {guild.name}.")
                                            channel_id = channel['channel_id']
                                            text_channel = guild.get_channel(channel_id)
                                            if text_channel:
                                                await text_channel.send(custom_message)
                                            else:
                                                print(f"Text channel with ID {channel_id} not found in server {guild.name}.")
                                        else:
                                            print(f"Server with ID {server_id} not found.")
                        else:
                            for channel in channels:
                                channel['live'] = False
                    else:
                        print(f"Error fetching stream status for {twitch_username}: {response.status}")
            except asyncio.TimeoutError:
                print(f"Timeout occurred while fetching stream status for {twitch_username}")

# Run the bot
bot.run(TOKEN)