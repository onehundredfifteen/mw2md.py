#!/usr/bin/env python

import sys
import os
import re

# Supporting Functions

def read_file(filename, mode='r'):
    '''read the content of a file into lines'''
    with open(filename, mode) as filey:
        content = filey.readlines()
    return content

def write_file(filename, content, mode='w'):
    '''read the content of a file into lines'''
    with open(filename, mode) as filey:
        filey.write(content)

def apply_lines(func, content):
    def wrapper():
        lines = []
        for line in content:
            line = func(line)
            lines.append(line)
        return lines
    return wrapper

# Converter

class MarkdownConverter:

    def __init__(self, _lines: list[str], dest: str):
        self.lines = _lines
        self.dest = dest

    @classmethod
    def fromContent(cls, content: str, dest: str):
        return cls(content.splitlines(), dest)
       
    @classmethod
    def fromFile(cls, source: str, dest: str):
        _source = cls._check_path(cls, source)
        
        return cls(read_file(_source), dest)   

    def run(self):

        if self.dest:
            print(f"Transforming MediaWiki {self.dest} to MarkDown syntax...")

        lines = self.lines
        lines = apply_lines(self._convert_headers, lines)()
        lines = apply_lines(self._convert_emphasis, lines)()
        lines = apply_lines(self._convert_links, lines)()
        lines = apply_lines(self._convert_codeblocks, lines)()
        lines = apply_lines(self._convert_lists, lines)()

        if self.dest:
            write_file(self.dest, ''.join(lines))
        else:
            print(''.join(lines))


# Conversion Functions ---------------------------------------------------------
# Each function below handles parsing one line, and should be wrapped by
# apply_lines, with the function as the first argument, and a list
# of lines as the second:  apply_lines(func, lines)(). This is a lazy
# man's decorator :)


    def _convert_lists(self, line):
        '''handle bullets in lists.
        '''
        if line.startswith('::-'):
            line = line.replace('::-', '  -', 1)
        return line

    def _convert_links(self, line):
        '''convert a media wiki link to a standard markdown one.

           [https://slurm.schedmd.com/pdfs/summary.pdf Slurm commands]
           to
           [Slurm Commands](https://slurm.schedmd.com/pdfs/summary.pdf)
        '''
        # Internal Links and images convert to markdown
        for match in re.findall(r"\[\[(.+\|.+)\]\]", line):
            parts = match.split('|')
            if len(parts) == 2:
                title, markdown = parts
            else:
                title = markdown = parts[0]
            

            # If it's an image, the title is the filename
            if re.search("^(F|f)ile:", title):
                holder = re.sub('(F|f)ile:', '', title)
                title = markdown
                markdown = holder.strip().replace(' ', '-')
                markdown = "![%s](%s)" %(title.strip(), markdown)

            else:
                markdown = markdown.lower().strip().replace(' ', '-')
                markdown = "[%s](%s.md)" %(title.strip(), markdown)
 
            line = line.replace("[[%s]]" % match, markdown)
             
        markup_regex = r'\[(http[s]?://.+?)\]'

        # First address external links
        for match in re.findall(markup_regex, line):
            url, text = match.split(" ", 1)
            markdown = "[%s](%s)" %(text.strip(), url.strip())
            line = line.replace("[%s]" % match, markdown)
        return line
         

    def _convert_headers(self, line):
        '''convert headers to markdown, e.g
           == Cluster description == --> ## Cluster Description
           This function should be handled by the apply_lines wrapper.
        '''
        if line.startswith('='):
            header = line.split(" ")[0]
            line = line.rstrip().rstrip(header).strip()
            line = line.replace('=', "#", len(header))
        return line


    def _convert_codeblocks(self, line):
        '''convert source blocks (<source lang="sh">) to ```
        '''
        code = "```"
        if line.startswith("<source"):
             lang = (line.replace("<source lang=", "").replace(
                     ">", "").replace("'","").replace('"','').strip())
             if lang:
                 code = "%s%s\n" %(code, lang)
             line = code
        line = line.replace("</source>", "```")
        return line


    def _convert_emphasis(self, line):
        '''convert in text code (e.g. ''only'') to markdown for bold
           or italic.
        '''
        groups = [("''", "''", "*"),         # bold
                  ("<code>", "</code>", "`") # code blocks
                 ]
        for group in groups:
            left, right, new = group
            for match in re.findall("%s.+%s" %(left, right), line):
                inner = match.replace(left, new).replace(right, new)
                line = line.replace(match, inner)
        return line


    def _check_path(self, path):
        path = os.path.abspath(path)
        if os.path.exists(path):
            return path
        else:
            raise ValueError("Cannot access file at '%s'" % path)
 

