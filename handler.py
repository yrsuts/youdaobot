from telegram.ext import CallbackContext
from telegram.ext.dispatcher import Update, run_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.utils.promise import Promise
from youdao import Youdao
from time import sleep
import os
import pickle
import gc
import re


query_path = './queries.pkl'


def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        '欢迎使用有道词典，发送任意单词继续。'
    )


def clear(update: Update, context: CallbackContext):
    bot = context.bot
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    delete_message(bot, chat_id, message_id, delay=0.5)

    all_queries = [query for query in gen_query_data(query_path)]
    for query in gen_query_data(query_path):
        if query[0] == chat_id:
            message_id = query[1]
            delete_message(bot, chat_id, message_id)
            all_queries.remove(query)
    with open(query_path, 'wb') as f:
        _ = [pickle.dump(query, f) for query in all_queries]
    gc.collect()


def youdao(update: Update, context: CallbackContext):
    bot = context.bot
    update_message = update.message
    chat_id = update_message.chat_id
    message_id = update_message.message_id
    delete_message(bot, chat_id, message_id, delay=3.0)
    try:
        query = update_message.text
    except Exception:
        query = None
    if query:
        youdao = Youdao(query)
        if not youdao.iserror:
            data = parse_youdao(youdao)
            if data[2] and data[3]:
                option = [1, 2]
            elif data[2]:
                option = [1]
            elif data[3]:
                option = [2]
            else:
                option = None

            text = '*%s*\n\n' % query + ''.join(data[:2])
            message = send_message(bot, chat_id=chat_id, text=text,
                                   parse_mode='markdown',
                                   reply_markup=menu_keyboard(option))
        else:
            data = [''] * 4
            error_block = youdao.get_error_block()
            if error_block:
                rec = error_block.get_text()
                rec = re.sub(r"\s{2,}", '\n', rec).strip()
                text = rec
            else:
                text = 'Sorry, no result.'
            message = send_message(bot, chat_id=chat_id, text=text,
                                   reply_markup=menu_keyboard(None))
        data_to_save = [chat_id, message, query] + data
        save_data(data_to_save)
    else:
        message = \
            send_message(bot, chat_id=chat_id, text='Sorry, try again.')
        delete_message(bot, chat_id, message, delay=5.0)


def auto_clear(context):
    bot = context.bot
    all_queries = [query for query in gen_query_data(query_path)]
    for query in gen_query_data(query_path):
        chat_id = query[0]
        message_id = query[1]
        delete_message(bot, chat_id, message_id)
    all_queries.clear()
    with open(query_path, 'wb') as f:
        _ = [pickle.dump(query, f) for query in all_queries]
    gc.collect()


def on_menu_update(update: Update, context: CallbackContext):
    bot = context.bot
    callback_query = update.callback_query
    query_message = callback_query.message
    chat_id = query_message.chat_id
    message_id = query_message.message_id
    target_query = []
    for query in gen_query_data(query_path):
        if query[0] == chat_id and query[1] == message_id:
            target_query = query
            break
    callback_data = callback_query['data']
    word = target_query[2]
    prons = target_query[3]
    trans = target_query[4]
    phrases = target_query[5]
    examples = target_query[6]
    text = '*%s*\n\n' % word
    option = []
    if callback_data == 'get_basicinfo':
        if not prons:
            prons = ''
        text += prons + trans
        if phrases and examples:
            option = [1, 2]
        elif phrases:
            option = [1]
        elif examples:
            option = [2]
    elif callback_data == 'get_phrases':
        text += phrases
        option = [0, 2] if examples else [0]
    elif callback_data == 'get_examples':
        text += examples
        option = [0, 1] if phrases else [0]
    elif callback_data == 'delete_query':
        delete_message(bot, chat_id, message_id)
        all_queries = [query for query in gen_query_data(query_path)]
        for data in gen_query_data(query_path):
            if data[0] == chat_id and data[1] == message_id:
                all_queries.remove(data)
        with open(query_path, 'wb') as f:
            _ = [pickle.dump(query, f) for query in all_queries]

    if not callback_data == 'delete_query':
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=menu_keyboard(option=option),
            parse_mode='markdown'
        )


def menu_keyboard(option):
    keyboards = [
        [InlineKeyboardButton('释义', callback_data='get_basicinfo'),
            InlineKeyboardButton('词组', callback_data='get_phrases'),
            InlineKeyboardButton('例句', callback_data='get_examples')],
        [InlineKeyboardButton('删除此条', callback_data='delete_query')],
    ]
    if option:
        return InlineKeyboardMarkup(
            [[keyboards[0][i] for i in option], [keyboards[1][0]]])
    else:
        return InlineKeyboardMarkup([[keyboards[1][0]]])


def parse_youdao(youdao):
    parsed_data = [''] * 4
    prons, trans, phrases, examples = \
        youdao.get_prons(), youdao.get_trans(), youdao.get_phrases(), \
        youdao.get_examples()
    if prons:
        text = '\[*Pronunciations*]\n' + '\n'.join(prons) + '\n\n'
        parsed_data[0] = text
    if trans:
        text = '\[*Translations*]\n' + '\n'.join(trans) + '\n\n'
        parsed_data[1] = text
    if phrases:
        text = '\[*Phrases*]\n\n'
        for item in phrases:
            text += '{}    {}\n'.format(item[0], item[1])
        parsed_data[2] = text
    if examples:
        text = '\[*Examples*]\n\n'
        for item in examples:
            text += '{}\n    {}\n\n'.format(item[0], item[1])
        parsed_data[3] = text
    return parsed_data


def save_data(data):
    if isinstance(data[1], Promise):
        data[1] = data[1].result().message_id
    if os.path.exists(query_path):
        with open(query_path, 'ab') as f:
            pickle.dump(data, f)
    else:
        with open(query_path, 'wb') as f:
            _ = [pickle.dump(data, f)]


@run_async
def delete_message(bot, chat_id, message_id, delay=0.0):
    if delay:
        sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass


@run_async
def send_message(bot, **kwargs):
    chat_id = kwargs['chat_id']
    text = kwargs['text']
    reply_markup, parse_mode = None, None
    if 'reply_markup' in kwargs.keys():
        reply_markup = kwargs['reply_markup']
    if 'parse_mode' in kwargs.keys():
        parse_mode = kwargs['parse_mode']

    message = bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup
    )
    return message


def gen_query_data(query_path):
    try:
        with open(query_path, 'rb') as f:
            while True:
                try:
                    query_data = pickle.load(f)
                    yield query_data
                except Exception:
                    raise StopIteration
    except Exception:
        raise StopIteration
