function disable_save()
{
    var savebutton = document.getElementById("save_button");
    savebutton.disabled = true;
    window.onbeforeunload = null;
}

function save_file(filename)
{
    if (using_codemirror)
        data = codemirror.getCode();
    else
        data = document.getElementById("editbox").value;

    /* Convert newlines to a single LF (mainly for IE's CRLFs) */
    data = data.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    /* Do NOT refresh the page contents (causes problems for editarea and is
     * unnecessary). */
    if (current_file.svnstatus != "revision" ||
        confirm("You are currently viewing an older version of this file. " +
                "Saving will overwrite the current version. " +
                "Are you sure you want to continue?"))
    {
        do_action("putfile", filename,
                  {"path":".", "data":data, "overwrite":"true"},
                  "multipart/form-data");
        disable_save();
    }
}

function save_file_as(default_filename)
{
    filename = prompt("Path to save to:", default_filename);
    if (!filename) return;

    /* The filename will be path_joined with the app name, so needs to not
     * be absolute, lest it clobber the app name. */
    if (filename.charAt(0) == "/") filename = filename.substring(1);
    ajax_call(save_file_as_callback, "fileservice", filename, {}, "POST");
}

function save_file_as_callback(response)
{
    if (response.status == 404 || confirm("Are you sure you want to overwrite " + filename + "?"))
        save_file(filename);
}

/* Return a warning to be used in window.onbeforeunload. */
function confirm_beforeunload() {
    return 'If you continue, any unsaved changes to the current file will be lost.';
}

function edit_text()
{
    var savebutton = document.getElementById("save_button");
    savebutton.disabled = false;
    window.onbeforeunload = confirm_beforeunload;
}

function highlighting_changed(select)
{
    codemirror_language(select.value);
}

/** Presents the text editor.
 */
function handle_text(path, content_type, url_args)
{
    /* Need to make a 2nd ajax call, this time get the actual file
     * contents */
    callback = function(response)
        {
            /* Read the response and set up the page accordingly */
            handle_text_response(path, content_type, response.responseText);
        }
    /* Call the server and request the listing. */
    if (url_args)
        args = shallow_clone_object(url_args);
    else
        args = {};
    /* This time, get the contents of the file, not its metadata */
    args['return'] = "contents";
    ajax_call(callback, service_app, path, args, "GET");
}

function handle_text_response(path, content_type, response_text)
{
    /* Create a textarea with the text in it
     * (The makings of a primitive editor).
     */
    var files = document.getElementById("filesbody");

    var div = document.createElement("div");
    div.style.height = '100%';
    files.appendChild(div);
    var txt_elem = document.createElement("textarea");
    txt_elem.value = response_text.toString();
    div.appendChild(txt_elem);
    txt_elem.setAttribute("id", "editbox");
    language = language_from_mime(content_type);

    // Assume plaintext if no type can be determined.
    language = language ? language : "text";
    document.getElementById("highlighting_select").value = language;

    $(txt_elem).change(edit_text);

    /* This isn't ideal, as Opera seems to fire it even for non-textual keys.
     * But IE and WebKit don't, so this will behave properly in most browsers.
     * This makes me sad.
     */
    $(txt_elem).keypress(edit_text);

    txt_elem.style.width = "100%";
    txt_elem.style.height = "100%";
    window.onbeforeunload = confirm_beforeunload;

    /* Always use CodeMirror (unless we find a good reason not to!) */
    using_codemirror = true;

    if (using_codemirror)
    {
        /* CodeMirror */
        using_codemirror = true;
        codemirror = new CodeMirror.fromTextArea(txt_elem, {
            path: codemirrorpath,
            stylesheet: [
                    codemirrorpath + "/contrib/python/css/pythoncolors.css",
                    codemirrorpath + "/css/xmlcolors.css",
                    codemirrorpath + "/css/jscolors.css",
                    codemirrorpath + "/css/csscolors.css"
                    ],
            basefiles: ["js/util.js",
                    "js/stringstream.js",
                    "js/select.js",
                    "js/undo.js",
                    "js/editor.js",
                    "js/tokenize.js"
                    ],
            parserfile: ["contrib/python/js/parsepython.js",
                    "js/parsexml.js",
                    "js/parsecss.js",
                    "js/tokenizejavascript.js",
                    "js/parsejavascript.js",
                    "js/parsehtmlmixed.js",
                    "js/parsedummy.js"
                    ],
            onChange: edit_text,
            indentUnit: 4,
            tabMode: "spaces",
            lineNumbers: true,
            initCallback: function() {codemirror_language(language);},
            saveFunction: function() {document.getElementById("save_button").click();}
        });

    }

    /* Not using CodePress, so we can already disable the Save button. */
    disable_save();

}

function codemirror_language(lang)
{
    if(lang == 'python') {
        codemirror.setParser("PythonParser")
    } else if(lang == 'html') {
        codemirror.setParser("HTMLMixedParser")
    } else if(lang == 'css') {
        codemirror.setParser("CSSParser")
    } else if(lang == 'javascript') {
        codemirror.setParser("JSParser")
    } else {
        codemirror.setParser("DummyParser")
    }

    // Show actions bar
    $("#actions2_file").show();
}

function language_from_mime(mime)
{
    return {'text/x-python': 'python',
            'application/x-javascript': 'javascript',
            'application/javascript': 'javascript',
            'text/css': 'css',
            'text/plain': 'text',
            'text/html': 'html',
            'application/xml': 'html',
            'application/xhtml+xml': 'html'}[mime];
}
