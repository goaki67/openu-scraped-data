import json
from bs4 import BeautifulSoup
import re

def clean_invisible(text):
    if not text: return ""
    return text.replace('\u200e', '').replace('\u200f', '').replace('\u202a', '').replace('\u202b', '').replace('\u202c', '').strip()

def tokenize(text):
    # Prepare text
    text = clean_invisible(text)
    
    # Pre-process Hebrew idioms
    text = text.replace('(', ' ( ').replace(')', ' ) ')
    text = text.replace('+', ' AND ')
    text = text.replace(',', ' AND ')
    text = text.replace('וכן', ' AND ')
    text = text.replace('או', ' OR ')
    text = text.replace('שניים מבין', ' AT_LEAST_2_OF ( ')
    text = text.replace('שלושה מבין', ' AT_LEAST_3_OF ( ')
    text = text.replace('אחד מבין', ' OR ( ')
    text = text.replace('אחד מהקורסים', ' OR ( ')
    text = text.replace('הצמד', ' ')
    text = text.replace('השלשה', ' ')
    text = text.replace('הקורסים', ' ')
    text = text.replace('הקורס', ' ')
    text = text.replace('קורסים', ' ')
    text = text.replace('קורס', ' ')
    
    # Extract tokens: operators and [ID]
    raw_tokens = text.split()
    tokens = []
    
    valid_ops = {'AND', 'OR', '(', ')', 'AT_LEAST_2_OF', 'AT_LEAST_3_OF'}
    
    for t in raw_tokens:
        if t in valid_ops:
            tokens.append(t)
        else:
            # find all [ID]s in the token
            matches = re.findall(r'\[\d{5}\]', t)
            for m in matches:
                tokens.append(m)
                
    # Clean up empty parenthesis and consecutive operators
    # This is a heuristic cleanup to handle messy natural language translations
    cleaned = []
    for t in tokens:
        if t == ')' and cleaned and cleaned[-1] == '(':
            cleaned.pop()
        elif re.match(r'^\[\d{5}\]$', t) and cleaned and cleaned[-1] == t:
            # Skip consecutive identical course IDs (often caused by "CourseName (CourseID)")
            continue
        elif re.match(r'^\[\d{5}\]$', t) and len(cleaned) >= 2 and cleaned[-1] == '(' and cleaned[-2] == t:
            # Skip [ID] ( [ID]
            continue
        elif t == ')' and cleaned and cleaned[-1] == t and len(cleaned)>=3 and cleaned[-2] == '(' and re.match(r'^\[\d{5}\]$', cleaned[-3]):
             # Skip the closing parens of the above
             continue
        else:
            cleaned.append(t)
            
    final_tokens = []
    last_was_course = False
    
    for i, t in enumerate(cleaned):
        if re.match(r'^\[\d{5}\]$', t):
            # If we have two courses in a row without an operator, assume AND
            if last_was_course:
                final_tokens.append('AND')
            final_tokens.append(t)
            last_was_course = True
        elif t in ['AND', 'OR']:
            if not last_was_course and (not final_tokens or final_tokens[-1] in ['AND', 'OR', '(']):
                continue # Skip dangling operators
            final_tokens.append(t)
            last_was_course = False
        else: # ( ) AT_LEAST_*
            # Clean dangling operators before close paren
            if t == ')' and final_tokens and final_tokens[-1] in ['AND', 'OR']:
                final_tokens.pop()
            final_tokens.append(t)
            last_was_course = (t == ')')
            
    # Remove trailing operators
    while final_tokens and final_tokens[-1] in ['AND', 'OR']:
        final_tokens.pop()
        
    # Deduplicate consecutive identical IDs that might have snuck through
    dedup_tokens = []
    for t in final_tokens:
        if re.match(r'^\[\d{5}\]$', t) and dedup_tokens and dedup_tokens[-1] == t:
            continue
        if t == ')' and dedup_tokens and dedup_tokens[-1] == '(':
            dedup_tokens.pop()
            continue
        dedup_tokens.append(t)
        
    return dedup_tokens

