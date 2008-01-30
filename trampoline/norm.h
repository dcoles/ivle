#ifndef NORM_H
#define NORM_H

/*
 * Normalize the unix pathname in src eliminating .. sequences
 * to yield an absolute path. Returns 0 on success, and -1 on
 * error.
 */
int norm(char* dest, int len, const char* src);

#endif /* NORM_H */
