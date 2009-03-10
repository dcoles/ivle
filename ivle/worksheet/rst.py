#!/usr/bin/python
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
import re, os.path, textwrap, sys, pickle, inspect
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



LATEX_VALIGN_IS_BROKEN = True
"""Set to true to compensate for a bug in the latex writer.  I've
   submitted a patch to docutils, so hopefully this wil be fixed
   soon."""

LATEX_DPI = 140
"""The scaling factor that should be used to display bitmapped images
   in latex/pdf output (specified in dots per inch).  E.g., if a
   bitmapped image is 100 pixels wide, it will be scaled to
   100/LATEX_DPI inches wide for the latex/pdf output.  (Larger
   values produce smaller images in the generated pdf.)"""

TREE_IMAGE_DIR = 'tree_images/'
"""The directory that tree images should be written to."""

EXTERN_REFERENCE_FILES = []
"""A list of .ref files, for crossrefering to external documents (used
   when building one chapter at a time)."""

BIBTEX_FILE = '../refs.bib'
"""The name of the bibtex file used to generate bibliographic entries."""

BIBLIOGRAPHY_HTML = "bibliography.html"
"""The name of the HTML file containing the bibliography (for
   hyperrefs from citations)."""

# needs to include "../doc" so it works in /doc_contrib
LATEX_STYLESHEET_PATH = '../../doc/definitions.sty'
"""The name of the LaTeX style file used for generating PDF output."""

LOCAL_BIBLIOGRAPHY = False
"""If true, assume that this document contains the bibliography, and
   link to it locally; if false, assume that bibliographic links
   should point to L{BIBLIOGRAPHY_HTML}."""

PYLISTING_DIR = 'pylisting/'
"""The directory where pylisting files should be written."""

PYLISTING_EXTENSION = ".py"
"""Extension for pylisting files."""

INCLUDE_DOCTESTS_IN_PYLISTING_FILES = False
"""If true, include code from doctests in the generated pylisting
   files. """

CALLOUT_IMG = '<img src="callouts/callout%s.gif" alt="[%s]" class="callout" />'
"""HTML code for callout images in pylisting blocks."""

REF_EXTENSION = '.ref'
"""File extension for reference files."""

# needs to include "../doc" so it works in /doc_contrib
CSS_STYLESHEET = '/dev/null' #/home/nick/exercise-ui/ivle/webapp/tutorial/media/nltkdoc.css'


OUTPUT_FORMAT = None
"""A global variable, set by main(), indicating the output format for
   the current file.  Can be 'latex' or 'html' or 'ref'."""

OUTPUT_BASENAME = None
"""A global variable, set by main(), indicating the base filename
   of the current file (i.e., the filename with its extension
   stripped).  This is used to generate filenames for images."""

COPY_CLIPBOARD_JS = ''


######################################################################
#{ Reference files
######################################################################

def read_ref_file(basename=None):
    if basename is None: basename = OUTPUT_BASENAME
    if not os.path.exists(basename + REF_EXTENSION):
        warning('File %r does not exist!' %
                (basename + REF_EXTENSION))
        return dict(targets=(),terms={},reference_labes={})
    f = open(basename + REF_EXTENSION)
    ref_info = pickle.load(f)
    f.close()
    return ref_info

def write_ref_file(ref_info):
    f = open(OUTPUT_BASENAME + REF_EXTENSION, 'w')
    pickle.dump(ref_info, f)
    f.close()

def add_to_ref_file(**ref_info):
    if os.path.exists(OUTPUT_BASENAME + REF_EXTENSION):
        info = read_ref_file()
        info.update(ref_info)
        write_ref_file(info)
    else:
        write_ref_file(ref_info)

######################################################################
#{ Directives
######################################################################

class example(docutils.nodes.paragraph): pass

def example_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    """
    Basic use::

        .. example:: John went to the store.

    To refer to examples, use::

        .. _store:
        .. example:: John went to the store.

        In store_, John performed an action.
    """
    text = '\n'.join(content)
    node = example(text)
    state.nested_parse(content, content_offset, node)
    return [node]
example_directive.content = True
directives.register_directive('example', example_directive)
directives.register_directive('ex', example_directive)

def doctest_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    """
    Used to explicitly mark as doctest blocks things that otherwise
    wouldn't look like doctest blocks.
    """
    text = '\n'.join(content)
    if re.match(r'.*\n\s*\n', block_text):
        warning('doctest-ignore on line %d will not be ignored, '
             'because there is\na blank line between ".. doctest-ignore::"'
             ' and the doctest example.' % lineno)
    return [docutils.nodes.doctest_block(text, text, codeblock=True)]
doctest_directive.content = True
directives.register_directive('doctest-ignore', doctest_directive)

_treenum = 0
def tree_directive(name, arguments, options, content, lineno,
                   content_offset, block_text, state, state_machine):
    global _treenum
    text = '\n'.join(arguments) + '\n'.join(content)
    _treenum += 1
    # Note: the two filenames generated by these two cases should be
    # different, to prevent conflicts.
    if OUTPUT_FORMAT == 'latex':
        density, scale = 300, 150
        scale = scale * options.get('scale', 100) / 100
        filename = '%s-tree-%s.pdf' % (OUTPUT_BASENAME, _treenum)
        align = LATEX_VALIGN_IS_BROKEN and 'bottom' or 'top'
    elif OUTPUT_FORMAT == 'html':
        density, scale = 100, 100
        density = density * options.get('scale', 100) / 100
        filename = '%s-tree-%s.png' % (OUTPUT_BASENAME, _treenum)
        align = 'top'
    elif OUTPUT_FORMAT == 'ref':
        return []
    else:
        assert 0, 'bad output format %r' % OUTPUT_FORMAT
    if not os.path.exists(TREE_IMAGE_DIR):
        os.mkdir(TREE_IMAGE_DIR)
    try:
        filename = os.path.join(TREE_IMAGE_DIR, filename)
        tree_to_image(text, filename, density)
    except Exception, e:
        raise
        warning('Error parsing tree: %s\n%s\n%s' % (e, text, filename))
        return [example(text, text)]

    imagenode = docutils.nodes.image(uri=filename, scale=scale, align=align)
    return [imagenode]

tree_directive.arguments = (1,0,1)
tree_directive.content = True
tree_directive.options = {'scale': directives.nonnegative_int}
directives.register_directive('tree', tree_directive)

