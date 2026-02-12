from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
import json
from datetime import datetime

app = FastAPI(title="Database Dashboard", version="1.0.0")

# Create directories if they don't exist
Path("templates").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database configuration
DATABASE_URL = "postgresql://retail_qtaf_user:XC4ExHINaIfVfbSzU0E6OmJA3EAqZkrj@dpg-d4t7leu3jp1c73e8oj8g-a.oregon-postgres.render.com:5432/retail_qtaf"

# Templates configuration
templates = Jinja2Templates(directory=".")

@contextmanager
def get_db_connection():
    """Context manager for database connection"""
    conn = None
    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor,
            connect_timeout=10
        )
        yield conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_all_tables(conn) -> List[str]:
    """Get all table names from the database"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        return [table['table_name'] for table in tables]
    except Exception as e:
        print(f"❌ Error getting tables: {e}")
        return []

def get_table_columns(conn, table_name: str) -> List[Dict]:
    """Get column information for a specific table"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position;
        """, (table_name,))
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error getting columns for {table_name}: {e}")
        return []

def get_table_data(conn, table_name: str, limit: int = 1000) -> List[Dict]:
    """Get all data from a specific table"""
    try:
        cursor = conn.cursor()
        # Use parameterized query to prevent SQL injection
        cursor.execute(f'SELECT * FROM "{table_name}" LIMIT %s;', (limit,))
        data = cursor.fetchall()

        # Format data for display
        columns = get_table_columns(conn, table_name)
        for row in data:
            for col in columns:
                col_name = col['column_name']
                if col_name in row and row[col_name] is not None:
                    if col['data_type'] == 'jsonb':
                        try:
                            parsed = json.loads(row[col_name])
                            row[col_name] = json.dumps(parsed, indent=2)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    elif 'timestamp' in col['data_type'].lower():
                        try:
                            # Handle various timestamp formats
                            dt_str = str(row[col_name])
                            if 'T' in dt_str:
                                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                            else:
                                dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                            row[col_name] = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except (ValueError, TypeError):
                            pass

        return data
    except Exception as e:
        print(f"❌ Error getting data from {table_name}: {e}")
        return []

def get_table_row_count(conn, table_name: str) -> int:
    """Get total row count for a table"""
    try:
        cursor = conn.cursor()
        cursor.execute(f'SELECT COUNT(*) as count FROM "{table_name}";')
        result = cursor.fetchone()
        return result['count'] if result else 0
    except Exception as e:
        print(f"❌ Error getting row count for {table_name}: {e}")
        return 0

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    print(f"📍 Dashboard accessed from {request.client.host}")
    try:
        with get_db_connection() as conn:
            # Get all tables
            tables = get_all_tables(conn)
            print(f"📊 Found {len(tables)} tables")
            
            # No default table selection
            selected_table = None
            table_data = []
            columns = []
            row_count = 0
            
            # Get row counts for all tables for the stats
            table_stats = []
            for table in tables:
                count = get_table_row_count(conn, table)
                table_stats.append({
                    'name': table,
                    'count': count
                })
            
            return templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "tables": tables,
                    "table_stats": table_stats,
                    "selected_table": selected_table,
                    "table_data": table_data,
                    "columns": columns,
                    "row_count": row_count,
                    "total_tables": len(tables),
                    "show_data": len(table_data) > 0
                }
            )
    except Exception as e:
        print(f"🚨 Dashboard error: {e}")
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "tables": [],
                "table_stats": [],
                "selected_table": None,
                "table_data": [],
                "columns": [],
                "row_count": 0,
                "total_tables": 0,
                "show_data": False,
                "error": f"Database Error: {str(e)}"
            }
        )

@app.get("/table/{table_name}", response_class=HTMLResponse)
async def view_table(request: Request, table_name: str):
    """View specific table data"""
    print(f"📍 Table {table_name} accessed from {request.client.host}")
    try:
        with get_db_connection() as conn:
            # Get all tables
            tables = get_all_tables(conn)
            
            if table_name not in tables:
                print(f"⚠️ Table {table_name} not found, redirecting to home")
                return RedirectResponse("/")
            
            # Get table data
            columns = get_table_columns(conn, table_name)
            table_data = get_table_data(conn, table_name)
            row_count = get_table_row_count(conn, table_name)
            print(f"✅ Loaded {len(table_data)} rows from {table_name}")
            
            # Get row counts for all tables for the stats
            table_stats = []
            for table in tables:
                count = get_table_row_count(conn, table)
                table_stats.append({
                    'name': table,
                    'count': count
                })
            
            return templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "tables": tables,
                    "table_stats": table_stats,
                    "selected_table": table_name,
                    "table_data": table_data,
                    "columns": columns,
                    "row_count": row_count,
                    "total_tables": len(tables),
                    "show_data": len(table_data) > 0
                }
            )
    except Exception as e:
        print(f"🚨 Table view error for {table_name}: {e}")
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "tables": [],
                "table_stats": [],
                "selected_table": table_name,
                "table_data": [],
                "columns": [],
                "row_count": 0,
                "total_tables": 0,
                "show_data": False,
                "error": f"Database Error: {str(e)}"
            }
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return {
                "status": "healthy",
                "database": "connected",
                "server": "running",
                "port": 8001
            }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected", 
            "error": str(e),
            "server": "running",
            "port": 8001
        }

@app.get("/api/tables")
async def get_tables_list():
    """API endpoint to get all tables"""
    try:
        with get_db_connection() as conn:
            tables = get_all_tables(conn)
            return {"tables": tables, "count": len(tables)}
    except Exception as e:
        return {"error": str(e), "tables": []}

@app.get("/api/table/{table_name}")
async def get_table_data_api(table_name: str, limit: int = 100):
    """API endpoint to get table data"""
    try:
        with get_db_connection() as conn:
            columns = get_table_columns(conn, table_name)
            data = get_table_data(conn, table_name, limit)
            row_count = get_table_row_count(conn, table_name)
            return {
                "table": table_name,
                "columns": columns,
                "data": data,
                "row_count": row_count,
                "showing": len(data)
            }
    except Exception as e:
        return {"error": str(e)}

@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint to prevent 404 errors"""
    from fastapi.responses import Response
    return Response(status_code=204)  # No content

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Database Dashboard...")
    print("🌐 Server running on: http://localhost:8001")
    print("📊 Dashboard available at: http://localhost:8001/")
    print("🔧 Health check: http://localhost:8001/api/health")
    print("📋 API Tables list: http://localhost:8001/api/tables")
    print("\n📝 Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "view:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        access_log=True
    )