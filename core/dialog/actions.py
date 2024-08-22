from cryptography.fernet import Fernet

from core.db import crud
from connector.facebook.bot import Bot
import urllib.request
from variables import (
    FB_PAGE_ACCESS_TOKEN,
    TW_ENDPOINT
)
import json

fb_bot = Bot(FB_PAGE_ACCESS_TOKEN)


def pre_cipher(recipient_id, db):
    user = crud.get_user(db, recipient_id)
    key, key_state = crud.get_user_key(db, recipient_id)
    if key_state == "NEW":
        fb_bot.send_text_message(
            recipient_id,
            "I have created a new key. Keep it Safe!!"
        )
        fb_bot.send_text_message(
            recipient_id,
            key
        )
        fb_bot.send_text_message(
            recipient_id,
            "Now enter the message that you want to keep it safe."
        )
        crud.update_user_state(db, recipient_id, "WAIT_MESSAGE_CIPHER")
    elif key_state == "OLD":
        fb_bot.send_quick_replies(
            recipient_id,
            "It seems that you have an already generated key, Do you want to keep using it?",
            [
                {
                    "content_type": 'text',
                    "title": 'Yes',
                    "payload": 'yes'
                },
                {
                    "content_type": 'text',
                    "title": 'No',
                    "payload": 'no'
                }
            ]
        )
        crud.update_user_last_intent(db, recipient_id, "CONFIRM_USING_OLD_KEY")


def reset_user_state(recipient_id, db):
    crud.update_user_state(db, recipient_id, "CONTINUE")


def send_error(recipient_id, db):
    fb_bot.send_text_message(
        recipient_id,
        "Error"
    )


def greeting(recipient_id, db):
    fb_bot.send_text_message(
        recipient_id,
        "Hi, Nice to meet you."
    )
    fb_bot.send_text_message(
        recipient_id,
        "How can I help you Today?."
    )


def want_to_know_order_status(recipient_id, db):
    crud.update_user_last_intent(db, recipient_id, "want_to_know_order_status")
    fb_bot.send_text_message(
        recipient_id,
        "Sure"
    )
    crud.delete_entity(db, recipient_id, 'order_number:order_number')
    crud.delete_entity(db, recipient_id, 'wit$email:email')
    fb_bot.send_text_message(
        recipient_id,
        "What's is your email?"
    )


def getting_email(recipient_id, db, prediction):
    crud.update_user_last_intent(db, recipient_id, "getting_email")
    for entity in prediction['prediction']['entities']:
        value = prediction['prediction']['entities'][entity][0]['body']
        email = value
        crud.update_or_create_entity(db, recipient_id, entity, value)
    order_number = crud.entity_exist(db, recipient_id, 'order_number:order_number')
    if order_number:
        return check_order_status(recipient_id, db, order_number.value, email)
    else:
        fb_bot.send_text_message(
            recipient_id,
            "What's is your order number?"
        )


def getting_order_number(recipient_id, db, prediction):
    crud.update_user_last_intent(db, recipient_id, "getting_order_number")
    for entity in prediction['prediction']['entities']:
        value = prediction['prediction']['entities'][entity][0]['body']
        order_number = value
        crud.update_or_create_entity(db, recipient_id, entity, value)
    email = crud.entity_exist(db, recipient_id, 'wit$email:email')
    if email:
        return check_order_status(recipient_id, db, order_number, email.value)
    else:
        fb_bot.send_text_message(
            recipient_id,
            "What's is your email?"
        )


def check_order_status(recipient_id, db, order_number, email):
    url = TW_ENDPOINT + "/api/mobile/app_version"
    res = urllib.request.urlopen(
        urllib.request.Request(
            url=url,
            headers={'Accept': 'application/json'},
            method='GET'
        ),
        timeout=5
    )
    app_version = res.read().decode("utf-8")
    url = TW_ENDPOINT + "/en/order/currentStatus?order_number={}&email={}".format(order_number,
                                                                                  email)
    try:
        res = urllib.request.urlopen(
            urllib.request.Request(
                url=url,
                headers={
                    'Accept': 'application/json',
                    'X-Inertia': 'true',
                    'X-Inertia-Version': app_version
                },
                method='GET'
            ),
            timeout=30
        )
        order = json.loads(res.read())
        status = order['props']['order']['status']
        fb_bot.send_text_message(
            recipient_id,
            "The status of order {} for email {} is {}".format(order_number, email, status)
        )
    except Exception as err:
        fb_bot.send_text_message(
            recipient_id,
            "Sorry, I couldn't find status of order {} with email {}".format(order_number, email)
        )


