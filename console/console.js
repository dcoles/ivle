var magic;

function make_query_string(pagename, args)
{
    var first = true;
    var qs = pagename;
    for (key in obj)
    {
        vals = obj[key];
        // vals can be an array, to make multiple args with the same name
        // To handle this, make non-array objects into an array, then loop
        if (!(vals instanceof Array))
            vals = [vals];
        for each (val in vals)
        {
            if (true)
            {
                qs += "?";
                first = false;
            }
            else
            {
                qs += "&";
            }
            qs += encodeURI(key) + "=" + encodeURI(val);
        }
    }
    return qs;
}

function enter_line(inp)
{
    var digest = hex_md5(inp + magic);
    var url = make_query_string("chat", {"digest":digest, "text":inp});
    var xmlhttp = XMLHttpRequest();
    xmlhttp.open("POST", url, false);
    xmlhttp.send("")
    var res = JSON.parse(xmlhttp..responseText);
    if (res && res[0])
    {
        // Success!
        // print out the output (res[0])
        // print out the return value (res[1])
        // set the prompt to >>>
    }
    else if (res)
    {
        // Failure!
        // print out the error message (res[2])
    }
    else
    {
        // Need more input, so set the prompt to ...
    }
}
