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

    def current_level(self, user_id, set_id):
        """
        Returns the set level of the set for user

        Arguments:
            user_id: Discord user id
            set_id: desired set to get current level from
        Returns:
            int representing current level
        Raises:
            RuntimeError if user-set pair doesn't exist
        """
        self.cur.execute(
            "SELECT current_level FROM 'unlocked-sets' WHERE user_id = ? AND set_id = ?", [user_id, set_id])
        try:
            return self.cur.fetchone()[0]
        except:
            raise RuntimeError(
                f'set_id {set_id} does not belong to user {user_id}')

    def active_set(self, user_id):
        """
        Returns the set id of the user's active set.

        Arguments:
            user_id: Discord user id
        Returns:
            Int representing set id
        Raises:
            RuntimeError if user doesn't exist
        """
        self.cur.execute(
            "SELECT active_set_id FROM 'users' WHERE user_id = ?", [user_id])
        try:
            return self.cur.fetchall()[0][0]
        except:
            raise RuntimeError(
                f'User {user_id} does not exist')

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
        new_level = self.current_level(user_id, set_id)
        self.__unlock_vocab(user_id, set_id, new_level)
        self.con.commit()

    def player_familiarities(self, user_id, set_id):
        """
        Returns all vocab id's and familiarity pairs for all unlocked levels of
        the specified set for the user.

        Arguments:
            user_id: Discord user id
            set_id: Desired set id to pull the familiarities from. If None, uses
                the user's active set.
        Returns:
            List of all vocab id and familiarity pairs in the specified
            set for the user.
        """
        max_level = self.current_level(user_id, set_id)
        print(max_level)
        self.cur.execute("SELECT vocab_id, familiarity FROM 'user-to-vocab' WHERE user_id = ? AND vocab_id IN ( \
            SELECT vocab_id FROM 'set-to-vocab' WHERE set_id = ? AND level <= ?)", [user_id, set_id, max_level])
        return self.cur.fetchall()

# self.cur.execute(
#     "SELECT char_native FROM 'vocab' WHERE vocab_id IN ( \
#         SELECT vocab_id FROM 'set-to-vocab' WHERE set_id = ? AND level = 1)", [set_id])
# test = self.cur.fetchall()
# print(test)


db = Database()
# db.unlock_set(123, 2)
print(db.player_familiarities(208353857992916992, 2))
