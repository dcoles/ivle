#!/usr/bin/env python
#
# Natural Language Toolkit: Documentation generation script
#
# Copyright (C) 2001-2006 University of Pennsylvania
# Author: Edward Loper <edloper@gradient.cis.upenn.edu>
#         Steven Bird (substantially cut down)
# URL: <http://nltk.sf.net>
# For license information, see LICENSE.TXT

r"""
This is a customized driver for converting docutils reStructuredText
documents into HTML and LaTeX.  It customizes the standard writers in
the following ways:
    
    - Source code highlighting is added to all doctest blocks.  In
      the HTML output, highlighting is performed using css classes:
      'pysrc-prompt', 'pysrc-keyword', 'pysrc-string', 'pysrc-comment',
      and 'pysrc-output'.
"""

import re, os.path, textwrap, sys, pickle
from optparse import OptionParser

import docutils.core, docutils.nodes, docutils.io
from docutils.writers import Writer
from docutils.writers.html4css1 import HTMLTranslator, Writer as HTMLWriter
from docutils.parsers.rst import directives, roles
from docutils.readers.standalone import Reader as StandaloneReader
from docutils.transforms import Transform
import docutils.writers.html4css1
from doctest import DocTestParser
import docutils.statemachine

OUTPUT_FORMAT = None
"""A global variable, set by main(), indicating the output format for
   the current file.  Can be 'latex' or 'html' or 'ref'."""

OUTPUT_BASENAME = None
"""A global variable, set by main(), indicating the base filename
   of the current file (i.e., the filename with its extension
   stripped).  This is used to generate filenames for images."""

######################################################################
#{ Doctest Indentation
######################################################################

class UnindentDoctests(Transform):
    """
    In our source text, we have indented most of the doctest blocks,
    for two reasons: it makes copy/pasting with the doctest script
    easier; and it's more readable.  But we don't *actually* want them
    to be included in block_quote environments when we output them.
    So this transform looks for any doctest_block's that are the only
    child of a block_quote, and eliminates the block_quote.
    """
    default_priority = 1000
    def apply(self):
        self.document.walkabout(UnindentDoctestVisitor(self.document))

class UnindentDoctestVisitor(docutils.nodes.NodeVisitor):
    def __init__(self, document):
        docutils.nodes.NodeVisitor.__init__(self, document)
    def unknown_visit(self, node): pass
    def unknown_departure(self, node): pass
    def visit_block_quote(self, node):
        if (len(node) == sum([1 for c in node if
                              isinstance(c, docutils.nodes.doctest_block)])):
            node.replace_self(list(node))
        raise docutils.nodes.SkipNode()
        
_OPTION_DIRECTIVE_RE = re.compile(
    r'(\n[ ]*\.\.\.[ ]*)?#\s*doctest:\s*([^\n\'"]*)$', re.MULTILINE)
def strip_doctest_directives(text):
    return _OPTION_DIRECTIVE_RE.sub('', text)

class pylisting(docutils.nodes.General, docutils.nodes.Element):
    """
    Python source code listing.

    Children: doctest_block+ caption?
    """

######################################################################
#{ HTML Output
######################################################################
from epydoc.docwriter.html_colorize import PythonSourceColorizer
import epydoc.docwriter.html_colorize
epydoc.docwriter.html_colorize .PYSRC_EXPANDTO_JAVASCRIPT = ''

class CustomizedHTMLWriter(HTMLWriter):
    settings_defaults = HTMLWriter.settings_defaults.copy()
    settings_defaults.update({
        'output_encoding': 'ascii',
        'output_encoding_error_handler': 'xmlcharrefreplace',
        })
        
    def __init__(self):
        HTMLWriter.__init__(self)
        self.translator_class = CustomizedHTMLTranslator

    #def translate(self):
    #    postprocess(self.document)
    #    HTMLWriter.translate(self)

