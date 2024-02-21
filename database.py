import aiosqlite
import time
import json

from utils import is_today


class Database:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        self.db = None
        
    async def connect(self) -> None:
        self.db = await aiosqlite.connect(self.db_name)
    
    async def create_tables(self) -> None:
        sql = """CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY, 
            notification_time TEXT, 
            join_date INTEGER)"""
        await self.db.execute(sql)
        
        sql = """CREATE TABLE IF NOT EXISTS notes(
            note_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER,
            headache BOOLEAN NOT NULL CHECK (headache IN (0, 1)),
            use_medicine BOOLEAN NOT NULL CHECK (use_medicine IN (0, 1)),
            medicine_list TEXT,
            note_date INTEGER)"""
        await self.db.execute(sql)
        
        sql = """CREATE TABLE IF NOT EXISTS notifications(
            user_id INTEGER PRIMARY KEY, 
            date INTEGER)"""
        await self.db.execute(sql)
        
        await self.db.commit()
    
    async def delete_notification(self, user_id: int) -> None:
        sql = "DELETE FROM notifications WHERE user_id = ?;"
        await self.db.execute(sql, (user_id, ))
        await self.db.commit()
    
    async def get_notifications(self) -> list:
        sql = "SELECT user_id, date FROM notifications"
        cursor = await self.db.execute(sql)
        
        return await cursor.fetchall()
    
    async def get_user_notification(self, user_id: int) -> list:
        sql = "SELECT user_id, date FROM notifications WHERE user_id = ?"
        cursor = await self.db.execute(sql, (user_id, ))
        
        return await cursor.fetchone()
        
    async def insert_notification(self, user_id: int, date: int) -> None:
        sql = "INSERT OR REPLACE INTO notifications(user_id, date) VALUES(?, ?)"
        
        await self.db.execute(sql, (user_id, date))
        await self.db.commit()
        
    async def insert_user(self, user_id: int) -> None:
        sql = "INSERT INTO users VALUES(?, ?, ?)"
        
        await self.db.execute(sql, (user_id, "19:00", time.time()))
        await self.db.commit()
    
    async def get_user(self, user_id: int) -> list:
        sql = "SELECT user_id, notification_time, join_date FROM users WHERE user_id = ?"
        cursor = await self.db.execute(sql, (user_id, ))
        
        return await cursor.fetchone()
    
    async def update_notification_time(self, user_id: int, notification_time: str) -> None:
        sql = "UPDATE users SET notification_time = ? WHERE user_id = ?"
        
        await self.db.execute(sql, (notification_time, user_id))
        await self.db.commit()

    async def insert_note(self, user_id: int, headache: bool, use_medicine: bool, medicine_list: list) -> None:
        if medicine_list is None:
            medicine_list = []
        
        user_notes = await self.get_user_notes(user_id)
        
        for note in user_notes:
            if is_today(int(note[3])):
                medicine_list += json.loads(note[2])
                
                if bool(note[0]):
                    headache = True
                
                if len(medicine_list) != 0:
                    use_medicine = True
                    
                await self.update_user_note(user_id, headache, use_medicine, medicine_list)
                
                return
                
        sql = "INSERT INTO notes(user_id, headache, use_medicine, medicine_list, note_date) VALUES(?, ?, ?, ?, ?)"
        
        await self.db.execute(sql, (user_id, headache, use_medicine, json.dumps(medicine_list), time.time()))
        await self.db.commit()
    
    async def update_user_note(self, user_id: int, headache: bool, use_medicine: bool, medicine_list: list) -> None:
        sql = "UPDATE notes SET headache = ?, use_medicine = ?, medicine_list = ? WHERE user_id = ?"
        
        await self.db.execute(sql, (headache, use_medicine, json.dumps(medicine_list), user_id))
        await self.db.commit()
        
    async def get_user_notes(self, user_id: int) -> list:
        sql = "SELECT headache, use_medicine, medicine_list, note_date FROM notes WHERE user_id = ?"
        cursor = await self.db.execute(sql, (user_id, ))
        
        return await cursor.fetchall()