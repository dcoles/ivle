saved_status = null;

function save_file()
{
    filename = document.getElementById("save_filename").value;
    data = editAreaLoader.getValue("editbox");
    /* Do NOT refresh the page contents (causes problems for editarea and is
     * unnecessary). */
    do_action("putfile", filename, {"path":".", "data":data}, null, true);
    saved_status.data = "Saved.";
}

function edit_text()
{
    saved_status.data = "Not saved.";
}

/** Presents the "editor heading" (the part with the save box)
 * inserting it into a given element at the front.
 */
function present_editorhead(elem, path, handler_type)
{
    var div = document.createElement("div");
    /* Insert as the head element */
    elem.insertBefore(div, elem.firstChild)
    div.setAttribute("id", "editorhead");

    /* Set up minimal interface */
    var p = dom_make_text_elem("p", "Path: ");
    var pathname = document.createElement("input");
    pathname.setAttribute("type", "text");
    pathname.setAttribute("size", "30");
    pathname.setAttribute("id", "save_filename");
    pathname.setAttribute("value", path);
    p.appendChild(pathname);
    var savebutton = document.createElement("input");
    savebutton.setAttribute("type", "button");
    savebutton.setAttribute("value", "Save");
    savebutton.setAttribute("onclick", "save_file()");
    p.appendChild(savebutton);
    var t = document.createTextNode(" ");
    p.appendChild(t);
    saved_status = document.createTextNode("Saved.");
    //p.appendChild(saved_status);
    div.appendChild(p);

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
    files.appendChild(div);
    var txt_elem = dom_make_text_elem("textarea",
        text.toString())
    div.appendChild(txt_elem);
    txt_elem.setAttribute("id", "editbox");
    txt_elem.setAttribute("onchange", "edit_text()");
    /* TODO: Make CSS height: 100% work */
    txt_elem.setAttribute("rows", "35");

    /* Load EditArea into the editbox */
    editAreaLoader.init({
        id : "editbox",
        syntax: "python",
        toolbar: "search, go_to_line, |, undo, redo, |, select_font, |, syntax_selection, |, highlight, |, help",
        start_highlight: true,
        allow_toggle: false,
        allow_resize: false,
        replace_tab_by_spaces: 4
    });
}

