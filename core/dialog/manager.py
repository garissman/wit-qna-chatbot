import random

from core.nlp.engine import NLPEngine
from core.db import crud
from core.dialog import actions

from connector.facebook.bot import Bot

from variables import (
    FB_PAGE_ACCESS_TOKEN
)

fb_bot = Bot(FB_PAGE_ACCESS_TOKEN)


class DialogManager:
    def __init__(self):
        self.engine = NLPEngine()

    def process_message(self, message, recipient_id, db):
        try:
            user_state = crud.get_user_state(db, recipient_id)
            if user_state == "CONTINUE":
                intent = self.engine.predict(message)
                self.get_response(intent, recipient_id, db)
            elif user_state == "WAIT_MESSAGE_CIPHER":
                actions.cipher(message, recipient_id, db)
                actions.reset_user_state(recipient_id, db)
            elif user_state == "WAIT_MESSAGE_DECIFER":
                actions.decipher(message, recipient_id, db)
                actions.reset_user_state(recipient_id, db)
            elif user_state == "WAIT_KEY":
                actions.confirm_pre_decipher(recipient_id, db)
        except Exception as err:
            actions.send_error(recipient_id, db)

    def get_response(self, intent, recipient_id, db):
        last_intent = crud.get_user_last_intent(db, recipient_id)
        current_intent = intent['intent']
        if current_intent == "cipher":
            actions.pre_cipher(recipient_id, db)
        elif current_intent == "decipher":
            actions.pre_decipher_key(recipient_id, db)
        elif current_intent == "new_key":
            actions.generate_key(recipient_id, db)
        elif current_intent == "yes":
            if last_intent == "CONFIRM_USING_OLD_KEY":
                actions.confirm_pre_cipher(recipient_id, db)
            elif last_intent == "CONFIRM_CIPHER_AGAIN":
                actions.confirm_pre_cipher(recipient_id, db)
            elif last_intent == "CONFIRM_DECIPHER_AGAIN":
                actions.pre_decipher_message(recipient_id, db)
        elif current_intent == "no":
            if last_intent == "CONFIRM_USING_OLD_KEY":
                actions.generate_key(recipient_id, db)
            elif last_intent == "CONFIRM_CIPHER_AGAIN":
                return "Great. Let me know if you need anything."
            elif last_intent == "CONFIRM_DECIPHER_AGAIN":
                return "Great. Let me know if you need anything."
        elif current_intent == "greeting":
            return actions.greeting(recipient_id, db)
        elif current_intent == "want_to_know_order_status":
            return actions.want_to_know_order_status(recipient_id, db)
        elif current_intent == "getting_email":
            return actions.getting_email(recipient_id, db, intent)
        elif current_intent == "getting_order_number":
            return actions.getting_order_number(recipient_id, db, intent)
        else:
            return actions.unknown_intent(recipient_id, db)
