
/** Presents the text editor.
 */
function handle_text(path, text, handler_type)
{
    /* Create a textarea with the text in it
     * (The makings of a primitive editor).
     */

    setmode(true);
    var files = document.getElementById("filesbody");
    var div = document.createElement("div");
    files.appendChild(div);
    div.setAttribute("class", "padding");
    /* First, print a warning message if this is not actually a text file.
     */
    if (handler_type != "text")
    {
        var warn = dom_make_text_elem("p",
            "Warning: You are editing a binary " +
            "file, which explains any strange characters you may see. If " +
            "you save this file, you could corrupt it.");
        div.appendChild(warn);
    }
    var txt_elem = dom_make_text_elem("textarea",
        text.toString())
    div.appendChild(txt_elem);
    txt_elem.setAttribute("id", "editbox");
    /* TODO: Make CSS height: 100% work */
    txt_elem.setAttribute("rows", "20");
}

