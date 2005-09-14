
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <arpa/inet.h>
#include <net/route.h>
#include <iwlib.h>
#include <wireless.h>

#include <Python.h>

static int
comarnet_socketsOpen(void)
{
  static const int families[] = {
    AF_INET, AF_IPX, AF_AX25, AF_APPLETALK
  };
  unsigned int  i;
  int sock;

  for(i = 0; i < sizeof(families)/sizeof(int); ++i)
    {
      sock = socket(families[i], SOCK_DGRAM, 0);
      if(sock >= 0)
	return sock;
    }

  return -1;
}


static int
comarnet_setInterface(PyObject *self, PyObject *args)
{
  struct ifreq ifr;
  struct sockaddr_in sin;
  int skfd;
  int ret = 0;
  char *dev, *ip, *bc, *nm;

  ret =  PyArg_ParseTuple(args, "ssss", &dev, &ip, &bc, &nm);

  skfd = comarnet_socketsOpen();
  if ( skfd < 0 )
    return PyInt_FromLong( (long) -1 );

  // setup device flags, which also enables (up) device
  strcpy( ifr.ifr_name, dev );
  ifr.ifr_flags = IFF_UP;
  ifr.ifr_flags |= IFF_RUNNING;
  ifr.ifr_flags |= IFF_BROADCAST;
  ifr.ifr_flags |= IFF_MULTICAST;
  ifr.ifr_flags &= ~IFF_NOARP;
  ifr.ifr_flags &= ~IFF_PROMISC;
  if ( ioctl( skfd, SIOCSIFFLAGS, &ifr ) < 0 ) {
    ret = -1;
  }

  memset( &sin, 0, sizeof( struct sockaddr ) );
  sin.sin_family = AF_INET;

  inet_aton( ip, &(sin.sin_addr) );
  memcpy( &ifr.ifr_addr, &sin, sizeof( struct sockaddr ));
  if ( ioctl( skfd, SIOCSIFADDR, &ifr ) < 0 ) {
    ret = -1;
  }

  return PyInt_FromLong( (long) ret );
}

static PyMethodDef comarnet_methods[] = {
  {"socketsOpen", comarnet_socketsOpen, METH_VARARGS, NULL},
  {"setInterface", comarnet_setInterface, METH_VARARGS, NULL},
  {NULL, NULL}
};

PyMODINIT_FUNC
initcomarnet(void)
{
  PyObject *m;
        
  m = Py_InitModule("comarnet", comarnet_methods);

  return;
}