def avm_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    text = '\n'.join(content)
    try:
        if OUTPUT_FORMAT == 'latex':
            latex_avm = parse_avm(textwrap.dedent(text)).as_latex()
            return [docutils.nodes.paragraph('','',
                       docutils.nodes.raw('', latex_avm, format='latex'))]
        elif OUTPUT_FORMAT == 'html':
            return [parse_avm(textwrap.dedent(text)).as_table()]
        elif OUTPUT_FORMAT == 'ref':
            return [docutils.nodes.paragraph()]
    except ValueError, e:
        if isinstance(e.args[0], int):
            warning('Error parsing avm on line %s' % (lineno+e.args[0]))
        else:
            raise
            warning('Error parsing avm on line %s: %s' % (lineno, e))
        node = example(text, text)
        state.nested_parse(content, content_offset, node)
        return [node]
avm_directive.content = True
directives.register_directive('avm', avm_directive)

def def_directive(name, arguments, options, content, lineno,
                  content_offset, block_text, state, state_machine):
    state_machine.document.setdefault('__defs__', {})[arguments[0]] = 1
    return []
def_directive.arguments = (1, 0, 0)
directives.register_directive('def', def_directive)
    
def ifdef_directive(name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    if arguments[0] in state_machine.document.get('__defs__', ()):
        node = docutils.nodes.compound('')
        state.nested_parse(content, content_offset, node)
        return [node]
    else:
        return []
ifdef_directive.arguments = (1, 0, 0)
ifdef_directive.content = True
directives.register_directive('ifdef', ifdef_directive)
    
def ifndef_directive(name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    if arguments[0] not in state_machine.document.get('__defs__', ()):
        node = docutils.nodes.compound('')
        state.nested_parse(content, content_offset, node)
        return [node]
    else:
        return []
ifndef_directive.arguments = (1, 0, 0)
ifndef_directive.content = True
directives.register_directive('ifndef', ifndef_directive)


######################################################################
#{ Table Directive
######################################################################
_table_ids = set()
def table_directive(name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    # The identifier for this table.
    if arguments:
        table_id = arguments[0]
        if table_id in _table_ids:
            warning("Duplicate table id %r" % table_id)
        _table_ids.add(table_id)

        # Create a target element for the table
        target = docutils.nodes.target(names=[table_id])
        state_machine.document.note_explicit_target(target)

    # Parse the contents.
    node = docutils.nodes.compound('')
    state.nested_parse(content, content_offset, node)
    if len(node) == 0 or not isinstance(node[0], docutils.nodes.table):
        return [state_machine.reporter.error(
            'Error in "%s" directive: expected table as first child' %
            name)]

    # Move the caption into the table.
    table = node[0]
    caption = docutils.nodes.caption('','', *node[1:])
    table.append(caption)

    # Return the target and the table.
    if arguments:
        return [target, table]
    else:
        return [table]
    
    
table_directive.arguments = (0,1,0) # 1 optional arg, no whitespace
table_directive.content = True
table_directive.options = {'caption': directives.unchanged}
directives.register_directive('table', table_directive)


######################################################################
#{ Program Listings
######################################################################
# We define a new attribute for doctest blocks: 'is_codeblock'.  If
# this attribute is true, then the block contains python code only
# (i.e., don't expect to find prompts.)

class pylisting(docutils.nodes.General, docutils.nodes.Element):
    """
    Python source code listing.

    Children: doctest_block+ caption?
    """
class callout_marker(docutils.nodes.Inline, docutils.nodes.Element):
    """
    A callout marker for doctest block.  This element contains no
    children; and defines the attribute 'number'.
    """

DOCTEST_BLOCK_RE = re.compile('((?:[ ]*>>>.*\n?(?:.*[^ ].*\n?)+\s*)+)',
                              re.MULTILINE)
CALLOUT_RE = re.compile(r'#[ ]+\[_([\w-]+)\][ ]*$', re.MULTILINE)

from docutils.nodes import fully_normalize_name as normalize_name

_listing_ids = set()
def pylisting_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    # The identifier for this listing.
    listing_id = arguments[0]
    if listing_id in _listing_ids:
        warning("Duplicate listing id %r" % listing_id)
    _listing_ids.add(listing_id)
    
    # Create the pylisting element itself.
    listing = pylisting('\n'.join(content), name=listing_id, callouts={})

    # Create a target element for the pylisting.
    target = docutils.nodes.target(names=[listing_id])
    state_machine.document.note_explicit_target(target)

    # Divide the text into doctest blocks.
    for i, v in enumerate(DOCTEST_BLOCK_RE.split('\n'.join(content))):
        pysrc = re.sub(r'\A( *\n)+', '', v.rstrip())
        if pysrc.strip():
            listing.append(docutils.nodes.doctest_block(pysrc, pysrc,
                                                        is_codeblock=(i%2==0)))

    # Add an optional caption.
    if options.get('caption'):
        cap = options['caption'].split('\n')
        caption = docutils.nodes.compound()
        state.nested_parse(docutils.statemachine.StringList(cap),
                           content_offset, caption)
        if (len(caption) == 1 and isinstance(caption[0],
                                             docutils.nodes.paragraph)):
            listing.append(docutils.nodes.caption('', '', *caption[0]))
        else:
            warning("Caption should be a single paragraph")
            listing.append(docutils.nodes.caption('', '', *caption))

    return [target, listing]

pylisting_directive.arguments = (1,0,0) # 1 required arg, no whitespace
pylisting_directive.content = True
pylisting_directive.options = {'caption': directives.unchanged}
directives.register_directive('pylisting', pylisting_directive)

def callout_directive(name, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
    if arguments:
        prefix = '%s-' % arguments[0]
    else:
        prefix = ''
    node = docutils.nodes.compound('')
    state.nested_parse(content, content_offset, node)
    if not (len(node.children) == 1 and
            isinstance(node[0], docutils.nodes.field_list)):
        return [state_machine.reporter.error(
            'Error in "%s" directive: may contain a single defintion '
            'list only.' % (name), line=lineno)]

    node[0]['classes'] = ['callouts']
    for field in node[0]:
        if len(field[0]) != 1:
            return [state_machine.reporter.error(
                'Error in "%s" directive: bad field id' % (name), line=lineno)]
            
        field_name = prefix+('%s' % field[0][0])
        field[0].clear()
        field[0].append(docutils.nodes.reference(field_name, field_name,
                                                 refid=field_name))
        field[0]['classes'] = ['callout']

    return [node[0]]

callout_directive.arguments = (0,1,0) # 1 optional arg, no whitespace
callout_directive.content = True
directives.register_directive('callouts', callout_directive)

_OPTION_DIRECTIVE_RE = re.compile(
    r'(\n[ ]*\.\.\.[ ]*)?#\s*doctest:\s*([^\n\'"]*)$', re.MULTILINE)
def strip_doctest_directives(text):
    return _OPTION_DIRECTIVE_RE.sub('', text)


######################################################################
#{ RST In/Out table
######################################################################

def rst_example_directive(name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    raw = docutils.nodes.literal_block('', '\n'.join(content))
    out = docutils.nodes.compound('')
    state.nested_parse(content, content_offset, out)
    if OUTPUT_FORMAT == 'latex':
        return [
            docutils.nodes.definition_list('',
              docutils.nodes.definition_list_item('',
                docutils.nodes.term('','Input'),
                docutils.nodes.definition('', raw)),
              docutils.nodes.definition_list_item('',
                docutils.nodes.term('','Rendered'),
                docutils.nodes.definition('', out)))]
    else:
        return [
            docutils.nodes.table('',
              docutils.nodes.tgroup('',
                docutils.nodes.colspec(colwidth=5,classes=['rst-raw']),
                docutils.nodes.colspec(colwidth=5),
                docutils.nodes.thead('',
                  docutils.nodes.row('',
                    docutils.nodes.entry('',
                      docutils.nodes.paragraph('','Input')),
                    docutils.nodes.entry('',
                      docutils.nodes.paragraph('','Rendered')))),
                docutils.nodes.tbody('',
                  docutils.nodes.row('',
                    docutils.nodes.entry('',raw),
                    docutils.nodes.entry('',out)))),
              classes=["rst-example"])]

rst_example_directive.arguments = (0, 0, 0)
rst_example_directive.content = True
directives.register_directive('rst_example', rst_example_directive)


######################################################################
#{ Glosses
######################################################################

"""
.. gloss::
   This  | is | used | to | make | aligned | glosses.
    NN   | BE |  VB  | TO |  VB  |  JJ     |   NN
   *Foog blogg blarg.*
"""

class gloss(docutils.nodes.Element): "glossrow+"
class glossrow(docutils.nodes.Element): "paragraph+"

def gloss_directive(name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    # Transform into a table.
    lines = list(content)
    maxlen = max(len(line) for line in lines)
    lines = [('|%-'+`maxlen`+'s|') % line for line in lines]
    tablestr = ''
    prevline = ''
    for line in (lines+['']):
        div = ['-']*(maxlen+2)
        for m in re.finditer(r'\|', prevline):
            div[m.start()] = '+'
        for m in re.finditer(r'\|', line):
            div[m.start()] = '+'
        tablestr += ''.join(div) + '\n' + line + '\n'
        prevline = line
    table_lines = tablestr.strip().split('\n')
    new_content = docutils.statemachine.StringList(table_lines)
    # [XX] DEBUG GLOSSES:
    # print 'converted to:'
    # print tablestr

    # Parse the table.
    node = docutils.nodes.compound('')
    state.nested_parse(new_content, content_offset, node)
    if not (len(node.children) == 1 and
            isinstance(node[0], docutils.nodes.table)):
        error = state_machine.reporter.error(
            'Error in "%s" directive: may contain a single table '
            'only.' % (name), line=lineno)
        return [error]
    table = node[0]
    table['classes'] = ['gloss', 'nolines']
    
    colspecs = table[0]
    for colspec in colspecs:
        colspec['colwidth'] = colspec.get('colwidth',4)/2
    
    return [example('', '', table)]
gloss_directive.arguments = (0, 0, 0)
gloss_directive.content = True
directives.register_directive('gloss', gloss_directive)


######################################################################
#{ Bibliography
######################################################################

class Citations(Transform):
    default_priority = 500 # before footnotes.
    def apply(self):
        if not os.path.exists(BIBTEX_FILE):
            warning('Warning bibtex file %r not found.  '
                    'Not linking citations.' % BIBTEX_FILE)
            return
        bibliography = self.read_bibinfo(BIBTEX_FILE)
        for k, citation_refs in self.document.citation_refs.items():
            for citation_ref in citation_refs[:]:
                cite = bibliography.get(citation_ref['refname'].lower())
                if cite:
                    new_cite = self.citeref(cite, citation_ref['refname'])
                    citation_ref.replace_self(new_cite)
                    self.document.citation_refs[k].remove(citation_ref)

    def citeref(self, cite, key):
        if LOCAL_BIBLIOGRAPHY:
            return docutils.nodes.raw('', '\cite{%s}' % key, format='latex')
        else:
            return docutils.nodes.reference('', '', docutils.nodes.Text(cite),
                                    refuri='%s#%s' % (BIBLIOGRAPHY_HTML, key))

    BIB_ENTRY = re.compile(r'@\w+{.*')
    def read_bibinfo(self, filename):
        bibliography = {} # key -> authors, year
        key = None
        for line in open(filename):
            line = line.strip()
            
            # @InProceedings{<key>,
            m = re.match(r'@\w+{([^,]+),$', line)
            if m:
                key = m.group(1).strip().lower()
                bibliography[key] = [None, None]
                
            #   author = <authors>,
            m = re.match(r'(?i)author\s*=\s*(.*)$', line)
            if m and key:
                bibliography[key][0] = self.bib_authors(m.group(1))
            else:
                m = re.match(r'(?i)editor\s*=\s*(.*)$', line)
                if m and key:
                    bibliography[key][0] = self.bib_authors(m.group(1))
                
            #   year = <year>,
            m = re.match(r'(?i)year\s*=\s*(.*)$', line)
            if m and key:
                bibliography[key][1] = self.bib_year(m.group(1))
        for key in bibliography:
            if bibliography[key][0] is None: warning('no author found:', key)
            if bibliography[key][1] is None: warning('no year found:', key)
            bibliography[key] = '[%s, %s]' % tuple(bibliography[key])
            #debug('%20s %s' % (key, `bibliography[key]`))
        return bibliography

    def bib_year(self, year):
        return re.sub(r'["\'{},]', "", year)

    def bib_authors(self, authors):
        # Strip trailing comma:
        if authors[-1:] == ',': authors=authors[:-1]
        # Strip quotes or braces:
        authors = re.sub(r'"(.*)"$', r'\1', authors)
        authors = re.sub(r'{(.*)}$', r'\1', authors)
        authors = re.sub(r"'(.*)'$", r'\1', authors)
        # Split on 'and':
        authors = re.split(r'\s+and\s+', authors)
        # Keep last name only:
        authors = [a.split()[-1] for a in authors]
        # Combine:
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return '%s & %s' % tuple(authors)
        elif len(authors) == 3:
            return '%s, %s, & %s' % tuple(authors)
        else:
            return '%s et al' % authors[0]
        return authors


######################################################################
#{ Indexing
######################################################################
class termdef(docutils.nodes.Inline, docutils.nodes.TextElement): pass
class idxterm(docutils.nodes.Inline, docutils.nodes.TextElement): pass
class index(docutils.nodes.Element): pass

def idxterm_role(name, rawtext, text, lineno, inliner,
                 options={}, content=[]):
    if name == 'dt': options['classes'] = ['termdef']
    elif name == 'topic': options['classes'] = ['topic']
    else: options['classes'] = ['term']
    # Recursively parse the contents of the index term, in case it
    # contains a substitiution (like |alpha|).
    nodes, msgs = inliner.parse(text, lineno, memo=inliner,
                                parent=inliner.parent)
    return [idxterm(rawtext, '', *nodes, **options)], []

roles.register_canonical_role('dt', idxterm_role)
roles.register_canonical_role('idx', idxterm_role)
roles.register_canonical_role('topic', idxterm_role)

def index_directive(name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    pending = docutils.nodes.pending(ConstructIndex)
    pending.details.update(options)
    state_machine.document.note_pending(pending)
    return [index('', pending)]
index_directive.arguments = (0, 0, 0)
index_directive.content = False
index_directive.options = {'extern': directives.flag}
directives.register_directive('index', index_directive)


class SaveIndexTerms(Transform):
    default_priority = 810 # before NumberReferences transform
    def apply(self):
        v = FindTermVisitor(self.document)
        self.document.walkabout(v)
        
        if OUTPUT_FORMAT == 'ref':
            add_to_ref_file(terms=v.terms)

class ConstructIndex(Transform):
    default_priority = 820 # after NumberNodes, before NumberReferences.
    def apply(self):
        # Find any indexed terms in this document.
        v = FindTermVisitor(self.document)
        self.document.walkabout(v)
        terms = v.terms

        # Check the extern reference files for additional terms.
        if 'extern' in self.startnode.details:
            for filename in EXTERN_REFERENCE_FILES:
                basename = os.path.splitext(filename)[0]
                terms.update(read_ref_file(basename)['terms'])

        # Build the index & insert it into the document.
        index_node = self.build_index(terms)
        self.startnode.replace_self(index_node)

    def build_index(self, terms):
        if not terms: return []
        
        top = docutils.nodes.bullet_list('', classes=['index'])
        start_letter = None
        
        section = None
        for key in sorted(terms.keys()):
            if key[:1] != start_letter:
                top.append(docutils.nodes.list_item(
                    '', docutils.nodes.paragraph('', key[:1].upper()+'\n',
                                                 classes=['index-heading']),
                    docutils.nodes.bullet_list('', classes=['index-section']),
                    classes=['index']))
                section = top[-1][-1]
            section.append(self.entry(terms[key]))
            start_letter = key[:1]
        
        return top

    def entry(self, term_info):
        entrytext, name, sectnum = term_info
        if sectnum is not None:
            entrytext.append(docutils.nodes.emphasis('', ' (%s)' % sectnum))
        ref = docutils.nodes.reference('', '', refid=name,
                                       #resolved=True,
                                       *entrytext)
        para = docutils.nodes.paragraph('', '', ref)
        return docutils.nodes.list_item('', para, classes=['index'])

class FindTermVisitor(docutils.nodes.SparseNodeVisitor):
    def __init__(self, document):
        self.terms = {}
        docutils.nodes.NodeVisitor.__init__(self, document)
    def unknown_visit(self, node): pass
    def unknown_departure(self, node): pass

    def visit_idxterm(self, node):
        node['name'] = node['id'] = self.idxterm_key(node)
        node['names'] = node['ids'] = [node['id']]
        container = self.container_section(node)
        
        entrytext = node.deepcopy()
        if container: sectnum = container.get('sectnum')
        else: sectnum = '0'
        name = node['name']
        self.terms[node['name']] = (entrytext, name, sectnum)
            
    def idxterm_key(self, node):
        key = re.sub('\W', '_', node.astext().lower())+'_index_term'
        if key not in self.terms: return key
        n = 2
        while '%s_%d' % (key, n) in self.terms: n += 1
        return '%s_%d' % (key, n)

    def container_section(self, node):
        while not isinstance(node, docutils.nodes.section):
            if node.parent is None: return None
            else: node = node.parent
        return node



######################################################################
#{ Crossreferences
######################################################################

class ResolveExternalCrossrefs(Transform):
    """
    Using the information from EXTERN_REFERENCE_FILES, look for any
    links to external targets, and set their `refuid` appropriately.
    Also, if they are a figure, section, table, or example, then
    replace the link of the text with the appropriate counter.
    """
    default_priority = 849 # right before dangling refs

    def apply(self):
        ref_dict = self.build_ref_dict()
        v = ExternalCrossrefVisitor(self.document, ref_dict)
        self.document.walkabout(v)

    def build_ref_dict(self):
        """{target -> (uri, label)}"""
        ref_dict = {}
        for filename in EXTERN_REFERENCE_FILES:
            basename = os.path.splitext(filename)[0]
            if OUTPUT_FORMAT == 'html':
                uri = os.path.split(basename)[-1]+'.html'
            else:
                uri = os.path.split(basename)[-1]+'.pdf'
            if basename == OUTPUT_BASENAME:
                pass # don't read our own ref file.
            elif not os.path.exists(basename+REF_EXTENSION):
                warning('%s does not exist' % (basename+REF_EXTENSION))
            else:
                ref_info = read_ref_file(basename)
                for ref in ref_info['targets']:
                    label = ref_info['reference_labels'].get(ref)
                    ref_dict[ref] = (uri, label)

        return ref_dict
    
class ExternalCrossrefVisitor(docutils.nodes.NodeVisitor):
    def __init__(self, document, ref_dict):
        docutils.nodes.NodeVisitor.__init__(self, document)
        self.ref_dict = ref_dict
    def unknown_visit(self, node): pass
    def unknown_departure(self, node): pass

    # Don't mess with the table of contents.
    def visit_topic(self, node):
        if 'contents' in node.get('classes', ()):
            raise docutils.nodes.SkipNode

    def visit_reference(self, node):
        if node.resolved: return
        node_id = node.get('refid') or node.get('refname')
        if node_id in self.ref_dict:
            uri, label = self.ref_dict[node_id]
            #debug('xref: %20s -> %-30s (label=%s)' % (
            #    node_id, uri+'#'+node_id, label))
            node['refuri'] = '%s#%s' % (uri, node_id)
            node.resolved = True

            if label is not None:
                if node.get('expanded_ref'):
                    warning('Label %s is defined both locally (%s) and '
                            'externally (%s)' % (node_id, node[0], label))
                    # hmm...
                else:
                    node.clear()
                    node.append(docutils.nodes.Text(label))
                    expand_reference_text(node)

######################################################################
#{ Exercises
######################################################################

"""
.. exercise:: path.xml
"""

class exercise(docutils.nodes.paragraph,docutils.nodes.Element): pass

def exercise_directive(name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    return [exercise('', arguments[0])]

exercise_directive.arguments = (1, 0, 0)
exercise_directive.content = False
directives.register_directive('exercise', exercise_directive)


######################################################################
#{ Challenges (optional exercises; harder than usual)
######################################################################

"""
.. challenge:: path.xml
"""

class challenge(docutils.nodes.paragraph,docutils.nodes.Element): pass

def challenge_directive(name, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    return [challenge('', arguments[0])]

challenge_directive.arguments = (1, 0, 0)
challenge_directive.content = False
directives.register_directive('challenge', challenge_directive)



######################################################################
#{ Figure & Example Numbering
######################################################################

# [xx] number examples, figures, etc, relative to chapter?  e.g.,
# figure 3.2?  maybe number examples within-chapter, but then restart
# the counter?

class section_context(docutils.nodes.Invisible, docutils.nodes.Element):
    def __init__(self, context):
        docutils.nodes.Element.__init__(self, '', context=context)
        assert self['context'] in ('body', 'preface', 'appendix')

def section_context_directive(name, arguments, options, content, lineno,
                       content_offset, block_text, state, state_machine):
    return [section_context(name)]
section_context_directive.arguments = (0,0,0)
directives.register_directive('preface', section_context_directive)
directives.register_directive('body', section_context_directive)
directives.register_directive('appendix', section_context_directive)
        
class NumberNodes(Transform):
    """
    This transform adds numbers to figures, tables, and examples; and
    converts references to the figures, tables, and examples to use
    these numbers.  For example, given the rst source::

        .. _my_example:
        .. ex:: John likes Mary.

        See example my_example_.

    This transform will assign a number to the example, '(1)', and
    will replace the following text with 'see example (1)', with an
    appropriate link.
    """
    # dangling = 850; contents = 720.
    default_priority = 800
    def apply(self):
        v = NumberingVisitor(self.document)
        self.document.walkabout(v)
        self.document.reference_labels = v.reference_labels
        self.document.callout_labels = v.callout_labels

class NumberReferences(Transform):
    default_priority = 830
    def apply(self):
        v = ReferenceVisitor(self.document, self.document.reference_labels,
                             self.document.callout_labels)
        self.document.walkabout(v)

        # Save reference info to a pickle file.
        if OUTPUT_FORMAT == 'ref':
            add_to_ref_file(reference_labels=self.document.reference_labels,
                            targets=v.targets)

class NumberingVisitor(docutils.nodes.NodeVisitor):
    """
    A transforming visitor that adds figure numbers to all figures,
    and converts any references to figures to use the text 'Figure #';
    and adds example numbers to all examples, and converts any
    references to examples to use the text 'Example #'.
    """
    LETTERS = 'abcdefghijklmnopqrstuvwxyz'
    ROMAN = 'i ii iii iv v vi vii viii ix x'.split()
    ROMAN += ['x%s' % r for r in ROMAN]
    
    def __init__(self, document):
        docutils.nodes.NodeVisitor.__init__(self, document)
        self.reference_labels = {}
        self.figure_num = 0
        self.table_num = 0
        self.example_num = [0]
        self.section_num = [0]
        self.listing_num = 0
        self.callout_labels = {} # name -> number
        self.set_section_context = None
        self.section_context = 'body' # preface, appendix, body
        
    #////////////////////////////////////////////////////////////
    # Figures
    #////////////////////////////////////////////////////////////

    def visit_figure(self, node):
        self.figure_num += 1
        num = '%s.%s' % (self.format_section_num(1), self.figure_num)
        for node_id in self.get_ids(node):
            self.reference_labels[node_id] = '%s' % num
        self.label_node(node, 'Figure %s' % num)
            
    #////////////////////////////////////////////////////////////
    # Tables
    #////////////////////////////////////////////////////////////

    def visit_table(self, node):
        if 'avm' in node['classes']: return
        if 'gloss' in node['classes']: return
        if 'rst-example' in node['classes']: return
        if 'doctest-list' in node['classes']: return
        self.table_num += 1
        num = '%s.%s' % (self.format_section_num(1), self.table_num)
        for node_id in self.get_ids(node):
            self.reference_labels[node_id] = '%s' % num
        self.label_node(node, 'Table %s' % num)

    #////////////////////////////////////////////////////////////
    # Listings
    #////////////////////////////////////////////////////////////

    def visit_pylisting(self, node):
        self.listing_num += 1
        num = '%s.%s' % (self.format_section_num(1), self.listing_num)
        for node_id in self.get_ids(node):
            self.reference_labels[node_id] = '%s' % num
        pyfile = re.sub('\W', '_', node['name']) + PYLISTING_EXTENSION
        self.label_node(node, 'Listing %s (%s)' % (num, pyfile),
                      PYLISTING_DIR + pyfile)
        self.callout_labels.update(node['callouts'])

    def visit_doctest_block(self, node):
        if isinstance(node.parent, pylisting):
            callouts = node['callouts'] = node.parent['callouts']
        else:
            callouts = node['callouts'] = {}
        
        pysrc = ''.join(('%s' % c) for c in node)
        for callout_id in CALLOUT_RE.findall(pysrc):
            callouts[callout_id] = len(callouts)+1
        self.callout_labels.update(callouts)

    #////////////////////////////////////////////////////////////
    # Sections
    #////////////////////////////////////////////////////////////
    max_section_depth = 3
    no_section_numbers_in_preface = True
    TOP_SECTION = 'chapter'

    # [xx] I don't think this currently does anything..
    def visit_document(self, node):
        if (len(node)>0 and isinstance(node[0], docutils.nodes.title) and
            isinstance(node[0].children[0], docutils.nodes.Text) and
            re.match(r'(\d+(.\d+)*)\.?\s+', node[0].children[0].data)):
                node['sectnum'] = node[0].children[0].data.split()[0]
                for node_id in node.get('ids', []):
                    self.reference_labels[node_id] = '%s' % node['sectnum']

    def visit_section(self, node):
        title = node[0]
        
        # Check if we're entering a new context.
        if len(self.section_num) == 1 and self.set_section_context:
            self.start_new_context(node)

        # Record the section's context in its title.
        title['section_context'] = self.section_context

        # Increment the section counter.
        self.section_num[-1] += 1
        
        # If a section number is given explicitly as part of the
        # title, then it overrides our counter.
        if isinstance(title.children[0], docutils.nodes.Text):
            m = re.match(r'(\d+(.\d+)*)\.?\s+', title.children[0].data)
            if m:
                pieces = [int(n) for n in m.group(1).split('.')]
                if len(pieces) == len(self.section_num):
                    self.section_num = pieces
                    title.children[0].data = title.children[0].data[m.end():]
                else:
                    warning('Explicit section number (%s) does not match '
                         'current section depth' % m.group(1))
                self.prepend_raw_latex(node, r'\setcounter{%s}{%d}' %
                               (self.TOP_SECTION, self.section_num[0]-1))

        # Record the reference pointer for this section; and add the
        # section number to the section title.
        node['sectnum'] = self.format_section_num()
        for node_id in node.get('ids', []):
            self.reference_labels[node_id] = '%s' % node['sectnum']
        if (len(self.section_num) <= self.max_section_depth and
            (OUTPUT_FORMAT != 'latex') and
            not (self.section_context == 'preface' and
                 self.no_section_numbers_in_preface)):
            label = docutils.nodes.generated('', node['sectnum']+u'\u00a0'*3,
                                             classes=['sectnum'])
            title.insert(0, label)
            title['auto'] = 1

        # Record the section number.
        self.section_num.append(0)

        # If this was a top-level section, then restart the figure,
        # table, and listing counters
        if len(self.section_num) == 2:
            self.figure_num = 0
            self.table_num = 0
            self.listing_num = 0

    def start_new_context(self,node):
        # Set the 'section_context' var.
        self.section_context = self.set_section_context
        self.set_section_context = None

        # Update our counter.
        self.section_num[0] = 0

        # Update latex's counter.
        if self.section_context == 'preface': style = 'Roman'
        elif self.section_context == 'body': style = 'arabic'
        elif self.section_context == 'appendix': style = 'Alph'
        raw_latex = (('\n'+r'\setcounter{%s}{0}' + '\n' + 
                      r'\renewcommand \the%s{\%s{%s}}'+'\n') %
               (self.TOP_SECTION, self.TOP_SECTION, style, self.TOP_SECTION))
        if self.section_context == 'appendix':
            raw_latex += '\\appendix\n'
        self.prepend_raw_latex(node, raw_latex)

    def prepend_raw_latex(self, node, raw_latex):
        if isinstance(node, docutils.nodes.document):
            node.insert(0, docutils.nodes.raw('', raw_latex, format='latex'))
        else:
            node_index = node.parent.children.index(node)
            node.parent.insert(node_index, docutils.nodes.raw('', raw_latex,
                                                              format='latex'))
        
    def depart_section(self, node):
        self.section_num.pop()

    def format_section_num(self, depth=None):
        pieces = [('%s' % p) for p in self.section_num]
        if self.section_context == 'body':
            pieces[0] = ('%s' % self.section_num[0])
        elif self.section_context == 'preface':
            pieces[0] = self.ROMAN[self.section_num[0]-1].upper()
        elif self.section_context == 'appendix':
            pieces[0] = self.LETTERS[self.section_num[0]-1].upper()
        else:
            assert 0, 'unexpected section context'
        if depth is None:
            return '.'.join(pieces)
        else:
            return '.'.join(pieces[:depth])
            
            
    def visit_section_context(self, node):
        assert node['context'] in ('body', 'preface', 'appendix')
        self.set_section_context = node['context']
        node.replace_self([])

    #////////////////////////////////////////////////////////////
    # Examples
    #////////////////////////////////////////////////////////////
    NESTED_EXAMPLES = True

    def visit_example(self, node):
        self.example_num[-1] += 1
        node['num'] = self.short_example_num()
        for node_id in self.get_ids(node):
            self.reference_labels[node_id] = self.format_example_num()
        self.example_num.append(0)

    def depart_example(self, node):
        if not self.NESTED_EXAMPLES:
            if self.example_num[-1] > 0:
                # If the example contains a list of subexamples, then
                # splice them in to our parent.
                node.replace_self(list(node))
        self.example_num.pop()

    def short_example_num(self):
        if len(self.example_num) == 1:
            return '(%s)' % self.example_num[0]
        if len(self.example_num) == 2:
            return '%s.' % self.LETTERS[self.example_num[1]-1]
        if len(self.example_num) == 3:
            return '%s.' % self.ROMAN[self.example_num[2]-1]
        else:
            return '%s.' % self.example_num[-1]

    def format_example_num(self):
        """ (1), (2); (1a), (1b); (1a.i), (1a.ii)"""
        ex_num = ('%s' % self.example_num[0])
        if len(self.example_num) > 1:
            ex_num += self.LETTERS[self.example_num[1]-1]
        if len(self.example_num) > 2:
            ex_num += '.%s' % self.ROMAN[self.example_num[2]-1]
        for n in self.example_num[3:]:
            ex_num += '.%s' % n
        return '(%s)' % ex_num

    #////////////////////////////////////////////////////////////
    # Helpers
    #////////////////////////////////////////////////////////////

    def unknown_visit(self, node): pass
    def unknown_departure(self, node): pass

    def get_ids(self, node):
        node_index = node.parent.children.index(node)
        if node_index>0 and isinstance(node.parent[node_index-1],
                                       docutils.nodes.target):
            target = node.parent[node_index-1]
            if target.has_key('refid'):
                refid = target['refid']
                target['ids'] = [refid]
                del target['refid']
                return [refid]
            elif target.has_key('ids'):
                return target['ids']
            else:
                warning('unable to find id for %s' % target)
                return []
        return []

    def label_node(self, node, label, refuri=None, cls='caption-label'):
        if not isinstance(node[-1], docutils.nodes.caption):
            node.append(docutils.nodes.caption())
        caption = node[-1]

        if OUTPUT_FORMAT == 'html':
            cap = docutils.nodes.inline('', label, classes=[cls])
            if refuri:
                cap = docutils.nodes.reference('', '', cap, refuri=refuri,
                                               mimetype='text/x-python')
            caption.insert(0, cap)
            if len(caption) > 1:
                caption.insert(1, docutils.nodes.Text(': '))
        
class ReferenceVisitor(docutils.nodes.NodeVisitor):
    def __init__(self, document, reference_labels, callout_labels):
        self.reference_labels = reference_labels
        self.callout_labels = callout_labels
        self.targets = set()
        docutils.nodes.NodeVisitor.__init__(self, document)
    def unknown_visit(self, node):
        if isinstance(node, docutils.nodes.Element):
            self.targets.update(node.get('names', []))
            self.targets.update(node.get('ids', []))
    def unknown_departure(self, node): pass

    # Don't mess with the table of contents.
    def visit_topic(self, node):
        if 'contents' in node.get('classes', ()):
            raise docutils.nodes.SkipNode

    def visit_reference(self, node):
        node_id = (node.get('refid') or
                   self.document.nameids.get(node.get('refname')) or
                   node.get('refname'))
        if node_id in self.reference_labels:
            label = self.reference_labels[node_id]
            node.clear()
            node.append(docutils.nodes.Text(label))
            expand_reference_text(node)
        elif node_id in self.callout_labels:
            label = self.callout_labels[node_id]
            node.clear()
            node.append(callout_marker(number=label, name='ref-%s' % node_id))
            expand_reference_text(node)
            # There's no explicitly encoded target element, so manually
            # resolve the reference:
            node['refid'] = node_id
            node.resolved = True

_EXPAND_REF_RE = re.compile(r'(?is)^(.*)(%s)\s+$' % '|'.join(
    ['figure', 'table', 'example', 'chapter', 'section', 'appendix',
     'sentence', 'tree', 'listing', 'program']))
def expand_reference_text(node):
    """If the reference is immediately preceeded by the word 'figure'
    or the word 'table' or 'example', then include that word in the
    link (rather than just the number)."""
    if node.get('expanded_ref'):
        assert 0, ('Already expanded!!  %s' % node)
    node_index = node.parent.children.index(node)
    if node_index > 0:
        prev_node = node.parent.children[node_index-1]
        if (isinstance(prev_node, docutils.nodes.Text)):
            m = _EXPAND_REF_RE.match(prev_node.data)
            if m:
                prev_node.data = m.group(1)
                link = node.children[0]
                link.data = '%s %s' % (m.group(2), link.data)
                node['expanded_ref'] = True

######################################################################
#{ Feature Structures (AVMs)
######################################################################

class AVM:
    def __init__(self, ident):
        self.ident = ident
        self.keys = []
        self.vals = {}
    def assign(self, key, val):
        if key in self.keys: raise ValueError('duplicate key')
        self.keys.append(key)
        self.vals[key] = val
    def __str__(self):
        vals = []
        for key in self.keys:
            val = self.vals[key]
            if isinstance(val, AVMPointer):
                vals.append('%s -> %s' % (key, val.ident))
            else:
                vals.append('%s = %s' % (key, val))
        s = '{%s}' % ', '.join(vals)
        if self.ident: s += '[%s]' % self.ident
        return s

    def as_latex(self):
        return '\\begin{avm}\n%s\\end{avm}\n' % self._as_latex()

    def _as_latex(self, indent=0):
        if self.ident: ident = '\\@%s ' % self.ident
        else: ident = ''
        lines = ['%s %s & %s' % (indent*'    ', key,
                                 self.vals[key]._as_latex(indent+1))
                 for key in self.keys]
        return ident + '\\[\n' + ' \\\\\n'.join(lines) + '\\]\n'

    def _entry(self, val, cls):
        if isinstance(val, basestring):
            return docutils.nodes.entry('',
                docutils.nodes.paragraph('', val), classes=[cls])
        else:
            return docutils.nodes.entry('', val, classes=[cls])

    def _pointer(self, ident):
        return docutils.nodes.paragraph('', '', 
                    docutils.nodes.inline(ident, ident,
                                          classes=['avm-pointer']))
    def as_table(self):
        if not self.keys:
            return docutils.nodes.paragraph('', '[]',
                                            classes=['avm-empty'])
        
        rows = []
        for key in self.keys:
            val = self.vals[key]
            key_node = self._entry(key, 'avm-key')
            if isinstance(val, AVMPointer):
                eq_node = self._entry(u'\u2192', 'avm-eq') # right arrow
                val_node = self._entry(self._pointer(val.ident), 'avm-val')
            elif isinstance(val, AVM):
                eq_node = self._entry('=', 'avm-eq')
                val_node = self._entry(val.as_table(), 'avm-val')
            else:
                value = ('%s' % val.val).replace(' ', u'\u00a0') # =nbsp
                eq_node = self._entry('=', 'avm-eq')
                val_node = self._entry(value, 'avm-val')
                
            rows.append(docutils.nodes.row('', key_node, eq_node, val_node))

            # Add left/right bracket nodes:
            if len(self.keys)==1: vpos = 'topbot'
            elif key == self.keys[0]: vpos = 'top'
            elif key == self.keys[-1]: vpos = 'bot'
            else: vpos = ''
            rows[-1].insert(0, self._entry(u'\u00a0', 'avm-%sleft' % vpos))
            rows[-1].append(self._entry(u'\u00a0', 'avm-%sright' % vpos))

            # Add id:
            if key == self.keys[0] and self.ident:
                rows[-1].append(self._entry(self._pointer(self.ident),
                                            'avm-ident'))
            else:
                rows[-1].append(self._entry(u'\u00a0', 'avm-ident'))

        colspecs = [docutils.nodes.colspec(colwidth=1) for i in range(6)]

        tbody = docutils.nodes.tbody('', *rows)
        tgroup = docutils.nodes.tgroup('', cols=3, *(colspecs+[tbody]))
        table = docutils.nodes.table('', tgroup, classes=['avm'])
        return table
    
class AVMValue:
    def __init__(self, ident, val):
        self.ident = ident
        self.val = val
    def __str__(self):
        if self.ident: return '%s[%s]' % (self.val, self.ident)
        else: return '%r' % self.val
    def _as_latex(self, indent=0):
        return '%s' % self.val

class AVMPointer:
    def __init__(self, ident):
        self.ident = ident
    def __str__(self):
        return '[%s]' % self.ident
    def _as_latex(self, indent=0):
        return '\\@{%s}' % self.ident

def parse_avm(s, ident=None):
    lines = [l.rstrip() for l in s.split('\n') if l.strip()]
    if not lines: raise ValueError(0)
    lines.append('[%s]' % (' '*(len(lines[0])-2)))

    # Create our new AVM.
    avm = AVM(ident)
    
    w = len(lines[0]) # Line width
    avmval_pos = None # (left, right, top) for nested AVMs
    key = None        # Key for nested AVMs
    ident = None      # Identifier for nested AVMs
    
    NESTED = re.compile(r'\[\s+(\[.*\])\s*\]$')
    ASSIGN = re.compile(r'\[\s*(?P<KEY>[^\[=>]+?)\s*'
                        r'(?P<EQ>=|->)\s*'
                        r'(\((?P<ID>\d+)\))?\s*'
                        r'((?P<VAL>.+?))\s*\]$')
    BLANK = re.compile(r'\[\s+\]$')

    for lineno, line in enumerate(lines):
        #debug('%s %s %s %r' % (lineno, key, avmval_pos, line))
        if line[0] != '[' or line[-1] != ']' or len(line) != w:
            raise ValueError(lineno)

        nested_m = NESTED.match(line)
        assign_m = ASSIGN.match(line)
        blank_m = BLANK.match(line)
        if not (nested_m or assign_m or blank_m):
            raise ValueError(lineno)
        
        if nested_m or (assign_m and assign_m.group('VAL').startswith('[')):
            left, right = line.index('[',1), line.rindex(']', 0, -1)+1
            if avmval_pos is None:
                avmval_pos = (left, right, lineno)
            elif avmval_pos[:2] != (left, right):
                raise ValueError(lineno)

        if assign_m:
            if assign_m.group('VAL').startswith('['):
                if key is not None: raise ValueError(lineno)
                if assign_m.group('EQ') != '=': raise ValueError(lineno)
                key = assign_m.group('KEY')
                ident = assign_m.group('ID')
            else:
                if assign_m.group('EQ') == '=':
                    avm.assign(assign_m.group('KEY'),
                               AVMValue(assign_m.group('ID'),
                                        assign_m.group('VAL')))
                else:
                    if assign_m.group('VAL').strip(): raise ValueError(lineno)
                    avm.assign(assign_m.group('KEY'),
                               AVMPointer(assign_m.group('ID')))

        if blank_m and avmval_pos is not None:
            left, right, top = avmval_pos
            valstr = '\n'.join(l[left:right] for l in lines[top:lineno])
            avm.assign(key, parse_avm(valstr, ident))
            key = avmval_pos = None
            
    return avm



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
        'stylesheet': CSS_STYLESHEET,
        'stylesheet_path': None,
        'output_encoding': 'unicode',
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
        self.head_prefix.append(COPY_CLIPBOARD_JS)

    def visit_pylisting(self, node):
        self._write_pylisting_file(node)
        self.body.append(self.CODEBOX_HEADER % ('pylisting', 'pylisting'))

    def depart_pylisting(self, node):
        self.body.append(self.CODEBOX_FOOTER)

    def visit_doctest_block(self, node):
        # Collect the text content of the doctest block.
        text = ''.join(('%s' % c) for c in node)
        text = textwrap.dedent(text)
        text = strip_doctest_directives(text)
        text = text.decode('latin1')

        # Colorize the contents of the doctest block.
        if hasattr(node, 'callouts'):
            callouts = node['callouts']
        else:
            callouts = None
        colorizer = HTMLDoctestColorizer(self.encode, callouts)
        if node.get('is_codeblock'):
            pysrc = colorizer.colorize_codeblock(text)
        else:
            try:
                pysrc = colorizer.colorize_doctest(text)
            except:
                print '='*70
                print text
                print '='*70
                raise

        if node.get('is_codeblock'): typ = 'codeblock' 
        else: typ = 'doctest'
        pysrc = self.CODEBOX_ROW % (typ, typ, pysrc)

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
      <tr><td width="1" class="copybar"
              onclick="javascript:copy_%s_to_clipboard(this.nextSibling);"
              >&nbsp;</td>
      <td class="pysrc">%s</td>
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
                out.write(''.join(('%s' % c) for c in child)+'\n\n')
            elif INCLUDE_DOCTESTS_IN_PYLISTING_FILES:
                lines = ''.join(('%s' % c) for c in child).split('\n')
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
        self.body.append('<exercise weight="1" src="')

    def depart_exercise(self, node):
        self.body.append('"/>')

    def visit_challenge(self, node):
        self.body.append('<exercise weight="0" src="')

    def depart_challenge(self, node):
        self.body.append('"/>')

    def visit_literal(self, node):
        """Process text to prevent tokens from wrapping."""
        text = ''.join(('%s' % c) for c in node)
        text = text.decode('latin1')
        colorizer = HTMLDoctestColorizer(self.encode)
        pysrc = colorizer.colorize_inline(text)#.strip()
        #pysrc = colorize_doctestblock(text, self._markup_pysrc, True)
        self.body+= [self.starttag(node, 'tt', '', CLASS='doctest'),
                     '<span class="pre">%s</span></tt>' % pysrc]
        raise docutils.nodes.SkipNode() # Content already processed
                          
    def _markup_pysrc(self, s, tag):
        return '\n'.join('<span class="pysrc-%s">%s</span>' %
                         (tag, self.encode(line))
                         for line in s.split('\n'))

    def visit_example(self, node):
        self.body.append(
            '<p><table border="0" cellpadding="0" cellspacing="0" '
            'class="example">\n  '
            '<tr valign="top"><td width="30" align="right">'
            '%s</td><td width="15"></td><td>' % node['num'])

    def depart_example(self, node):
        self.body.append('</td></tr></table></p>\n')

    def visit_idxterm(self, node):
        self.body.append('<span class="%s">' % ' '.join(node['classes']))
        if 'topic' in node['classes']: raise docutils.nodes.SkipChildren
        
    def depart_idxterm(self, node):
        self.body.append('</span>')

    def visit_index(self, node):
        self.body.append('<div class="index">\n<h1>Index</h1>\n')
        
    def depart_index(self, node):
        self.body.append('</div>\n')

    _seen_callout_markers = set()
    def visit_callout_marker(self, node):
        # Only add an id to a marker the first time we see it.
        add_id = (node['name'] not in self._seen_callout_markers)
        self._seen_callout_markers.add(node['name'])
        if add_id:
            self.body.append('<span id="%s">' % node['name'])
        self.body.append(CALLOUT_IMG % (node['number'], node['number']))
        if add_id:
            self.body.append('</span>')
        raise docutils.nodes.SkipNode() # Done with this node.

    def depart_field_name(self, node):
        # Don't add ":" in callout field lists.
        if 'callout' in node['classes']:
            self.body.append(self.context.pop())
        else:
            HTMLTranslator.depart_field_name(self, node)
    
    def _striphtml_len(self, s):
        return len(re.sub(r'&[^;]+;', 'x', re.sub(r'<[^<]+>', '', s)))

    def visit_caption(self, node):
        if isinstance(node.parent, pylisting):
            self.body.append('<tr><td class="caption">')
        HTMLTranslator.visit_caption(self, node)
        
    def depart_caption(self, node):
        if isinstance(node.parent, pylisting):
            self.body.append('</td></tr>')
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
        CustomizedHTMLWriter.settings_defaults.update()
        header = '.. include:: ' + os.path.join(
            os.path.dirname(inspect.getfile(rst)), 'definitions.txt') + '\n' 
        input = header + input
        output = docutils.core.publish_string(input,
            writer=CustomizedHTMLWriter(), reader=CustomizedReader())
        match = _OUTPUT_RE.search(output)
        if match:
            return "<div>" + match.group(1) + "</div>"
        else:
            raise ValueError('Could not process exercise definition')

    except docutils.utils.SystemMessage, e:
        print 'Fatal error encountered!', e
        raise
        sys.exit(-1)