def build_ast(tokens):
    """
    Converts a token list into a nested AST JSON structure.
    Tokens: [ID], AND, OR, (, ), AT_LEAST_2_OF, AT_LEAST_3_OF
    This is a simplified precedence parser: AND has higher precedence than OR.
    Because natural language is messy, we just build nested dicts.
    """
    if not tokens:
        return None
        
    def parse_expression(token_list):
        # Base case
        if not token_list:
            return None
        if len(token_list) == 1:
            if token_list[0].startswith('['):
                return {"type": "COURSE", "id": token_list[0][1:-1]}
            return None

        # Split by OR (lowest precedence)
        # We need to find ORs that are not inside parentheses
        or_indices = []
        depth = 0
        for i, t in enumerate(token_list):
            if t in ['(', 'AT_LEAST_2_OF', 'AT_LEAST_3_OF']: depth += 1
            elif t == ')': depth -= 1
            elif t == 'OR' and depth == 0:
                or_indices.append(i)
                
        if or_indices:
            operands = []
            start = 0
            for idx in or_indices:
                parsed = parse_expression(token_list[start:idx])
                if parsed: operands.append(parsed)
                start = idx + 1
            parsed = parse_expression(token_list[start:])
            if parsed: operands.append(parsed)
            
            if len(operands) == 1: return operands[0]
            elif operands: return {"type": "OR", "operands": operands}
            return None

        # Split by AND
        and_indices = []
        depth = 0
        for i, t in enumerate(token_list):
            if t in ['(', 'AT_LEAST_2_OF', 'AT_LEAST_3_OF']: depth += 1
            elif t == ')': depth -= 1
            elif t == 'AND' and depth == 0:
                and_indices.append(i)
                
        if and_indices:
            operands = []
            start = 0
            for idx in and_indices:
                parsed = parse_expression(token_list[start:idx])
                if parsed: operands.append(parsed)
                start = idx + 1
            parsed = parse_expression(token_list[start:])
            if parsed: operands.append(parsed)
            
            if len(operands) == 1: return operands[0]
            elif operands: return {"type": "AND", "operands": operands}
            return None

        # Handle parentheses / blocks
        if token_list[0] in ['(', 'AT_LEAST_2_OF', 'AT_LEAST_3_OF'] and token_list[-1] == ')':
            inner = token_list[1:-1]
            parsed_inner = parse_expression(inner)
            if token_list[0] == 'AT_LEAST_2_OF' and parsed_inner:
                return {"type": "AT_LEAST_2", "operands": parsed_inner.get("operands", [parsed_inner])}
            elif token_list[0] == 'AT_LEAST_3_OF' and parsed_inner:
                return {"type": "AT_LEAST_3", "operands": parsed_inner.get("operands", [parsed_inner])}
            return parsed_inner

        # If we got here, maybe mismatched parens, just treat as AND of everything valid
        operands = []
        for t in token_list:
            if t.startswith('['):
                operands.append({"type": "COURSE", "id": t[1:-1]})
        if len(operands) == 1: return operands[0]
        elif operands: return {"type": "AND", "operands": operands}
        return None

    return parse_expression(tokens)

def generate_ast():
    output = {}
    
    with open('scraped_course_pages.jsonl', 'r', encoding='windows-1255') as f:
        for line in f:
            try:
                data = json.loads(line)
            except:
                continue
                
            course_id = data.get('course_id')
            html = data.get('html', '')
            if not html: continue
            
            soup = BeautifulSoup(html, 'html.parser')
            title_elem = soup.find('title')
            title = clean_invisible(title_elem.get_text()) if title_elem else ''
            
            # Extract footnotes
            footnotes = {}
            for p in soup.find_all('p', class_='textheara'):
                num_span = p.find('span', class_='remarksnumber')
                if num_span:
                    num = clean_invisible(num_span.get_text())
                    # Clone p to manipulate
                    p_clone = BeautifulSoup(str(p), 'html.parser').p
                    p_clone.find('span', class_='remarksnumber').decompose() # remove number
                    
                    # Replace links in footnote with [ID]
                    for a in p_clone.find_all('a'):
                        href = a.get('href', '')
                        match = re.search(r'/courses/(\d{5})\.htm', href)
                        if match:
                            a.replace_with(f" [{match.group(1)}] ")
                    
                    fn_text = clean_invisible(p_clone.get_text())
                    fn_text = re.sub(r'(?<!\[)(\b\d{5}\b)(?!\])', r'[\1]', fn_text)
                    footnotes[num] = fn_text
                    
            # Extract prerequisite paragraphs
            req_keys = ['תנאי קבלה', 'ידע קודם דרוש', 'ידע קודם מומלץ']
            reqs = {
                "kabala": None,
                "darush": None,
                "mumlats": None
            }
            
            for p in soup.find_all('p'):
                p_text_raw = clean_invisible(p.get_text())
                if not any(k in p_text_raw for k in req_keys):
                    continue
                    
                # Replace links with [ID] in the paragraph
                for a in p.find_all('a'):
                    href = a.get('href', '')
                    match = re.search(r'/courses/(\d{5})\.htm', href)
                    if match:
                        a.replace_with(f" [{match.group(1)}] ")
                        
                # Replace footnotes with inline text wrapped in OR ()
                for span in p.find_all('span', class_='heara'):
                    fn_num = clean_invisible(span.get_text())
                    if fn_num in footnotes:
                        # Inject OR ( footnote_text )
                        span.replace_with(f" OR ( {footnotes[fn_num]} ) ")
                        
                p_text = clean_invisible(p.get_text())
                # Replace raw 5 digits
                p_text = re.sub(r'(?<!\[)(\b\d{5}\b)(?!\])', r'[\1]', p_text)
                
                # Split by requirement types if they are in the same paragraph
                import re as regex
                pattern = '(' + '|'.join(req_keys) + r'):'
                parts = regex.split(pattern, p_text)
                
                current_key = None
                for part in parts:
                    part = part.strip()
                    if part in req_keys:
                        current_key = part
                    elif current_key and part:
                        tokens = tokenize(part)
                        ast = build_ast(tokens)
                        
                        if current_key == 'תנאי קבלה': reqs['kabala'] = ast
                        elif current_key == 'ידע קודם דרוש': reqs['darush'] = ast
                        elif current_key == 'ידע קודם מומלץ': reqs['mumlats'] = ast
                        current_key = None
                        
            if any(reqs.values()):
                output[course_id] = {
                    "course_name": title,
                    "requirements": {k: v for k, v in reqs.items() if v}
                }
                
    with open('ast_prerequisites.json', 'w', encoding='utf-8') as out_f:
        json.dump(output, out_f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    generate_ast()
