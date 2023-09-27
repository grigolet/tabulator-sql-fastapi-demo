from fastapi import FastAPI, Request, Query, Depends, Body, HTTPException
from fastapi.templating import Jinja2Templates
from typing import Annotated, Any
import sqlite3
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    db_path: Path = "app/db.sqlite"


async def get_settings():
    yield Settings()


async def get_db(settings: Annotated[Settings, Depends(get_settings)]):
    conn = sqlite3.connect(settings.db_path)
    try:
        yield conn
    finally:
        conn.close()


app = FastAPI()
templates = Jinja2Templates('app/templates')


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse('index.html', context={'request': request})


@app.get("/alarm")
async def alarm(
    request: Request,
    id: Annotated[int, Query()],
    db: sqlite3.Connection = Depends(get_db),
):
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("SELECT * FROM alarms WHERE id = ?", (id, ))
    alarm = cursor.fetchone()
    return templates.TemplateResponse('alarm.html', context={'request': request, 'alarm': alarm})


@app.post("/alarms")
async def home(
    request: Request,
    page: Annotated[int, Body(ge=1)] = 1,
    size: Annotated[int, Body(lt=100)] = 100,
    db: sqlite3.Connection = Depends(get_db), 
    filter: Annotated[list[dict], Body()] = None
):
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    where_clauses = []
    where_query = ""
    placeholder_values = []
    if len(filter):  # Apply a WHERE clause in the SQL query
        where_query += " WHERE "
        for filter_obj in filter:
            field, type, value = filter_obj['field'], filter_obj['type'], filter_obj['value']
            # Check that the filter field can be trusted and exists as a column in our table
            cursor.execute("select name from PRAGMA_TABLE_INFO('alarms') where name = ?", (field,))
            column_field = cursor.fetchone()
            operand = type.upper()
            if column_field:  # the filter field exists as a column
                identifier = column_field['name']
                match (operand, identifier):
                    case 'LIKE', _: # if using like as tabulator mention, add wildcards
                        placeholder_value = f'%{value}%'
                    case ('=', 'timestamp'):
                        # convert the timestamp identifier column to a date
                        column_field 
                        placeholder_value = value
                        identifier = f"strftime('%Y-%m-%d', {column_field['name']})"
                    case ('=', _):  # this is mostly used for numerical, categorical or date filtering
                        placeholder_value = value

                    case other:  # the operand is not supported, return an HTTP 400 response
                        raise HTTPException(status_code=400, detail=f"Filter type {operand} not supported.")
    
                where_clauses.append(f"{identifier} {operand} ?")
                placeholder_values.append(placeholder_value)
        where_query += " AND ".join(where_clauses)
                    
    offset = (page - 1) * size
    cursor.execute("SELECT COUNT(id) as count FROM alarms")
    n_rows = cursor.fetchone()['count']
    n_pages = n_rows // size if n_rows % size == 0 else n_rows // size + 1
    
    cursor.execute(f"SELECT * FROM alarms {where_query} LIMIT ? OFFSET ?", (*placeholder_values, size, offset))
    alarms = cursor.fetchall()
    return {
        'last_page': n_pages,
        'data': alarms 
    }