from memory import save_memory, list_memories, add_reminder, list_reminders

def calc(expression: str) -> str:
    allowed = set('0123456789+-*/(). %')
    if not all(ch in allowed for ch in expression):
        return 'Invalid expression'
    try:
        return str(eval(expression, {'__builtins__': {}}, {}))
    except Exception as e:
        return f'Calculation error: {e}'

def run_tool(tool_name: str, *args) -> str:
    try:
        if tool_name == 'save_memory':
            save_memory(args[0], args[1])
            return f'Saved: {args[0]}'
        if tool_name == 'list_memories':
            rows = list_memories()
            return '\n'.join(f'- {k}: {v}' for k, v, _ in rows) if rows else 'No memories stored.'
        if tool_name == 'add_reminder':
            add_reminder(args[0], args[1], args[2])
            return f'Reminder set for {args[1]}'
        if tool_name == 'list_reminders':
            rows = list_reminders()
            return '\n'.join(f'- {r[1]} @ {r[2]}' for r in rows) if rows else 'No reminders.'
        if tool_name == 'calc':
            return calc(args[0])
        return f'Unknown tool: {tool_name}'
    except Exception as e:
        return f'Tool error: {e}'
