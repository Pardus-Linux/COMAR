#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2004, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

# CORE_EVENT.py
# COMAR Event Subsystem.


import os, sys, time
import comar_global

class eventSubsystem:
	def __init__(self, dbHelper = None, CV = None, OMMGR=None):
		self.db_event = dbHelper.dbOpen(comar_global.comar_basic_data + "eventhnd.db")
		self.dbHelper = dbHelper
		self.CV = CV
		self.objHandlers = { "EVENTOBJ":self.eventSys_objHandler }
		self.methodVtbl	 = {	"eventSys.create":				self.eventSys_create,
								"eventSys.addTask":				self.eventSys_addTask,
								"eventSys.delTask":				self.eventSys_delTask,
								"eventSys.fireUp":				self.eventSys_fireUp,
								"eventSys.new":					self.eventSys_new,
								"eventSys.get":					self.eventSys_get,
								"eventSys.std.TimerMinutely":	self.eventSys_stdTimerMinutely,
								"eventSys.std.Timer30Minutely":	self.eventSys_stdTimer30Minutely,
								"eventSys.std.TimerHourly":		self.eventSys_stdTimerHourly,
								"eventSys.std.TimerWorkStart":	self.eventSys_stdTimerWorkStart,
								"eventSys.std.TimerWorkFinish":	self.eventSys_stdTimerWorkFinish,
								"eventSys.std.TimerDaily":		self.eventSys_stdTimerDaily,
								"eventSys.std.TimerMorning":	self.eventSys_stdTimerMorning,
								"eventSys.std.TimerAt":			self.eventSys_stdTimerAt,
								"eventSys.std.BootUp":			self.eventSys_stdBootUp,
								"eventSys.std.COMARdUp":		self.eventSys_stdCOMARdUp,
								"eventSys.std.BeforeShutdown":	self.eventSys_stdBeforeShutdown,
								"eventSys.std.Shutdown":		self.eventSys_stdShutdown,
								"eventSys.std.ProfileChange":	self.eventSys_stdProfileChange }
		self.propVtbl	= {}
		self.objDriver	= { "OM:CORE:EMBED:EVENT": (None, self.eventSys_objHandler) }
		self.eventTag = 0
	def eventSys_create(self, prms = {}, callerInfo = None):
		"""Bu çağrı, yeni bir eventid oluşturarak geriye döndürür.\n"""
		self.eventTag += 1
		return self.CV.string_create("USER:LOCAL:%s-%s-%s" % (os.getpid(), time.time(), self.eventTag))
	def eventSys_addTask(self, prms = {}, callerInfo = None):
		"""
eventSys.addTask(eventid = "eventid", object=ÇağrılacakNesne, method=ÇağrılacakMethod [, wait='N'])
eventSys.addTask(eventid = "eventid", omnode="NS:node.method" [, wait='N'])
eventSys.addTask(eventid = "eventid" [, wait='N'])
		Bu çağrı başarılı olması durumunda, eventSys.delTask() çağrısı ile kullanılmak üzere bir "taskKey" değeri döndürür. Bu değer, 255 karakterden kısa, 8Bit-ASCII uyumlu bir COMARString'dir."""
		ret = self.CV.COMARValue("null")
		wait = self.CV.getPrmVal(prms, "wait", ("string", "N"))
		wait = self.CV.string_boolval(wait)
		eventid = self.CV.getPrmVal(prms, "eventid", None)

		if eventid == None:
			return ret
		if prms.has_key("object"):
			# Register object
			obj = self.CV.getPrmVal(prms, "object", None)
			method = self.CV.getPrmVal(prms, "method", None)
			if obj == None or method == None:
				return ret
			#ERSU_AOBJ	: addNewEventObject. ANY->TAMEV: DATA = EVENTID=eventid\x00OBJECT=objDescriptor\x00METHOD=methodName\x00WAIT=0\x00
			data = "EVENTID:%s\x00OBJECT=%s\x00METHOD=%s\x00WAIT=%s\x00" % (eventid, obj, method, wait)
			tk = self.dbHelper.sendRootCmd(cmd="ERSU_AOBJ", tid=0, pkData=data)
			if tk != None and tk[3] != None:
				return self.CV.string_create(tk[3])
			return ret
		elif prms.has_key("omnode"):
			# Register omnode.
			omnode = ret
			if omnode == None:
				return 			
			#ERSU_AOM : addNewEventOMNode. ANY->TAMEV: DATA = EVENTID=eventid\x00NODE=OMNode\x00WAIT=0\x00
			data = "EVENTID:%s\x00OMNODE=%s\x00WAIT=%s\x00" % (eventid, omnode, wait)
			tk = self.dbHelper.sendRootCmd(cmd="ERSU_AOM", tid=0, pkData=data)
			if tk != None and tk[3] != None:
				return self.CV.string_create(tk[3])
			return ret
		else:
			# Register Self.
			# first extract obj info from callerInfo
			pass		

	def eventSys_delTask(self, prms = {}, callerInfo = None):
		taskKey = self.CV.getPrmVal(prms, "taskKey", None)
		if taskKey == None:
			ret = self.CV.COMARValue("null")
		# ERSU_DTK: deleteEventTask. ANY->TAMEV: DATA = taskKey
		tk = self.dbHelper.sendRootCmd(cmd="ERSU_DTK", tid=0, pkData=taskKey, loop = 0)
		return self.CV.COMARValue("null")
	def eventSys_fireUp(self, prms = {}, callerInfo = None):
		evid = self.CV.getPrmVal(prms, "eventid", None)
		if eventid == None:
			ret = self.CV.COMARValue("null")
		# ERSU_FUP	: FireEvent. ANY->TAMEV: DATA = eventid.
		tk = self.dbHelper.sendRootCmd(cmd="ERSU_FUP", tid=0, pkData=evid, loop = 0)
		return self.CV.COMARValue("null")
	def eventSys_new(self, prms = {}, callerInfo = None):
		"""Bir event nesnesi 'eventObj' oluşturup geri döndürür. Bu nesne şu yordamlara sahiptir:
	eventSys.get(eventid)
	Belirtilen eventid için 'eventObj' oluşturup geri döndürür. Eğer bu eventid daha önceden kullanılmamışsa, geriye herhangi bir değer döndürmez.
	'eventObj' nesnesi şu yordamlara sahiptir:
	Property eventObj.eventid (read-only)	: COMARString.
	Property eventObj.keys (read-only)		: COMARArray. Bu event'a dahil olan görevlere ait keyleri ihtiva eder. Sadece çağıran nesne tarafından eklenen görevler bu listede bulunur.
	Method eventObj.del(taskKey = key)
	Method eventObj.addNode(omnode="NS:node.method" [, wait='N'])
	Method eventObj.addObject(object=objValue, method=methodName[, wait='N'])
	Method eventObj.addCurrent([wait='N'])
	Method eventObj.fireUp()\n"""
		pass
	def eventSys_get(self, prms = {}, callerInfo = None):
		pass
	def eventSys_objHandler(self, objClass = "", objid = "", callType = "", callName = "", prms = {}, callerInfo = None):
		# This is a private method.
		pass
	def eventSys_stdTimerMinutely(self, prms = {}, callerInfo = None):
		"""Her dakika başında tetiklenen bir event için eventid değerini döndürür."""
		return self.CV.string_create("STD-EVENT:TIMER:MINUTE")

	def eventSys_stdTimer30Minutely(self, prms = {}, callerInfo = None):
		"""Her saat xx:00 ve xx:30 dakikalarında tetiklenen bir event için eventid değerini döndürür."""
		return self.CV.string_create("STD-EVENT:TIMER:HALFHOUR")

	def eventSys_stdTimerHourly(self, prms = {}, callerInfo = None):
		"""Her saat başında tetiklenen bir eventid döndürür."""
		return self.CV.string_create("STD-EVENT:TIMER:HOUR")

	def eventSys_stdTimerWorkStart(self, prms = {}, callerInfo = None):
		"""Mesai saatinin başlangıcında tetiklenen bir eventid döndürür."""
		return self.CV.string_create("STD-EVENT:TIMER:WSTART")

	def eventSys_stdTimerWorkFinish(self, prms = {}, callerInfo = None):
		"""Mesai saatinin bbitiminde tetiklenen bir eventid döndürür."""
		return self.CV.string_create("STD-EVENT:TIMER:WEND")

	def eventSys_stdTimerDaily(self, prms = {}, callerInfo = None):
		"""Her gün saat 00:00'da tetiklenen bir eventid döndürür."""
		return self.CV.string_create("STD-EVENT:TIMER:DAILY")

	def eventSys_stdTimerMorning(self, prms = {}, callerInfo = None):
		"""Her sabah "MorningTime" da tetiklenen bir eventid döndürür. "Morning Time", COMARd içinde ayarlanabilen bir değerdir."""
		return self.CV.string_create("STD-EVENT:TIMER:MORNING")

	def eventSys_stdTimerAt(self, prms = {}, callerInfo = None):
		"""Belirtilen saat ve günde tetiklenen bir eventid döndürür. Her gün için, 0000-00-00 tarihi kullanılabilir."""
		tim = self.CV.getPrmVal(prms, "time", None)
		if tim == None:
			ret = self.CV.COMARValue("null")
		# ERSU_DTK: deleteEventTask. ANY->TAMEV: DATA = taskKey
		return self.CV.string_create("STD-EVENT:TIMER:AT:%s", time)
	def eventSys_stdBootUp(self, prms = {}, callerInfo = None):
		"""Sistem bootup esnasında tetiklenen bir event oluşturur. Bu sadece %100 COMAR Compatible sistemler için mevcuttur."""
		return self.CV.string_create("STD-EVENT:SYSINIT:BOOTUP")

	def eventSys_stdCOMARdUp(self, prms = {}, callerInfo = None):
		"""COMARd başlar başlamaz tetiklenen bir eventid oluşturur."""
		return self.CV.string_create("STD-EVENT:SYSINIT:COMARUP")

	def eventSys_stdBeforeShutdown(self, prms = {}, callerInfo = None):
		"""Sistem kapatılmaya başlandığında tetiklenen bir event oluşturur. Bu sadece %100 COMAR Compatible sistemler için mevcuttur."""
		return self.CV.string_create("STD-EVENT:SYSINIT:PREHALT")

	def eventSys_stdShutdown(self, prms = {}, callerInfo = None):
		"""Sistem kapatılmaya başlanıp, stdBeforeShutdown() eventindeki görevler sona erince tetiklenen bir eventid oluşturur."""
		return self.CV.string_create("STD-EVENT:SYSINIT:HALT")

	def eventSys_stdProfileChange(self, prms = {}, callerInfo = None):
		"""Sistemde tarif edilmiş bulunan bir profil değiştiğinde tetiklenen bir eventid oluşturur."""
		return self.CV.string_create("STD-EVENT:PROFILE:CHANGE:%s" % (profile))
