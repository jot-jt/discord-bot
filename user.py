import sqlite3
import json
conn = sqlite3.connect('data/data.db')

c = conn.cursor()

with open('data/users.json', 'r', encoding='utf-8') as f:
    users = json.load(f)

list = []
for user, value in users.items():
    for vocab, value2 in value['sets']['hiragana']['vocab'].items():
        c.execute("SELECT vocab_id FROM vocab WHERE char_native = ?;", vocab)
        vocab_id = c.fetchone()
        print(vocab_id)
        tuple = (int(user), vocab_id[0], value2['times_correct'],
                 value2['times_asked'], value2['familiarity'])
        list.append(tuple)
c.executemany(
    f"INSERT INTO 'user-to-vocab'(user_id,vocab_id,times_correct,times_shown,familiarity) VALUES(?,?,?,?,?)", list)
conn.commit()
