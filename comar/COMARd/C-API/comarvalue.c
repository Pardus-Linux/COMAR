#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include "comarvalue.h"

static	void *(*_xmalloc)(size_t bufsize);
static	void *(*_xrealloc)(void *old, size_t bufsize);
static	void (*_xfree)(void *old);
static	char *glo_encoding	= "utf-8";
static	char *glo_lang		= "en_EN";

void	initCV(	void *(*mallocFunc)(size_t bufsize),
				void *(*reallocFunc)(void *old, size_t bufsize),
				void (*freeFunc)(void *old),
				char *encoding,
				char *lang) {
		if (encoding)
			glo_encoding = encoding;
		if (lang)
			glo_lang = lang;

		if (mallocFunc)
			_xmalloc = mallocFunc;
		else
			_xmalloc = malloc;

		if (reallocFunc)
			_xrealloc = reallocFunc;
		else
			_xrealloc = realloc;

		if (freeFunc)
				_xfree = freeFunc;
		else
			_xfree = free;
}

/* CV_CreateString
	Create a new COMARValue with string type.
	COMAR Always use utf-8 and (EN) language combination.
	Please pass langid = NULL, encoding = NULL
*/

CVPTR CV_createString(const char *langid, const char *encoding, const char *str, size_t size) {
	char *enc = NULL;
	CVPTR	CV;
	COMARString *CS;

	if (!langid) {
		langid = glo_lang;
	}
	if (!encoding) {
		encoding = glo_encoding;
	}
	CS = _xmalloc(sizeof(COMARString));
	CS->encoding = _xmalloc(strlen(langid) + strlen(encoding) + 2);
	strcpy(CS->encoding, langid);
	strcat(CS->encoding, ":");
	strcat(CS->encoding, encoding);
	if (size == 0) {
		size = strlen(str);
	}
	CS->string = _xmalloc(size + 1);
	memcpy(CS->string, str, size);
	CS->len = size;
	CV = _xmalloc(sizeof(struct _COMARValue));
	CV->type = CVTYPE_STRING;
	CV->data = CS;
	printf("String created: %s (%s)\n", CS->string, CS->encoding);
	return CV;
}

CVPTR CV_createNumber_int(int number) {
	CVPTR CV;
	char *str = _xmalloc(128);
	CV = _xmalloc(sizeof(COMARValue));
	snprintf(str, 127, "%d", number);
	CV->type = CVTYPE_NUMERIC;
	CV->data = str;
	return CV;
}

CVPTR CV_createNumber_fp(float number)
{
	CVPTR CV;
	char *str = _xmalloc(128);
	CV = _xmalloc(sizeof(COMARValue));
	snprintf(str, 127, "%f", number);
	CV->type = CVTYPE_NUMERIC;
	CV->data = str;
	return CV;
}
CVPTR CV_createNumber_dbl(double number)
{
	CVPTR CV;
	char *str = _xmalloc(128);
	CV = _xmalloc(sizeof(COMARValue));
	snprintf(str, 127, "%f", number);
	CV->type = CVTYPE_NUMERIC;
	CV->data = str;
	return CV;
}
CVPTR CV_createObject(void *objData, size_t size)
{
	CVPTR CV;
	CV = _xmalloc(sizeof(COMARValue));
	CV->type = CVTYPE_OBJECT;
	CV->data = _xmalloc(size);
	memcpy(CV->data, objData, size);
	return CV;
}
CVPTR CV_createArray(void) {
	CVPTR CV;
	CV = _xmalloc(sizeof(COMARValue));
	CV->type = CVTYPE_ARRAY;
	CV->data = NULL;
	return CV;
}

CVARRPTR CV_arrayItem(char *key, unsigned int instance, CVPTR value) {
	CVARRPTR CA;
	char *keystr = _xmalloc(strlen(key) + 1);
	CA = _xmalloc(sizeof(COMARArrayItem));
	CA->instance = 0;
	CA->next = NULL;
	CA->value = value;
	strcpy(CA->key, key);
	return CA;
}

int CV_addItem(CVPTR array, CVARRPTR item) {
	CVARRPTR first;
	if (array->type != CVTYPE_ARRAY) {
		return EINVAL;
	}
	first = (CVARRPTR)array->data;
	if (first == NULL) {
		array->data = item;
		return 0;
	}
	while (first) {
		if (first->next == NULL) {
			first->next = item;
			return 0;
		}
		first = first->next;
	}
	return 0;
}

