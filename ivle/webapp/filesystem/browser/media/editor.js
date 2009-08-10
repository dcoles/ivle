function disable_save_if_safe()
{
    /* If we are using CodePress, we can only safely disable the save button
     * (indicating that there are no changes to save) if the engine supports
     * change notification, so the button can be enabled again.
     *
     * Our non-CodePress mode just uses normal textarea events, so is always
     * fine.
     */
    if((!using_codepress) || editbox.editor.addChangeHandler)
    {
        var savebutton = document.getElementById("save_button");
        savebutton.disabled = true;
        window.onbeforeunload = null;
    }
}

function save_file(filename)
{
    data = editbox.getCode();
    /* Do NOT refresh the page contents (causes problems for editarea and is
     * unnecessary). */
    if (current_file.svnstatus != "revision" ||
        confirm("You are currently viewing an older version of this file. " +
                "Saving will overwrite the current version. " +
                "Are you sure you want to continue?"))
    {
        do_action("putfile", filename,
                  {"path":".", "data":data, "overwrite":"true"},
                  "multipart/form-data", true);
        disable_save_if_safe();
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

function highlighting_changed(select)
{
    editbox.edit(editbox.getCode(), select.value);
}

function initialise_codepress()
{
    editbox.addChangeHandler(edit_text);
    editbox.addSaveHandler(function() {document.getElementById("save_button").click()});
     
    /* We can only safely disable the save button on the first load.
     * Syntax highlighting changes will also get this function called.
     * We unfortunately need the change handler added each time.
     */
    if (!initialise_codepress.already)
    {
        disable_save_if_safe();
        initialise_codepress.already = true;
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
    language = language_from_mime(current_file.type);

    // Assume plaintext if no type can be determined.
    language = language ? language : "text";
    document.getElementById("highlighting_select").value = language;

    txt_elem.setAttribute("onchange", "edit_text()");
    txt_elem.style.width = "100%";
    txt_elem.style.height = "100%";
    window.onbeforeunload = confirm_beforeunload;

    /* XXX: Lord, please forgive me for browser sniffing.
            CodePress only works properly in real Gecko at the moment,
            so we must go to great and evil lengths to sniff it out.
            It's by no means a complete check, but it has to support
            more browsers than the previous situation.
            This should be killed ASAP when we fix/replace CodePress.
     */
    using_codepress = (navigator.userAgent.match('Gecko') &&
                       !navigator.userAgent.match('WebKit') &&
                       !navigator.userAgent.match('Presto'))

    if (using_codepress)
    {
        /* This is probably real Gecko. Try to fire up CodePress.
         * If it fails we'll have a horrible mess, so we'll hope.
         */
        txt_elem.className = "codepress autocomplete-off " + language;
        CodePress.run();

        /* And set a callback so we know that the editor iframe is loaded so
         * we can set a callback so we know when to enable the save button.
         * We also take this opportunity to disable the save button, if
         * the browser is likely to reenable it as needed. */
        editbox.onload = initialise_codepress;
    }
    else
    {
        /* Not using CodePress, so we can already disable the Save button. */
        disable_save_if_safe();
    }
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
