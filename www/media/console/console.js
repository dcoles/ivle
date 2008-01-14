digest_constant = "hello";

/* Starts the console server.
 * Returns an object with fields "host", "port", "magic" describing the
 * server.
 */
function start_server()
{
    var xhr = ajax_call("consoleservice", "", "", "POST");
    var json_text = xhr.responseText;
    return JSON.parse(json_text);
}

function onload()
{
    var consolebody = document.getElementById("consolebody");
    var iframe = document.createElement("iframe");
    consolebody.appendChild(iframe);
    iframe.setAttribute("width", "100%");
    /* TODO: Height 100%, once CSS is working */
    iframe.setAttribute("height", "600px");

    /* Start the server */
    var server_info = start_server();

    var digest = hex_md5(digest_constant + server_info.magic);

    var url = "http://"
        + server_info.host.toString() + ":"
        + server_info.port.toString() + "?digest=" + digest;

    iframe.setAttribute("src", url);
}
