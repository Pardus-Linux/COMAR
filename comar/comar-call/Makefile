CC= gcc
CFLAGS= -Wall -O2 -I.
OBJS= main.o rpc.o

comar-call: $(OBJS) rpc.h
	$(CC) -o comar-call $(OBJS)

clean:
	rm -f *.o comar-call