int CVDestroy(CVPTR value) {
	COMARString *cs;
	COMARArrayItem *ai;
	COMARObject *co;
	switch (value->type) {
		case CVTYPE_NUMERIC:
			_xfree(value->data);
			_xfree(value);
			break;
		case CVTYPE_STRING:
			cs = (COMARString *)value->data;
			_xfree(cs->encoding);
			_xfree(cs->string);
			_xfree(value->data);
			_xfree(value);
			break;
		case CVTYPE_OBJECT:
			co = (COMARObject *)value->data;
			_xfree(co->data);
			_xfree(value->data);
			_xfree(value);
			break;
		case CVTYPE_ARRAY:
			ai = value->data;
			while (ai) {
				CVDestroy(ai->value);
				_xfree(ai->key);
				ai = ai->next;
				_xfree(ai);
			}
			break;
	}
	return 0;
}

int CV_delItem(CVPTR array, char *key, unsigned int instance) {
	CVARRPTR first;
	if (array->type != CVTYPE_ARRAY) {
		return EINVAL;
	}
	first = (CVARRPTR) array->data;
	if (first == NULL) {
		return ENOENT;
	}
	while (first) {
		/* We dont use instance value currently.. */
		if (strcmp(first->key, key) == 0) {
			CVDestroy(first->value);
			_xfree(first->key);
			_xfree(first);
			return 0;
		}
		first = first->next;
	}
	return ENOENT;
}

CVPTR CV_getItem(CVPTR array, char *key, unsigned int instance) {
	CVARRPTR first;
	if (array->type != CVTYPE_ARRAY) {
		errno = EINVAL;
		return NULL;
	}
	first = (CVARRPTR) array->data;
	if (first == NULL) {
		errno = EBADF;
		return NULL;
	}
	while (first) {
		/* We dont use instance value currently.. */
		if (strcmp(first->key, key) == 0) {
			return first->value;
		}
		first = first->next;
	}
	errno = ENOENT;
	return NULL;
}

char *CV_toXmlStr(CVPTR value) {
	COMARString *cs;
	COMARArrayItem *ai;
	COMARObject *co;
	char *buf, *tmp, *m;
	size_t bsize;
	switch (value->type) {
		case CVTYPE_NUMERIC:
			bsize = strlen(value->data) + 128;
			buf = _xmalloc(bsize);
			snprintf(buf, bsize, "<numeric>%s</numeric>", value->data);
			return buf;
		case CVTYPE_STRING:
			cs = (COMARString *)value->data;
			bsize = cs->len + 128;
			buf = _xmalloc(bsize);
			snprintf(buf, bsize, "<string encoding=\"%s\">%s</string>", cs->encoding, cs->string);
			return buf;
		case CVTYPE_OBJECT:
			co = (COMARObject *)value->data;
			_xfree(co->data);
			_xfree(value->data);
			_xfree(value);
			break;
		case CVTYPE_ARRAY:
			ai = value->data;
			if (!ai) {
				buf = _xmalloc(12);
				snprintf(buf, 12, "<array/>");
				return buf;
			}
			m = _xmalloc(24);
			strcpy(m, "<array>");
			while (ai) {
				tmp = CV_toXmlStr(ai->value);
				bsize =  512 + strlen(tmp) + strlen(m);
				buf = _xmalloc(512 + bsize);
				snprintf(buf, bsize + 512, "<item key='%s' instance='%d'>%s</item>", ai->key, ai->instance, tmp);
				_xfree(tmp);
				m = _xrealloc(m, strlen(m) + strlen(buf) + 15);
				strcat(m, buf);
				ai = ai->next;
			}
			strcat(m, "</array>");
			break;
	}
	return 0;
}

CVPTR CV_fromXmlStr(xmlNodePtr xml, xmlDocPtr doc, const char *xmlCVString) {

    xmlInitMemory();
    xmlInitParser();
    xmlLineNumbersDefault(1);
    //printf("Parser entry..numbers\n");
    xmlKeepBlanksDefault(0);
    //printf("Parser entry..\n");
    //conf = xmlParseFile(file);
	doc = xmlParseFile(file);
}

int main(int argc, char **argv) {
	CVPTR cv;
	initCV(NULL, NULL, NULL, NULL, NULL);
	cv = CV_createString(NULL, NULL, "serdar", 6);
	printf("XML: %s \n", CV_toXmlStr(cv));
	return 0;
}
