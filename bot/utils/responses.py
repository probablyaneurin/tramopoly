from discord import Embed, Interaction, File, TextChannel, MISSING, Message
from discord.interactions import Interaction as Interaction2
from discord.ui import View
from utils.embeds import embed_complaint

async def complain(ctx: Interaction | TextChannel | Message, title: str, message: str):
    # defer as ephermal
    if (isinstance(ctx, Interaction) or isinstance(ctx, Interaction2)) and not ctx.response.is_done():
        await ctx.response.defer(ephemeral=True)
    # create error colour and send
    await sendMessage(ctx, None, embed_complaint(title, message))

async def sendMessage(ctx: Interaction | TextChannel | Message, content: str = None, *embeds: tuple[Embed, list[File]], view:View = MISSING) -> Message | None:
    # defer as non ephermal
    if (isinstance(ctx, Interaction) or isinstance(ctx, Interaction2)) and not ctx.response.is_done():
        await ctx.response.defer()
    all_embeds = []
    files = []
    # gather all the stuff
    for item in embeds:
        all_embeds.append(item[0])
        files.extend(item[1])
    # send the embed!
    if isinstance(ctx, TextChannel):
        return await ctx.send(
            content=content,
            embeds=all_embeds,
            files=files,
            view=view
        )
    elif isinstance(ctx, Message):
        return await ctx.reply(
            content=content,
            embeds=all_embeds,
            files=files,
            view=view
        )       
    else:
        return await ctx.followup.send(
            content=content,
            embeds=all_embeds,
            files=files,
            view=view
        )  
