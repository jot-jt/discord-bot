import sqlite3

import os
from dotenv import load_dotenv
load_dotenv()
DB_LOC = os.getenv('DB_LOC')


class Database():
    def __init__(self):
        self.con = sqlite3.connect(DB_LOC)
        self.cur = self.con.cursor()
        print('Connected to database.')

    def __unlock_vocab(self, user_id, set_id, new_level):
        """
        Updates the [user-to-vocab] table with vocabulary associated with
        a set level for a user.
        Arguments:
            user_id: Discord user id
            set_id: desired set to add
            new_level: specific level from the set to add to user
        """
        self.cur.execute(
            "SELECT vocab_id FROM 'set-to-vocab' WHERE set_id = ? AND level = ?", [set_id, new_level])
        new_vocab_ids = tuple(self.cur.fetchall())
        for entry in new_vocab_ids:
            vocab_id = entry[0]
            self.cur.execute(
                "INSERT INTO 'user-to-vocab' (user_id, vocab_id, times_correct, times_shown, familiarity) VALUES (?, ?, 0, 0, 0)", (user_id, vocab_id)
            )
        self.con.commit()

    def unlock_set(self, user_id, set_id):
        """
        Unlocks a specific set for a user.

        A user id and set id will be inserted into the [unlocked-sets] table.
        All Level 1 vocab related to the set will become associated with
        the user id in the [user-to-vocab] table.

        Arguments:
            user_id: Discord user id
            set_id: desired set to unlock
        """
        self.cur.execute(
            "INSERT INTO 'unlocked-sets' (user_id, set_id, current_level) VALUES (?, ?, 1);",
            (user_id, set_id))
        self.__unlock_vocab(user_id, set_id, 1)
        self.con.commit()

    def level_up(self, user_id, set_id):
        """
        Levels up the user's set.

        The user's level for this specific set is incremented in the 
        [unlocked-sets] table. All vocab related to that specific set level
        is associated with the user in the [user-to-vocab] table.

        Arguments:
            user_id: Discord user id
            set_id: desired set to level up
        """
        self.cur.execute(
            "UPDATE 'unlocked-sets' SET current_level = current_level + 1 WHERE user_id = ?;",
            [user_id])
        self.cur.execute(
            "SELECT current_level FROM 'unlocked-sets' WHERE user_id = ? AND set_id = ?", [user_id, set_id])
        new_level = self.cur.fetchall()[0][0]
        self.__unlock_vocab(user_id, set_id, new_level)
        self.con.commit()

# self.cur.execute(
#     "SELECT char_native FROM 'vocab' WHERE vocab_id IN ( \
#         SELECT vocab_id FROM 'set-to-vocab' WHERE set_id = ? AND level = 1)", [set_id])
# test = self.cur.fetchall()
# print(test)


db = Database()
# db.unlock_set(123, 2)
db.level_up(123, 2)
