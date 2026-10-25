#pragma once
#include <stddef.h>
typedef struct probe_FILE FILE;
extern FILE *stdin, *stdout, *stderr;
#define EOF (-1)
#define SEEK_SET 0
#define SEEK_CUR 1
#define SEEK_END 2
int fprintf(FILE *, const char *, ...);
int printf(const char *, ...);
int fputs(const char *, FILE *);
int fclose(FILE *);
int fseek(FILE *, long, int);
long ftell(FILE *);
size_t fread(void *, size_t, size_t, FILE *);
size_t fwrite(const void *, size_t, size_t, FILE *);
