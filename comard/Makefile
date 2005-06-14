
CC= gcc
PYTHON_CFLAGS= -I/usr/include/python2.3/
PYTHON_LIBS= `python-config` -Xlinker -export-dynamic \
	-lnsl -ldl -lieee -lpthread -lutil
CFLAGS= -O2 -Wall -Iinclude $(PYTHON_CFLAGS)

OBJS = \
	src/main.o \
	src/csl.o

comard: $(OBJS)
	$(CC) -o $@ $(OBJS) $(PYTHON_LIBS)

clean:
	rm -f comard *.o
