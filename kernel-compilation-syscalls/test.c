#include "/usr/include/lib.h"
#include "/usr/include/minix/type.h"
#include <stdio.h>
#include <stdlib.h>

int getprocnr(int pid) {
	message m;
	m.m1_i1 = pid;
	return _syscall(MM, GETPROCNR, &m);
}


int main(int argc, char* argv[])
{
    int pid, stop, ret_val;

    if(argc != 2) {
    	pid = 1;
        printf("Give argument - PID number!\nResults assuming pid = 1:\n");
    }
    else {
        pid = atoi(argv[1]);
    }
    stop = pid + 10;

    for (; pid <= stop; pid++){
        ret_val = getprocnr(pid);
        if(ret_val >= 0){
            printf("pid = %d, index = %d\n", pid, ret_val);
        }
        else {
            fprintf(stderr, "Error %d: Entry for pid %d not found\n", errno, pid);
        }
    }
    return 0;
}
