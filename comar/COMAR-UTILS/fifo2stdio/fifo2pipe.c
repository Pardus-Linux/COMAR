#include <stdio.h>
#include <unistd.h>
#include <locale.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ipc.h>
#include <sys/shm.h>

int file;
int stdio_read, stdio_write, semid, shmid;
char *shmbuffer;
key_t shmkey;

void read_process(int sig) {
}

void write_process(int sig) {
}

int main(int argc, char **argv) {    
    char filename[1024];
    char oldfname[1024];
    struct stat st;
    int i, x;
    int extflags = 0;
        
    if (argc != 3) {
        perror("FIFO/DEVICE to STDIO Bridge for COMAR Applications.\nPlease read COMAR Documentation for details\nUsage:\n\tfifo2stdio shm_key filename\nStatus:");
        return 1;
    }
    setlocale(LC_ALL, "POSIX");
    if (lstat(argv[2], &st)) {
	perror("File cannot stat");
	return errno;
    }
    strncpy(filename, argv[2], 1024);
    strncpy(oldfname, filename, 1024);
    
    while (S_ISLNK(st.st_mode)) {
    	/* Symlink */	
	i = readlink(oldfname, filename, 1024);
	if (i == -1) {
	    perror("Cannot stat symlink ");
	    return errno;
	}
	filename[i] = 0;
	if (filename[0] != '/') {
	    x = strlen(oldfname) - 1;
	    while (x--) {
		if (oldfname[x] == '/') {
		    x++;
		    oldfname[x] = 0;
		    break;
		}
	    }
	    strncat(&oldfname[x], filename, 1024);
	} else {
	    strncpy(oldfname, filename, 1024);
	}
	printf("FSTAT: %s\n", oldfname);	
	if (lstat(oldfname, &st)) {
	    printf("FN: %s\n", oldfname);
	    perror("Broken Symlink ");
	    return errno;
	}
    }
    
    if (S_ISREG(st.st_mode) || S_ISDIR(st.st_mode) || S_ISBLK(st.st_mode)) {
	perror("Regular Files/Block Devices cannot be used with fifo2stdio ");
	return 1025;
    }
    extflags |= O_ASYNC;    
    printf("ST DEV: %d ST RDEV: %d\n", st.st_dev, st.st_rdev);
    extflags |= O_NOCTTY;
    
    printf("Open File: %s\n", oldfname);
    
    /* Test SHMEM Segment for exist ? */
    
    shmkey = atoi(argv[1]);
    printf("Seek SHM Segment: %d\n", shmkey);
    shmid = shmget(shmkey, 4096, 0666);    
    printf("SHMGET Returned: %d\n", shmid);
    if (shmid == -1) {
	perror("Cannot open IPC Segment ");
	return 1026;
    }
    semid = semget(shmkey, 0, 0666);
    if (shmid == -1) {
	perror("Cannot open IPC Semaphore ");
	return 1027;
    }
    
    daemon(0,0);
    
    
}
