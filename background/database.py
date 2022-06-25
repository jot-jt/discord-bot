import sqlite3
import numpy as np


import os
from dotenv import load_dotenv
load_dotenv()
DB_LOC = os.getenv('DB_LOC')


class Database():
    def __init__(self):
        self.con = sqlite3.connect(DB_LOC)
        self.cur = self.con.cursor()
        print('Connected to database.')

    def user_exists(self, user_id: int):
        """
        Returns a bool of whether the user exists in the database.
        """
        self.cur.execute(
            "SELECT user_id FROM 'users' WHERE user_id = ?", [user_id])
        return self.cur.fetchone() != None

    def current_level(self, user_id: int, set_id: int):
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

    def active_set_id(self, user_id: int):
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

    def familiarity(self, user_id, vocab_id):
        """
        Returns an int of the user's familiarity level of the vocab.

        Raises:
            RuntimeError if user_id, vocab_id pair is invalid
        """
        self.cur.execute("SELECT familiarity FROM 'user-to-vocab' \
            WHERE user_id = ? AND vocab_id = ?", [user_id, vocab_id])
        try:
            return self.cur.fetchone()[0]
        except:
            raise RuntimeError(
                f'Cannot find {vocab_id} for user {user_id}')

    def __unlock_vocab(self, user_id: int, set_id: int, new_level: int):
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

    def unlock_set(self, user_id: int, set_id: int):
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

    def check_level_up(self, user_id: int):
        """
        Checks if the user can level up their active set, and levels up if
        conditions are met.

        A player can level up if all words in the active set are familiarity
        5 or higher.

        Arguments:
            user_id: Discord user id
        Returns:
            Pair of (int, bool) where
            - Int of player's new level if they leveled up, or None
            - Bool of whether user has leveled up
        """
        def level_up(user_id: int, set_id: int):
            """
            Levels up the user's set.

            The user's level for this specific set is incremented in the
            [unlocked-sets] table. All vocab related to that specific set level
            is associated with the user in the [user-to-vocab] table.

            Arguments:
                user_id: Discord user id
                set_id: desired set to level up
            Returns:
                int of player's new level for this set
            """
            self.cur.execute(
                "UPDATE 'unlocked-sets' SET current_level = current_level + 1 WHERE user_id = ?;",
                [user_id])
            new_level = self.current_level(user_id, set_id)
            self.__unlock_vocab(user_id, set_id, new_level)
            self.con.commit()
            return new_level

        active_set = self.active_set_id(user_id)
        self.cur.execute(
            "SELECT familiarity FROM 'user-to-vocab' WHERE user_id = ? AND familiarity < 5 AND vocab_id IN ( \
                SELECT vocab_id FROM 'set-to-vocab' WHERE set_id = ?)", [user_id, active_set]
        )
        can_level_up = len(self.cur.fetchall()) == 0
        new_level = None
        if can_level_up:
            new_level = level_up(user_id, active_set)
        return new_level, can_level_up

    def create_user(self, user_id: int):
        """
        Adds a user into the database.

        Arguments:
            user_id: Discord user id
        """
        self.cur.execute(
            "INSERT INTO 'users'(user_id, active_set_id) VALUES (?, 1);",
            [user_id])
        self.unlock_set(user_id, 1)
        self.con.commit()

    def player_vocab(self, user_id: int, familiarity_level, set_id: int = None):
        """
        Returns any matching vocab ids given the set and user familiarity.

        Arguments:
            user_id: Discord user id
            familiarity_level: User familiarity of vocab. Between 0 and 9,
                inclusive.
            set_id: Desired set id to pull the familiarities from. If None, uses
                the user's active set.
        Returns:
            List of 1-tuples of vocab ids in the specified set for the user.
        """
        if set_id == None:
            set_id = self.active_set_id(user_id)
        max_level = self.current_level(user_id, set_id)
        self.cur.execute("SELECT vocab_id FROM 'user-to-vocab' \
            WHERE user_id = ? AND familiarity = ? AND vocab_id IN ( \
            SELECT vocab_id FROM 'set-to-vocab' WHERE set_id = ? AND level <= ?)",
                         [user_id, familiarity_level, set_id, max_level])
        return self.cur.fetchall()

    def as_defn_pair(self, vocab_id: int):
        """
        Returns a pair of the native character and its romanization

        Arguments:
            vocab_id: vocabulary id
        Returns:
            Pair of (native character, romanization)
        """
        self.cur.execute("SELECT char_native, romanization FROM 'vocab' \
            WHERE vocab_id = ?", [vocab_id])
        return self.cur.fetchone()

    def pronunciation(self, vocab_id: int):
        """
        Returns a string with the pronunciation of vocab_id.
        """
        self.cur.execute("SELECT pronunciation FROM 'vocab' \
            WHERE vocab_id = ?", [vocab_id])
        return self.cur.fetchone()[0]

    def response_update(self, user_id: int, vocab_id: int, correct: bool):
        """
        Updates the database based on whether the user answered the question
        correctly.

        Arguments:
            user_id: Discord user id
            vocab_id: vocab that was asked to user
            correct: whether the user answered correctly or not
        """
        familiarity = self.familiarity(user_id, vocab_id)
        if correct:
            correct_int = 1
            familiarity = min(familiarity + 1, 9)
        else:
            correct_int = 0
            familiarity = max(familiarity - 1, 0)
        self.cur.execute(
            "UPDATE 'user-to-vocab' SET times_correct = times_correct + ?, \
            times_shown = times_shown + 1, familiarity = ? \
            WHERE user_id = ? AND vocab_id = ?;",
            [correct_int, familiarity, user_id, vocab_id])
        self.con.commit()

    def user_sets(self, user_id: int):
        """
        Gives the user's available sets in the format of
        (set id, set name, current level, total level)

        Arguments:
            user_id: Discord user id
        Returns:
            A list of all of the user's sets, where each entry is a
            int-str-int-int 4-tuple.
        """
        self.cur.execute("SELECT set_id, name, current_level, total_levels FROM \
            'unlocked-sets' INNER JOIN 'sets' USING (set_id) WHERE \
            user_id = ?", [user_id])
        return self.cur.fetchall()

    def total_level(self, user_id: int) -> int:
        """
        Returns the total level of the user.
        The total level is the sum of all of the user's current set levels.

        Arguments:
            user_id: Discord user id
        """
        self.cur.execute("SELECT SUM(current_level) FROM 'unlocked-sets' \
            WHERE user_id = ?", [user_id])
        return self.cur.fetchone()[0]

    def total_vocab(self, user_id: int) -> int:
        """
        Returns the total vocabulary discovered by the user across all sets.

        Arguments:
            user_id: Discord user id
        """
        self.cur.execute("SELECT COUNT(vocab_id) FROM 'user-to-vocab' \
            WHERE user_id = ?", [user_id])
        return self.cur.fetchone()[0]

    def total_times_played(self, user_id: int) -> int:
        """
        Returns the total number of sessions played by the user across all sets.

        Arguments:
            user_id: Discord user id
        """
        self.cur.execute("SELECT SUM(times_shown) FROM 'user-to-vocab' \
            WHERE user_id = ?", [user_id])
        return self.cur.fetchone()[0]

    def total_times_correct(self, user_id: int) -> int:
        """
        Returns the total number of correct answers by the user across all sets.

        Arguments:
            user_id: Discord user id
        """
        self.cur.execute("SELECT SUM(times_correct) FROM 'user-to-vocab' \
            WHERE user_id = ?", [user_id])
        return self.cur.fetchone()[0]
