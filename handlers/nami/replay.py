from aiohttp import web
import aiofiles, os

# get
async def view_replay(request):
    replay_id = request.match_info['replay_id']

    if not os.path.isfile(f'data/replays/{replay_id}'):
        return web.Response(text='replay not found lol')
    
    return web.FileResponse(path=f'data/replays/{replay_id}')


# post
# TODO: add verification stuff maybe? so ppl cant just upload shit here
async def upload_replay(request):
    replay_id = request.rel_url.query['replayID']
    body = await request.content.read()
    replay = body[191:][:-48] # lol

    if os.path.isfile(f'data/replays/{replay_id}.odr'):
        # if file odi exist we just return 
        return web.Response(text='lol what no')

    # if shit is fayn then just save the file
    async with aiofiles.open(f'data/replays/{replay_id}.odr', 'wb') as file:
        await file.write(replay)

    return web.Response(text='ok sure')



