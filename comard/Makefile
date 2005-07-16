
CC= gcc
PYTHON_CFLAGS= -I/usr/include/python2.3/
PYTHON_LIBS= `python-config` -Xlinker -export-dynamic \
	-lnsl -ldl -lieee -lpthread -lutil
CFLAGS= -O2 -Wall -Iinclude -DVERSION='"1.0"' $(PYTHON_CFLAGS)

OBJS = \
	src/main.o \
	src/cfg.o \
	src/log.o \
	src/job.o \
	src/model.o \
	src/process.o \
	src/csl.o \
	src/data.o \
	src/rpc_unix.o \
	src/iksemel.o

comar: $(OBJS)
	$(CC) -o $@ $(OBJS) -ldb $(PYTHON_LIBS)

clean:
	rm -f comar src/*.o
