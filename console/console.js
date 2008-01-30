var magic = 'xyzzy';

function historyUp()
{
    if (this.cursor >= 0)
    {
        this.cursor--;
    }
}

function historyDown()
{
    if (this.cursor < this.items.length)
    {
        this.cursor++;
    }
}

function historyCurr()
{
    if (this.cursor < 0 || this.cursor >= this.items.length)
    {
        return "";
    }
    return this.items[this.cursor];
}

function historyAdd(text)
{
    this.items[this.items.length] = text;
    this.cursor = this.items.length;
}

function historyShow()
{
    var res = "";
    if (this.cursor == -1)
    {
        res += "[]";
    }
    for (var i = 0; i < this.items.length; i++)
    {
        if (i == this.cursor)
        {
            res += "["
        }
        res += this.items[i].toString();
        if (i == this.cursor)
        {
            res += "]"
        }
        res += " "
    }
    if (this.cursor == this.items.length)
    {
        res += "[]";
    }
    return res;
}

function History()
{
    this.items = new Array();
    this.cursor = -1;
    this.up = historyUp;
    this.down = historyDown;
    this.curr = historyCurr;
    this.add = historyAdd;
    this.show = historyShow;
}

var hist = new History();

function make_post_body(args)
{
    var qs = '';
    for (key in args)
    {
        vals = args[key];
        // vals can be an array, to make multiple args with the same name
        // To handle this, make non-array objects into an array, then loop
        if (!(vals instanceof Array))
            vals = [vals];
        var i;
        for (i=0; i<vals.length; i++)
        {
            if (i > 0)
            {
                qs += "&";
            }
            qs += encodeURIComponent(key) + "=" + encodeURIComponent(vals[i]);
        }
    }
    return qs;
}

function enter_line()
{
    var inp = document.getElementById('inputText');
    var digest = hex_md5(inp.value + magic);
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open("POST", "chat", false);
    xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xmlhttp.send(make_post_body({"digest":digest, "text":inp.value}))
    var res = JSON.parse(xmlhttp.responseText);
    var output = document.getElementById("output");
    {
        var pre = document.createElement("pre");
        pre.setAttribute("class", "inputMsg");
        pre.appendChild(document.createTextNode(inp.value + "\n"));
        output.appendChild(pre);
    }
    if (res.hasOwnProperty('okay'))
    {
        // Success!
        // print out the output (res.okay[0])
        var pre = document.createElement("pre");
        pre.setAttribute("class", "outputMsg");
        pre.appendChild(document.createTextNode(res.okay[0]));
        output.appendChild(pre);
        // print out the return value (res.okay[1])
        if (res.okay[1])
        {
            var pre = document.createElement("pre");
            pre.setAttribute("class", "outputMsg");
            pre.appendChild(document.createTextNode(res.okay[1] + "\n"));
            output.appendChild(pre);
        }
        // set the prompt to >>>
        var prompt = document.getElementById("prompt");
        prompt.replaceChild(document.createTextNode(">>> "), prompt.firstChild);
    }
    else if (res.hasOwnProperty('exc'))
    {
        // Failure!
        // print out any output that came before the error
        if (res.exc[0].length > 0)
        {
            var pre = document.createElement("pre");
            pre.setAttribute("class", "outputMsg");
            pre.appendChild(document.createTextNode(res.exc[0]));
            output.appendChild(pre);
        }

        // print out the error message (res.exc)
        var pre = document.createElement("pre");
        pre.setAttribute("class", "errorMsg");
        pre.appendChild(document.createTextNode(res.exc[1]));
        output.appendChild(pre);
    }
    else if (res.hasOwnProperty('more'))
    {
        // Need more input, so set the prompt to ...
        var prompt = document.getElementById("prompt");
        prompt.replaceChild(document.createTextNode("... "), prompt.firstChild);
    }
    else {
        // assert res.hasOwnProperty('input')
        var prompt = document.getElementById("prompt");
        prompt.replaceChild(document.createTextNode("+++ "), prompt.firstChild);
    }
}

function catch_input(key)
{
    var inp = document.getElementById('inputText');
    if (key == 13)
    {
        enter_line();
        hist.add(inp.value);
        inp.value = hist.curr();
    }
    if (key == 38)
    {
        hist.up();
        inp.value = hist.curr();
    }
    if (key == 40)
    {
        hist.down();
        inp.value = hist.curr();
    }
}
