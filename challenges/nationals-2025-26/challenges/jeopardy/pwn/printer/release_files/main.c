#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>
#include <inttypes.h>

FILE* fp;
void* STACK_START;
void* STACK_END;
char* STACK_STR = "[stack]";

void** va_ith(va_list ap, int64_t i) {
    i++;
    if(1 <= i && i <= 5) {
        return (void**)(ap->reg_save_area + i * 8);
    }
    return (void**)(ap->overflow_arg_area + (i - 6) * 8);
}

const char* _printt_offset(const char* fmt, va_list ap, FILE* fp, void*** p, int* has_offset) {
    switch(*fmt) {
        case '+':
            *has_offset = 1;
            fmt++;
            // Parse the int
            int off = strtoimax(fmt, (char**)&fmt, 10);
            fmt = _printt_offset(fmt, ap, fp, p, has_offset);
            *p = (void**)(**p + off);
        default:
            break;
    }
    return fmt;
}

const char* _printt_specifier(const char* fmt, va_list ap, FILE* fp, void*** p, int* cur_pos, int* has_offset) {
    switch(*fmt) {
        case '$':
            fmt++;
            // Parse the int
            *cur_pos = strtoimax(fmt, (char**)&fmt, 10);
            // Fallthrough
        default:
            *p = va_ith(ap, *cur_pos-1);
            (*cur_pos)++;
            break;
    }
    return _printt_offset(fmt, ap, fp, p, has_offset);
}


const char* _printt_term(const char* fmt, va_list ap, FILE* fp, int* cur_pos) {
    void** res = NULL;
    int has_offset = 0;
    fmt = _printt_specifier(fmt, ap, fp, &res, cur_pos, &has_offset);
    switch(*fmt++) {
        case 'd':
            fprintf(fp, "%d", *res);
            break;
        case 'l':
            fprintf(fp, "%lld", *res);
            break;
        case 'p':
            fprintf(fp, "%p", *res);
            break;
        case 's':
            fprintf(fp, "%s", *res);
            break;
        case 'c':
            fprintf(fp, "%c", *res);
            break;
        case 'n':
            if(has_offset) {
                break;
            }
            char** res_p = (char**)res;
            if(STACK_START <= res && res <= STACK_END) {
                puts(">:(");
                exit(1);
            }
            int sz = ftell(fp);
            *res_p = malloc(sz+1);
            rewind(fp);
            fread(*res_p, 1, sz, fp);
            (*res_p)[sz] = 0;
            break;
        default:
            break;
    }
    return fmt;
}

void _fprintt(const char* fmt, va_list ap, FILE* fp) {
    int cur_pos = 1;
    while(*fmt) {
        if(*fmt == '!') {
            fmt++;
            switch(*fmt) {
                case '!':
                    putc('!', fp);
                    fmt++;
                    break;
                default:
                    fmt = _printt_term(fmt, ap, fp, &cur_pos);
                    break;

            }
        } else {
            putc(*fmt++, fp);
        }
    }
}

int _printt(const char* fmt, va_list ap) {
    fp = tmpfile();
    if(fp == NULL) exit(1);
    _fprintt(fmt, ap, fp);
    rewind(fp);
    int ch;
    while ((ch = fgetc(fp)) != EOF) {
        fputc(ch, stdout);
    }
    fclose(fp);
    fp = NULL;
}

int printt(const char* fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    int ret = _printt(fmt, ap);
    va_end(ap);
    return ret;
}

int init() {
    setbuf(stdin, NULL);
    setbuf(stdout, NULL);
    // TODO: setvbuf stuff
    FILE* f = fopen("/proc/self/maps", "r");
    if(f == NULL) return -1;
    char* line = NULL;
    size_t len = 0;
    size_t nread;
    while((nread = getline(&line, &len, f)) != -1) {
        if(strncmp(line + nread - 1 - strlen(STACK_STR), STACK_STR, strlen(STACK_STR)) == 0) {
            sscanf(line, "%p-%p", &STACK_START, &STACK_END);
            fclose(f);
            f = NULL;
            return 0;
        }
    }
    return -1;
}

int main() {
    if(init()) {
        puts("Error");
        return 1;
    }
    printt("Printer 1.0\n");
    char buf[0x1000];
    while(1) {
        printt("> ");
        fgets(buf, sizeof(buf), stdin);
        printt(buf);
    }
}