def unknown_intent(recipient_id, db):
    fb_bot.send_text_message(
        recipient_id,
        "Sorry I didn't get that"
    )


def generate_key(recipient_id, db):
    user = crud.get_user(db, recipient_id)
    key = crud.create_user_key(db, recipient_id)
    fb_bot.send_text_message(
        recipient_id,
        "I have created a new key. Keep it Safe!!"
    )
    fb_bot.send_text_message(
        recipient_id,
        key.key
    )
    fb_bot.send_text_message(
        recipient_id,
        "Now enter the message that you want to keep it safe."
    )
    crud.update_user_state(db, recipient_id, "WAIT_MESSAGE_CIPHER")


def confirm_pre_cipher(recipient_id, db):
    user = crud.get_user(db, recipient_id)
    fb_bot.send_text_message(
        recipient_id,
        "Great. Now enter the message that you want to keep safe."
    )
    crud.update_user_state(db, recipient_id, "WAIT_MESSAGE_CIPHER")


def confirm_pre_decipher(recipient_id, db):
    fb_bot.send_text_message(
        recipient_id,
        "Now enter the message that you want to decrypt."
    )
    crud.update_user_state(db, recipient_id, "WAIT_MESSAGE_DECIFER")


def cipher(message, recipient_id, db):
    key, _ = crud.get_user_key(db, recipient_id)
    key = key.encode()
    message = message.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(message).decode()
    fb_bot.send_text_message(
        recipient_id,
        "This is the encrypted message. It'll only be decrypted using the key that you used"
    )
    fb_bot.send_text_message(
        recipient_id,
        encrypted_message
    )
    fb_bot.send_quick_replies(
        recipient_id,
        "Do you want to encrypt anything else?",
        [
            {
                "content_type": 'text',
                "title": 'Yes',
                "payload": 'yes'
            },
            {
                "content_type": 'text',
                "title": 'No',
                "payload": 'no'
            }
        ]
    )
    crud.update_user_last_intent(db, recipient_id, "CONFIRM_CIPHER_AGAIN")
    crud.update_user_state(db, recipient_id, "CONTINUE")


def pre_decipher_key(recipient_id, db):
    user = crud.get_user(db, recipient_id)
    fb_bot.send_text_message(
        recipient_id,
        "Please enter the key that has been shared with you to decrypt the message"
    )
    crud.update_user_state(db, recipient_id, "WAIT_KEY")


def pre_decipher_message(message, recipient_id, db):
    user = crud.get_user(db, recipient_id)
    try:
        crud.update_user_last_used_key(db, recipient_id, message)
        fb_bot.send_text_message(
            recipient_id,
            "Now enter the message that you want to decrypt."
        )
        crud.update_user_state(db, recipient_id, "WAIT_MESSAGE_DECIFER")
    except Exception:
        fb_bot.send_text_message(
            recipient_id,
            "The key you've entered is not valid. Please make sure you have the correct key"
        )


def decipher(message, recipient_id, db):
    try:
        user = crud.get_user(db, recipient_id)
        key = user.last_used_key
        key = key.encode()
        message = message.encode()
        f = Fernet(key)
        decrypted_message = f.decrypt(message)
        fb_bot.send_text_message(
            recipient_id,
            "This is the decrypted message. Keep it safe and delete after you read it."
        )
        fb_bot.send_text_message(
            recipient_id,
            decrypted_message.decode()
        )
        fb_bot.send_quick_replies(
            recipient_id,
            "Do you want to decrypt anything else?",
            [
                {
                    "content_type": 'text',
                    "title": 'Yes',
                    "payload": 'yes'
                },
                {
                    "content_type": 'text',
                    "title": 'No',
                    "payload": 'no'
                }
            ]
        )
        crud.update_user_last_intent(db, recipient_id, "CONFIRM_DECIPHER_AGAIN")
        crud.update_user_state(db, recipient_id, "CONTINUE")
    except Exception:
        fb_bot.send_text_message(
            recipient_id,
            "The encrypted message you've entered is not valid. Please make sure you have the correct message"
        )
