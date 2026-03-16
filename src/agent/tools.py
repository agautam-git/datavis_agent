TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List all available tables in the database. Only call if [Available tables] is not already in context.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "Get schema, row count and sample row for a specific table. Only call if that table schema is not already in context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to inspect",
                    }
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Run a DuckDB SQL query. Use JOINs across tables when needed. No LIMIT on GROUP BY. LIMIT 100 on raw rows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "Valid DuckDB SQL query"}
                },
                "required": ["sql"],
            },
        },
    },
]
