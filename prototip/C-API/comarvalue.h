/*

	COMARValue.h
	Prototype and structures for COMARValue.

*/
#ifndef	__COMARVALUE__
#define __COMARVALUE__

#ifndef size_t
#include <sys/types.h>
#endif

#ifndef __XML_TREE_H__
#include <libxml2/libxml/tree.h>
#endif
/* COMARValue
   Main type for COMARValue family..
*/

enum {
	CVTYPE_NUMERIC = 0,
	CVTYPE_STRING,
	CVTYPE_ARRAY,
	CVTYPE_OBJECT
};

typedef struct _COMARValue COMARValue;

struct _COMARValue {
size_t			type;
void			*data;
};

typedef COMARValue *CVPTR;

typedef struct _COMARString COMARString;
struct  _COMARString {
char			*encoding;
size_t			len;
char			*string;
};

typedef struct _COMARArrayItem COMARArrayItem;
struct	_COMARArrayItem {
char			*key;
unsigned int	instance;
CVPTR			value;
COMARArrayItem	*next;
};

typedef COMARArrayItem	*CVARRPTR;

/* Warning: COMARObject always opaque data.. */
typedef struct _COMARObject COMARObject;
struct _COMARObject {
void			*data;
size_t			size;
};

CVPTR			CV_createCOMARStr(const char *str, size_t size);
CVPTR 			CV_createString(const char *langid, const char *encoding, const char *str, size_t size);
CVPTR			CV_createNumber_int(int number);
CVPTR			CV_createNumber_fp(float number);
CVPTR			CV_createNumber_dbl(double number);
CVPTR			CV_createObject(void *objData, size_t size);
CVPTR			CV_createArray(void);
CVARRPTR		CV_ArrayItem(char *key, unsigned int instance, CVPTR value);
int				CV_AddItem(CVPTR array, CVARRPTR value);
int				CV_DelItem(CVPTR array, char *key, unsigned int instance);
CVPTR			CV_GetItem(CVPTR array, char *key, unsigned int instance);

int				CVDestroy(CVPTR value);
char			*CV_toXmlStr(CVPTR value);
CVPTR			CV_fromXml(xmlNodePtr xml);
CVPTR			CV_fromXmlStr(xmlNodePtr xml, xmlDocPtr doc, const char *xmlCVString);

#endif	/* __COMARVALUE__ */

