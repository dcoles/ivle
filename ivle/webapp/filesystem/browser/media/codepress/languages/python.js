/*
 * CodePress regular expressions for Python syntax highlighting
 */
 
// Python
Language.syntax = [ 
	{ input : /(\'\'\')(.*?)(\'\'\')/mg, output : '<s>$1$2$3</s>' }, // strings triple-single quote
	{ input : /(\"\"\")(.*?)(\"\"\")/mg, output : '<s>$1$2$3</s>' }, // strings triple-single quote
	{ input : /\"(.*?)(\"|<br>|<\/P>)/g, output : '<s>"$1$2</s>' }, // strings double quote
	{ input : /\'(.*?)(\'|<br>|<\/P>)/g, output : '<s>\'$1$2</s>' }, // strings single quote
	{ input : /\b(break|continue|del|except|exec|finally|pass|print|raise|return|try|with|global|assert|lambda|yield|def|class|for|while|if|elif|else|and|in|is|not|or|import|from|as)\b/g, output : '<b>$1</b>' }, // reserved words
	{ input : /\b(True|False|bool|enumerate|set|frozenset|help|reversed|sorted|sum|Ellipsis|None|NotImplemented|__import__|abs|apply|buffer|callable|chr|classmethod|cmp|coerce|compile|complex|delattr|dict|dir|divmod|eval|execfile|file|filter|float|getattr|globals|hasattr|hash|hex|id|input|int|intern|isinstance|issubclass|iter|len|list|locals|long|map|max|min|object|oct|open|ord|pow|property|range|raw_input|reduce|reload|repr|round|setattr|slice|staticmethod|str|super|tuple|type|unichr|unicode|vars|xrange|zip)\b/g, output : '<u>$1</u>' }, // special words
	{ input : /([^:]|^)#(.*?)(<br|<\/P)/g, output : '$1<i>#$2</i>$3' }, // comments //
]

Language.snippets = [
]

Language.complete = [
	{ input : '\'',output : '\'$0\'' },
	{ input : '"', output : '"$0"' },
	{ input : '(', output : '\($0\)' },
	{ input : '[', output : '\[$0\]' },
	{ input : '{', output : '{\n\t$0\n}' }		
]

Language.shortcuts = []
