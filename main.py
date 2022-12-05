#!/usr/bin/python
__author__ = 'Benjamin M. Singleton'
__date__ = '04 December 2022'
__version__ = '0.1.1'

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
open_check_regex = r'^\s*<\s*(custom_item|item|(report\s+type\s*:\s*"(PASSED|FAILED|WARNING)"))\s*>'
open_if_regex = r'^\s*<\s*if\s*>'
open_condition_regex = r'^\s*<\s*condition\s+type\s*:\s*"(AND|OR)"\s*>'
open_then_regex = r'^\s*<\s*then\s*>'
open_else_regex = r'^\s*<\s*else\s*>'

close_check_type_regex = r'^\s*<\s*\/\s*check_type\s*>'
close_group_policy_regex = r'^\s*<\s*\/\s*group_policy>'
close_check_regex = r'^\s*<\s*\/\s*(custom_item|item|report)\s*>'
close_if_regex = r'^\s*<\s*\/\s*if\s*>'
close_condition_regex = r'^\s*<\s*\/\s*condition\s*>'
close_then_regex = r'^\s*<\s*\/\s*then\s*>'
close_else_regex = r'^\s*<\s*\/\s*else\s*>'

printable_types = ["Comment", "Blank line", "Check close", "Policy line", "Close check type line", "Close group policy line", "Close If block line", "Close Condition block line", "Close Then block line", "Close Else block line", "Open Check type line", "Open Group policy line", "Open If block line", "Open Condition block line", "Open Then block line", "Open Else block line", "Check block line"]

non_printable_types = ["Group policy block", "Check type block", "Check block", "If block", "Condition block", "Then block", "Else block"]


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


def json_to_audit_file(my_audit_file: dict) -> str:
    """
    Recursively builds a string representing the .audit file format of the 
    checks.
    """
    s = ''
    if my_audit_file['type'] in printable_types:
        s += my_audit_file['text'] + '\n'
    if 'children' in my_audit_file.keys():
        for each_child in my_audit_file['children']:
            s += json_to_audit_file(each_child)
    return s


def main():
    my_audit_file = {"type": "root", "text": "", "parent": None, "children": []}
    parent_object = my_audit_file
    with open('test.audit', 'r') as my_file:
        raw_text = my_file.read().split('\n')

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
            parent_object['children'].append({"type": "Close check type line", "text": line_text, "start_line": line_number, "end_line": line_number})
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_group_policy_regex, line_text):
            parent_object['children'].append({"type": "Close group policy line", "text": line_text, "start_line": line_number, "end_line": line_number})
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_if_regex, line_text):
            parent_object['children'].append({"type": "Close If block line", "text": line_text, "start_line": line_number, "end_line": line_number})
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_condition_regex, line_text):
            parent_object['children'].append({"type": "Close Condition block line", "text": line_text, "start_line": line_number, "end_line": line_number})
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_then_regex, line_text):
            parent_object['children'].append({"type": "Close Then block line", "text": line_text, "start_line": line_number, "end_line": line_number})
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_else_regex, line_text):
            parent_object['children'].append({"type": "Close Else block line", "text": line_text, "start_line": line_number, "end_line": line_number})
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        # these open_*_regex lines are also mostly indentical.
        elif re.search(open_check_type_regex, line_text):
            parent_object['children'].append({"type": "Check type block", "text": "", "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
            parent_object['children'].append({"type": "Open Check type line", "text": line_text, "start_line": line_number, "end_line": line_number})
        elif re.search(open_group_policy_regex, line_text):
            parent_object['children'].append({"type": "Group policy block", "text": "", "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
            parent_object['children'].append({"type": "Open Group policy line", "text": line_text, "start_line": line_number, "end_line": line_number})
        elif re.search(open_if_regex, line_text):
            parent_object['children'].append({"type": "If block", "text": "", "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
            parent_object['children'].append({"type": "Open If block line", "text": line_text, "start_line": line_number, "end_line": line_number})
        elif re.search(open_condition_regex, line_text):
            parent_object['children'].append({"type": "Condition block", "text": "", "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
            parent_object['children'].append({"type": "Open Condition block line", "text": line_text, "start_line": line_number, "end_line": line_number})
        elif re.search(open_then_regex, line_text):
            parent_object['children'].append({"type": "Then block", "text": "", "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
            parent_object['children'].append({"type": "Open Then block line", "text": line_text, "start_line": line_number, "end_line": line_number})
        elif re.search(open_else_regex, line_text):
            parent_object['children'].append({"type": "Else block", "text": "", "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
            parent_object['children'].append({"type": "Open Else block line", "text": line_text, "start_line": line_number, "end_line": line_number})
        elif re.search(open_check_regex, line_text):
            parent_object['children'].append({"type": "Check block", "text": "", "start_line": line_number, "end_line": -1, "parent": parent_object, "children": list()})
            parent_object = parent_object['children'][-1]
            parent_object['children'].append({"type": "Check block line", "text": line_text, "start_line": line_number, "end_line": line_number})
    
    # strip out all references to parent objects, since those aren't JSONable.
    my_audit_file = remove_parents(my_audit_file)
    with open('out.json', 'w') as my_file:
        my_file.write(json.dumps(my_audit_file))
    
    # try to recreate a copy of the audit file from the JSON alone
    with open('out.audit', 'w') as my_file:
        # json_to_audit_file adds an unnecessary trailing newline, so leave it out.
        my_file.write(json_to_audit_file(my_audit_file)[:-1])


if __name__ == '__main__':
    main()
