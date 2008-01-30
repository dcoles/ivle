#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "norm.h"

int main(int argc, const char* argv[])
{
    char buf[256];

    assert(norm(buf,256, "/usr/bin/python") == 0);
    assert(strcmp(buf,"/usr/bin/python") == 0);

    assert(norm(buf,256, "/usr/./bin/./python") == 0);
    assert(strcmp(buf,"/usr/bin/python") == 0);

    assert(norm(buf,256, "/x/../python") == 0);
    assert(strcmp(buf,"/python") == 0);

    assert(norm(buf,256, "/../python") != 0);

    return 0;
}
