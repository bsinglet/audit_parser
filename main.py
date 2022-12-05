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


open_xml_tag_regex = r'^\s*<[^\\>]*>'
close_xml_tag_regex = r'^\s*<\\[^\\>]*>'

comment_line_regex = r'^\s*#'
blank_line_regex = r'^\s*$'

open_check_regex = r'^\s*<\s*(custom_item|item|report\s+type\s*:\s*"PASSED|FAILED|WARNING")\s*>'
open_if_regex = r'^\s*<\s*if\s*>'
open_condition_regex = r'^\s*<\s*condition\s+type\s*:\s*"(AND|OR)"\s*>'
open_then_regex = r'^\s*<\s*then\s*>'
open_else_regex = r'^\s*<\s*else\s*>'

close_check_regex = r'^\s*<\s*/\s*(custom_item|item|report\s+type\s*:\s*"PASSED|FAILED|WARNING")\s*>'
close_if_regex = r'^\s*<\s*/\s*if\s*>'
close_condition_regex = r'^\s*<\s*condition\s+type\s*:\s*"(AND|OR)"\s*>'
close_then_regex = r'^\s*<\s*/\s*then\s*>'
close_else_regex = r'^\s*<\s*/\s*else\s*>'


def main():
    my_audit_file = {"type": "root", "text": "", "parent": None, "children": []}
    parent_object = my_audit_file
    with open('test.audit', 'r') as my_file:
        raw_text = my_file.read().split('\n')
    last_header_pos = 0

    for line_number, line_text in raw_text:
        if re.search(comment_line_regex, line_text):
            parent_object['children'].append({"type": "Comment", "text": line_text, "start_line": line_number, "end_line": line_number})
        elif re.search(blank_line_regex, line_text):
            parent_object['children'].append({"type": "Blank line", "text": line_text, "start_line": line_number, "end_line": line_number})
        # if we're already in a check definition, then we can't open or close 
        # any other checks or control structures.
        elif parent_object["type"] == "Check block":
            if re.search(close_check_regex, line_text):
                parent_object['children'].append({"type": "Check close", "text": line_text, "start_line": line_number, "end_line": line_number})
                parent_object['end_line'] = line_number
                parent_object = parent_object['parent']
            else:
                parent_object.append({type: "Policy line", "text": line_text})
        elif re.search(close_if_regex, line_text):
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_condition_regex, line_text):
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_then_regex, line_text):
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
        elif re.search(close_else_regex, line_text):
            parent_object['end_line']: line_number
            parent_object = parent_object['parent']
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


if __name__ == '__main__':
    main()
