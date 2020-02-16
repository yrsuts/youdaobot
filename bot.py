#! /home/cooper/venv/bin/python
from telegram.ext import Updater, CallbackQueryHandler
from telegram.ext import CommandHandler, MessageHandler, Filters
from datetime import time
import handler


def main():
    TOKEN = 'YOUR KEY'
    REQUEST_KWARGS = {'proxy_url': 'http://127.0.0.1:8118'}
    updater = Updater(TOKEN, use_context=True, request_kwargs=REQUEST_KWARGS)
    updater.dispatcher.add_handler(
        CommandHandler(
            'start', handler.start,
        )
    )
    updater.dispatcher.add_handler(
        CommandHandler(
            'clear', handler.clear,
        )
    )
    updater.dispatcher.add_handler(
        CallbackQueryHandler(
            handler.on_menu_update,
        )
    )
    updater.dispatcher.add_handler(
        MessageHandler(
            Filters.all, handler.youdao
        )
    )
    job = updater.job_queue
    job.run_daily(handler.auto_clear, time=time(22, 12, 0, 0))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
