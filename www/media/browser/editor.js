function disable_save_if_safe()
{
    /* If this is defined, this engine supports change notification, so is able
     * to enable the button again. Disable it for them. */
    if(editbox.editor.addChangeHandler)
    {
        var savebutton = document.getElementById("save_button");
        savebutton.disabled = true;
    }
}

function save_file(filename)
{
    data = editbox.getCode();
    /* Do NOT refresh the page contents (causes problems for editarea and is
     * unnecessary). */
    do_action("putfile", filename,
              {"path":".", "data":data, "overwrite":"true"},
              "multipart/form-data", true);
    disable_save_if_safe();
}

function save_file_as(default_filename)
{
    filename = prompt('Path to save to:', default_filename);
    /* TODO: Confirm overwriting. */
    save_file(filename);
}

function edit_text()
{
    var savebutton = document.getElementById("save_button");
    savebutton.disabled = false;
}

/** Presents the "editor heading" inserting it into a given element at
 *  the front. Note that the save widget is handled by the Python.
 */
function present_editorhead(elem, path, handler_type)
{
    var div = document.getElementById("actions2");

    /* Print a warning message if this is not actually a text file.
     */
    if (handler_type != "text")
    {
        var warn = dom_make_text_elem("p",
            "Warning: You are editing a binary " +
            "file, which explains any strange characters you may see. If " +
            "you save this file, you could corrupt it.");
        div.appendChild(warn);
    }
}

/** Presents the text editor.
 */
function handle_text(path, text, handler_type)
{
    /* Create a textarea with the text in it
     * (The makings of a primitive editor).
     */
    var files = document.getElementById("filesbody");
    /* Put our UI at the top */
    present_editorhead(files, path, handler_type);

    var div = document.createElement("div");
    div.style.height = '100%';
    files.appendChild(div);
    var txt_elem = dom_make_text_elem("textarea",
        text.toString())
    div.appendChild(txt_elem);
    txt_elem.setAttribute("id", "editbox");
    language = language_from_mime(current_file.type)

    // Assume plaintext if no type can be determined.
    txt_elem.className = "codepress " + (language ? language : 'text');
    txt_elem.setAttribute("onchange", "edit_text()");
    /* TODO: Make CSS height: 100% work */
    txt_elem.setAttribute("rows", "35");
    CodePress.run();

    /* And set a callback so we know that the editor iframe is loaded so we
     * can set a callback so we know when to enable the save button.
     * We also take this opportunity to disable the save button, if
     * the browser is likely to reenable it as needed. */
    editbox.onload = function() {editbox.addChangeHandler(edit_text);
                                 disable_save_if_safe(); };
}

function language_from_mime(mime)
{
    return {'text/x-python': 'python',
            'application/javascript': 'javascript',
            'text/css': 'css',
            'text/plain': 'text',
            'text/html': 'html',
            'application/xhtml+xml': 'html'}[mime];
}
