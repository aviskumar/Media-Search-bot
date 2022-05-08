import asyncio
import os
import subprocess
import sys
import traceback
from io import StringIO

from info import ADMINS
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton
)


logger = logging.getLogger(__name__)


async def apexec(code, client, message):
    app = client
    chat = message.chat.id
    m = message
    rm = reply = message.reply_to_message
    exec(
        f"async def __aexec(client, message): "
        + "".join(f"\n {l}" for l in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)


@Client.on_message(
    filters.user(ADMINS)
    & filters.command(["eval", "peval"])
    & ~filters.edited
)
async def _eval(client, m: Message):
    try:
        cmd = m.text.split(maxsplit=1)[1]
    except IndexError:
        return await m.reply_text("Give Command as well :)", quote=True)

    status = await m.reply_text("`Processing...`", quote=True)
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    redirected_error = sys.stderr = StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await apexec(cmd, client, m)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"

    final_output = f"**>**  `{cmd}` \n\n**>>**  `{evaluation.strip()}`"
    if len(final_output) > 4096:
        filename = "eval_pyro.txt"
        out =str(final_output).replace("`", "").replace("*", "").replace("_", "")
        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(out)
        await m.reply_document(
            document=filename,
            caption=f"**>>** `{cmd[:300]} \n ...`",
            disable_notification=True
        )
        os.remove(filename)
        await status.delete()
    else:
        await status.edit(str(final_output))


# ~~~~~~~~~~~~~~~ Bash ~~~~~~~~~~~~~~~~~~~~


async def bash(cmd):
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    err = stderr.decode(errors='replace').strip() or None
    out = stdout.decode(errors='replace').strip()
    return out, err


@Client.on_message(
    filters.user(ADMINS)
    & filters.command(["bash", "exec"])
    & ~filters.edited
)
async def _bash(client: Client, m: Message):
    try:
        cmd = m.text.split(maxsplit=1)[1]
    except IndexError:
        return await m.reply_text("Give some cmd too", quote=True)
    msg_ = await m.reply_text("`Processing ...`", quote=True)
    out, err = await bash(cmd)
    xx = f"**u:~$**  `{cmd}`\n\n"
    if err:
        xx += f"**Error:**  `{err}`\n\n"
    if out:
        _k = out.split("\n")
        o_ = "\n".join(_k)
        xx += f"`{o_}`"
    if not err and not out:
        xx += "**u:~$**  `Success`"
    if len(xx) > 4096:
        out = xx.replace("`", "").replace("*", "").replace("_", "")
        with open("bash_.txt", "w+", encoding="utf8") as out_file:
            out_file.write(str(out))
        await m.reply_document(
            "bash_.txt",
            caption=f"**CMD :**\n`{cmd[:600]}` \n ....",
        )
        await msg_.delete()
        os.remove("bash_.txt")
    else:
        await msg_.edit(xx)
