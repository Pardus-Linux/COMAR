libcomar: 
	  gcc -fPIC -g3 -c -Wall libcomar.c
	  gcc -shared -Wl,-soname,libcomar.so.1 \
	      -o libcomar.so.1.0.0 libcomar.o
install:
	rm -f /usr/lib/libcomar.so.1.0.0 /usr/include/comar.h /usr/lib/libcomar.so
	cp libcomar.so.1.0.0 /usr/lib
	ln -s /usr/lib/libcomar.so.1.0.0 /usr/lib/libcomar.so
	cp libcomar.h /usr/include/comar.h

