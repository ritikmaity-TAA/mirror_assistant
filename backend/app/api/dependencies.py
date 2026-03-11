from fastapi import Depends, HTTPException, status
from db.supabase import get_db
from supabase import Client

def get_supabase_client(db: Client = Depends(get_db)):
    return db