class CustomizedHTMLTranslator(HTMLTranslator):
    def __init__(self, document):
        HTMLTranslator.__init__(self, document)

    def visit_pylisting(self, node):
        self._write_pylisting_file(node)
        self.body.append(self.CODEBOX_HEADER % ('pylisting', 'pylisting'))

    def depart_pylisting(self, node):
        self.body.append(self.CODEBOX_FOOTER)

    def visit_doctest_block(self, node):
        # Collect the text content of the doctest block.
        text = ''.join(str(c) for c in node)
        text = textwrap.dedent(text)
        text = strip_doctest_directives(text)

        # Colorize the contents of the doctest block.
        colorizer = HTMLDoctestColorizer(self.encode)
        if node.get('is_codeblock'):
            pysrc = colorizer.colorize_codeblock(text)
        else:
            pysrc = colorizer.colorize_doctest(text)

        if node.get('is_codeblock'): typ = 'codeblock' 
        else: typ = 'doctest'
        pysrc = self.CODEBOX_ROW % (typ, pysrc)

        if not isinstance(node.parent, pylisting):
            self.body.append(self.CODEBOX_HEADER % ('doctest', 'doctest'))
            self.body.append(pysrc)
            self.body.append(self.CODEBOX_FOOTER)
        else:
            self.body.append(pysrc)
            
        raise docutils.nodes.SkipNode() # Content already processed

    CODEBOX_HEADER = ('<div class="%s">\n'
                        '<table border="0" cellpadding="0" cellspacing="0" '
                        'class="%s" width="95%%">\n')
    CODEBOX_FOOTER = '</table></div>\n'
    CODEBOX_ROW = textwrap.dedent('''\
      <tr><td class="%s">
      <table border="0" cellpadding="0" cellspacing="0" width="100%%">
      <tr><td class="pysrc">%s</td>
      </tr></table></td></tr>\n''')

    # For generated pylisting files:
    _PYLISTING_FILE_HEADER = "# Natural Language Toolkit: %s\n\n"

    def _write_pylisting_file(self, node):
        if not os.path.exists(PYLISTING_DIR):
            os.mkdir(PYLISTING_DIR)
            
        name = re.sub('\W', '_', node['name'])
        filename = os.path.join(PYLISTING_DIR, name+PYLISTING_EXTENSION)
        out = open(filename, 'w')
        out.write(self._PYLISTING_FILE_HEADER % name)
        for child in node:
            if not isinstance(child, docutils.nodes.doctest_block):
                continue
            elif child['is_codeblock']:
                out.write(''.join(str(c) for c in child)+'\n\n')
            elif INCLUDE_DOCTESTS_IN_PYLISTING_FILES:
                lines = ''.join(str(c) for c in child).split('\n')
                in_doctest_block = False
                for line in lines:
                    if line.startswith('>>> '):
                        out.write(line[4:]+'\n')
                        in_doctest_block = True
                    elif line.startswith('... ') and in_doctest_block:
                        out.write(line[4:]+'\n')
                    elif line.strip():
                        if in_doctest_block:
                            out.write('# Expect:\n')
                        out.write('#     ' + line+'\n')
                        in_doctest_block = False
                    else:
                        out.write(line+'\n')
                        in_doctest_block = False
        out.close()

    def visit_exercise(self, node):
        self.body.append('<exercise src="')

    def depart_exercise(self, node):
        self.body.append('"/>')

    def visit_literal(self, node):
        """Process text to prevent tokens from wrapping."""
        text = ''.join(str(c) for c in node)
        colorizer = HTMLDoctestColorizer(self.encode)
        pysrc = colorizer.colorize_inline(text)#.strip()
        #pysrc = colorize_doctestblock(text, self._markup_pysrc, True)
        self.body+= [self.starttag(node, 'tt', '', CLASS='doctest'),
                     '<span class="pre">%s</span></tt>' % pysrc]
        raise docutils.nodes.SkipNode() # Content already processed
                          
    def depart_field_name(self, node):
        # Don't add ":" in callout field lists.
        if 'callout' in node['classes']:
            self.body.append(self.context.pop())
        else:
            HTMLTranslator.depart_field_name(self, node)
    
    def _striphtml_len(self, s):
        return len(re.sub(r'&[^;]+;', 'x', re.sub(r'<[^<]+>', '', s)))

    def visit_caption(self, node):
        HTMLTranslator.visit_caption(self, node)
        
    def depart_caption(self, node):
        HTMLTranslator.depart_caption(self, node)

    def starttag(self, node, tagname, suffix='\n', empty=0, **attributes):
        if node.get('mimetype'):
            attributes['type'] = node.get('mimetype')
        return HTMLTranslator.starttag(self, node, tagname, suffix,
                                       empty, **attributes)
        
######################################################################
#{ Source Code Highlighting
######################################################################

# [xx] Note: requires the very latest svn version of epydoc!
from epydoc.markup.doctest import DoctestColorizer

class HTMLDoctestColorizer(DoctestColorizer):
    PREFIX = '<pre class="doctest">\n'
    SUFFIX = '</pre>\n'
    def __init__(self, encode_func, callouts=None):
        self.encode = encode_func
        self.callouts = callouts
    def markup(self, s, tag):
        if tag == 'other':
            return self.encode(s)
        elif (tag == 'comment' and self.callouts is not None and
              CALLOUT_RE.match(s)):
            callout_id = CALLOUT_RE.match(s).group(1)
            callout_num = self.callouts[callout_id]
            img = CALLOUT_IMG % (callout_num, callout_num)
            return ('<a name="%s" /><a href="#ref-%s">%s</a>' %
                    (callout_id, callout_id, img))
        else:
            return ('<span class="pysrc-%s">%s</span>' %
                    (tag, self.encode(s)))

######################################################################
#{ Customized Reader (register new transforms)
######################################################################

class CustomizedReader(StandaloneReader):
    _TRANSFORMS = [
        UnindentDoctests,           # 1000
        ]
    def get_transforms(self):
        return StandaloneReader.get_transforms(self) + self._TRANSFORMS

######################################################################
#{ Main Function
######################################################################

_OUTPUT_RE = re.compile(r'<div class="document">\s+(.*)\s+</div>\n</body>\n</html>',
    re.MULTILINE | re.DOTALL)

def rst(input):
    try:
        CustomizedHTMLWriter.settings_defaults.update({'stylesheet_path': '/dev/null'})
        output = docutils.core.publish_string(input,
            writer=CustomizedHTMLWriter(), reader=CustomizedReader())
        match = _OUTPUT_RE.search(output)
        if match:
            return match.group(1)
        else:
            raise ValueError('Could not process exercise definition')

    except docutils.utils.SystemMessage, e:
        print 'Fatal error encountered!', e
        raise
        sys.exit(-1)

