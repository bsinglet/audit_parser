#!/usr/bin/python
__author__ = 'Benjamin M. Singleton'
__date__ = '04 December 2022'
__version__ = '0.1.0'

"""
This is a script that parses Tenable audit files, transforming them each check 
into a Python dict. These are then transformed to JSON objects to more easily
manipulate.
"""

import re
import json

open_xml_tag_regex = r'^\s*<[^\\>]*>'
close_xml_tag_regex = r'^\s*<\\[^\\>]*>'

comment_line_regex = r'^\s*#'
blank_line_regex = r'^\s*$'

open_check_type_regex = r'^\s*<\s*check_type\s*:\s*"[^"]*"\s*(version\s*:\s*"\d+"\s*)?>'
open_group_policy_regex = r'^\s*<\s*group_policy\s*:\s*"[^"]*"\s*>'
open_check_regex = r'^\s*<\s*(custom_item|item|report\s+type\s*:\s*"PASSED|FAILED|WARNING")\s*>'
open_if_regex = r'^\s*<\s*if\s*>'
open_condition_regex = r'^\s*<\s*condition\s+type\s*:\s*"(AND|OR)"\s*>'
open_then_regex = r'^\s*<\s*then\s*>'
open_else_regex = r'^\s*<\s*else\s*>'

close_check_type_regex = r'^\s*<\s*/\s*check_type\s*>'
close_group_policy_regex = r'^\s*<\s*/\s*group_policy>'
close_check_regex = r'^\s*<\s*/\s*(custom_item|item|report\s+type\s*:\s*"PASSED|FAILED|WARNING")\s*>'
close_if_regex = r'^\s*<\s*/\s*if\s*>'
close_condition_regex = r'^\s*<\s*/\s*condition\s*>'
close_then_regex = r'^\s*<\s*/\s*then\s*>'
close_else_regex = r'^\s*<\s*/\s*else\s*>'


def remove_parents(my_audit_file: dict) -> dict:
    """
    Recursively remove all 'parent' from this dict of dicts, as these aren't 
    serializable in JSON.
    """
    my_audit_file['parent'] = ''
    if 'children' in my_audit_file.keys():
        for each_index in range(len(my_audit_file['children'])):
            my_audit_file['children'][each_index] = remove_parents(my_audit_file['children'][each_index])
    return my_audit_file


def main():
    my_audit_file = {"type": "root", "text": "", "parent": None, "children": []}
    parent_object = my_audit_file
    with open('test.audit', 'r') as my_file:
        raw_text = my_file.read().split('\n')
    last_header_pos = 0

    for line_number, line_text in enumerate(raw_text):
        print(f"Reading line number {line_number}")
        if re.search(comment_line_regex, line_text):
            parent_object['children'].append({"type": "Comment", "text": line_text, "start_line": line_number, "end_line": line_number})
        elif re.search(blank_line_regex, line_text):
            parent_object['children'].append({"type": "Blank line", "text": line_text, "start_line": line_number, "end_line": line_number})
        # if we're already in a check definition, then we can't open or close 
        # any other checks or control structures.
        elif re.search(close_check_regex, line_text):
            if not parent_object:
                raise Exception(f"Encountered check block close at line {line_number}, despite no parent object!")
            elif parent_object['type'] != "Check block":
                raise Exception(f"Encountered check block close at line {line_number}, despite parent object type {parent_object['type']}")
            else:
                parent_object['children'].append({"type": "Check close", "text": line_text, "start_line": line_number, "end_line": line_number})
                parent_object['end_line'] = line_number
                parent_object = parent_object['parent']
        elif parent_object and parent_object["type"] == "Check block":
            if not re.search(close_check_regex, line_text):
                parent_object['children'].append({"type": "Policy line", "text": line_text, "start_line": line_number, "end_line": line_number})
        # these close_*_regex conditions are all identical, but might add some 
        # logic later, so breaking it out for now.
        elif re.search(close_check_type_regex, line_text):
            # this should be the end of the audit file, but if we're preserving 
            # comment lines and blank lines we should keep reading.
            if parent_object['type'] != 'Check type block':
                raise Exception(f"Ran into a Check type close when inside a {parent_object['type']}")
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_group_policy_regex, line_text):
            if parent_object['type'] != 'Group policy block':
                raise Exception(f"Ran into a Group policy close when inside a {parent_object['type']}")
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_if_regex, line_text):
            if parent_object['type'] != 'If block':
                raise Exception(f"Ran into a If close when inside a {parent_object['type']}")
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_condition_regex, line_text):
            if parent_object['type'] != 'Condition block':
                raise Exception(f"Ran into a Condition close when inside a {parent_object['type']}")
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_then_regex, line_text):
            if parent_object['type'] != 'Then block':
                raise Exception(f"Ran into a Then close when inside a {parent_object['type']}")
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_else_regex, line_text):
            if parent_object['type'] != 'Else block':
                raise Exception(f"Ran into a Else close when inside a {parent_object['type']}")
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        # these open_*_regex lines are also mostly indentical.
        elif re.search(open_check_type_regex, line_text):
            parent_object['children'].append({"type": "Check type block", "text": line_text, "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
        elif re.search(open_group_policy_regex, line_text):
            parent_object['children'].append({"type": "Group policy block", "text": line_text, "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
        elif re.search(open_if_regex, line_text):
            parent_object['children'].append({"type": "If block", "text": line_text, "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
        elif re.search(open_condition_regex, line_text):
            parent_object['children'].append({"type": "Condition block", "text": line_text, "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
        elif re.search(open_then_regex, line_text):
            parent_object['children'].append({"type": "Then block", "text": line_text, "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
        elif re.search(open_else_regex, line_text):
            parent_object['children'].append({"type": "Else block", "text": line_text, "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
        elif re.search(open_check_regex, line_text):
            parent_object['children'].append({"type": "Check block", "text": line_text, "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
    
    # strip out all references to parent objects, since those aren't JSONable.
    my_audit_file = remove_parents(my_audit_file)
    with open('out.json', 'w') as my_file:
        my_file.write(json.dumps(my_audit_file))


if __name__ == '__main__':
    main()
