from typing import Any, Dict

def execute_scraper(code_str: str, html: str, base_url: str = "") -> Dict[str, Any]:
    """
    Executes the scraper python code against the given html.
    Returns the extracted structured dictionary.
    """
    exec_scope = {"__builtins__": __builtins__}
    # Compile and execute code in unified scope so imports are accessible in extract()
    exec(code_str, exec_scope)
    
    if "extract" not in exec_scope:
        raise ValueError("Generated code does not contain an 'extract' function.")
    
    extract_fn = exec_scope["extract"]
    result = extract_fn(html, base_url)
    
    if not isinstance(result, (dict, list)):
        raise ValueError(f"Extractor must return a dict or list, got {type(result).__name__}")
        
    return result
