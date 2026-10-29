import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError, TokenError

def is_sql_safe(sql_query: str) -> bool:
    """
    Parses SQL into an AST and strictly validates it for read-only safety.
    Returns True if safe, False if it contains destructive commands or syntax errors.
    """
    try:
        # 1. Parse the SQL query into a list of statements (handles queries with semicolons)
        statements = sqlglot.parse(sql_query, read="postgres")
        
        if not statements or all(stmt is None for stmt in statements):
            print("SECURITY BLOCK: Empty or unparseable query.")
            return False

        for statement in statements:
            if statement is None:
                continue
            
            # 2. Whitelist Check: The root operation MUST be a Select or Union (for CTEs)
            if not isinstance(statement, (exp.Select, exp.Union)):
                print(f"SECURITY BLOCK: Forbidden root statement type detected: {type(statement).__name__}")
                return False
            
            # 3. Blacklist Check: Traverse the entire AST looking for any forbidden nodes
            # This catches malicious commands hidden inside subqueries or CTEs
            forbidden_nodes = (
                exp.Drop, exp.Delete, exp.Update, exp.Insert, 
                exp.Alter, exp.Command, exp.Commit, exp.Rollback,
                exp.Create, exp.TruncateTable, exp.Grant, exp.Revoke
            )
            
            for node in statement.walk():
                if isinstance(node, forbidden_nodes):
                    print(f"SECURITY BLOCK: Destructive node detected inside query: {type(node).__name__}")
                    return False

        return True

    # 4. Catch both errors so cut-off text or bad syntax doesn't crash your app
    except (ParseError, TokenError) as e:
        print(f"VALIDATION ERROR: The LLM generated malformed or incomplete SQL. \nDetails: {e}")
        return False